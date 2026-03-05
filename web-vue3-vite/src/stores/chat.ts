import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { createConversation, deleteConversation, getMessages, listConversations } from '@/api/conversations'
import {
  deleteConversationData,
  loadAllMessages,
  loadConversations,
  loadThinkStates,
  saveConversation,
  saveConversations,
  saveMessage,
  saveMessages,
  saveThinkState
} from '@/persistence/indexeddb'
import type { Conversation, Message, PendingConversationMeta, ThinkState, UiMode } from '@/types/chat'

function nowIso(): string {
  return new Date().toISOString()
}

function lastNonDraftMessage(messages: Message[]): Message | null {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (!messages[i].isStreamingDraft) return messages[i]
  }
  return null
}

function draftAssistantMessage(conversationId: string): Message {
  return {
    id: `draft-${conversationId}`,
    conversation_id: conversationId,
    role: 'assistant',
    content: '',
    sequence_no: Number.MAX_SAFE_INTEGER,
    provider: null,
    model: null,
    created_at: nowIso(),
    isStreamingDraft: true
  }
}

function buildConversationTitleFromFirstPrompt(text: string): string {
  const compact = text.trim().replace(/\s+/g, ' ')
  if (!compact) return 'New chat'
  return compact.slice(0, 20)
}

export const useChatStore = defineStore('chat', () => {
  const uiMode = ref<UiMode>('draft')
  const conversations = ref<Conversation[]>([])
  const activeConversationId = ref<string | null>(null)
  const pendingConversations = ref<Record<string, PendingConversationMeta>>({})
  const messagesByConversation = ref<Record<string, Message[]>>({})
  const thinkStatesByConversation = ref<Record<string, ThinkState>>({})

  const activeConversation = computed(() =>
    conversations.value.find((item) => item.id === activeConversationId.value) || null
  )

  const activeMessages = computed(() => {
    if (!activeConversationId.value) return []
    return messagesByConversation.value[activeConversationId.value] || []
  })

  const activeThinkState = computed(() => {
    if (!activeConversationId.value) return null
    return thinkStatesByConversation.value[activeConversationId.value] || null
  })

  function enterDraftMode(): void {
    activeConversationId.value = null
    uiMode.value = 'draft'
  }

  function setActiveConversation(id: string | null): void {
    activeConversationId.value = id
    uiMode.value = id ? 'conversation' : 'draft'
  }

  function upsertConversation(conversation: Conversation): void {
    const idx = conversations.value.findIndex((item) => item.id === conversation.id)
    if (idx >= 0) {
      conversations.value[idx] = { ...conversations.value[idx], ...conversation }
    } else {
      conversations.value.unshift(conversation)
    }
    conversations.value.sort((a, b) => (a.last_active_at < b.last_active_at ? 1 : -1))
    void saveConversation(conversations.value.find((item) => item.id === conversation.id) as Conversation)
  }

  function revealPendingConversation(conversationId: string): void {
    const pending = pendingConversations.value[conversationId]
    if (!pending) return

    const visible: Conversation = {
      id: pending.id,
      title: pending.title,
      status: 'active',
      provider: pending.provider,
      model: pending.model,
      system_prompt: null,
      memory_mode: 'window_summary',
      memory_window_size: 12,
      summary_message_count: 0,
      created_at: pending.created_at,
      updated_at: pending.updated_at,
      last_active_at: pending.last_active_at,
      isStreaming: true
    }

    delete pendingConversations.value[conversationId]
    upsertConversation(visible)
  }

  function dropPendingConversation(conversationId: string): void {
    if (!pendingConversations.value[conversationId]) return
    delete pendingConversations.value[conversationId]
    delete messagesByConversation.value[conversationId]
    delete thinkStatesByConversation.value[conversationId]
    void deleteConversationData(conversationId)
    if (activeConversationId.value === conversationId) {
      enterDraftMode()
    }
  }

  function setConversationStreaming(conversationId: string, isStreaming: boolean, requestId?: string): void {
    const conv = conversations.value.find((item) => item.id === conversationId)
    if (!conv) return
    conv.isStreaming = isStreaming
    conv.streamRequestId = requestId
    conv.updated_at = nowIso()
    conv.last_active_at = nowIso()
    void saveConversation(conv)
  }

  function setThinkState(conversationId: string, patch: Partial<ThinkState>): void {
    const existing =
      thinkStatesByConversation.value[conversationId] ||
      ({
        conversationId,
        isThinking: false,
        isCollapsed: true,
        rawText: '',
        updatedAt: nowIso()
      } as ThinkState)

    const next = {
      ...existing,
      ...patch,
      updatedAt: nowIso()
    }
    thinkStatesByConversation.value[conversationId] = next
    void saveThinkState(next)
  }

  function ensureMessages(conversationId: string): void {
    if (!messagesByConversation.value[conversationId]) {
      messagesByConversation.value[conversationId] = []
    }
  }

  function appendUserMessage(conversationId: string, text: string): void {
    ensureMessages(conversationId)
    const list = messagesByConversation.value[conversationId]
    const nextSeq = (lastNonDraftMessage(list)?.sequence_no || 0) + 1
    const message: Message = {
      id: `local-user-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content: text,
      sequence_no: nextSeq,
      provider: null,
      model: null,
      created_at: nowIso()
    }
    list.push(message)
    void saveMessage(message)
  }

  function beginAssistantDraft(conversationId: string): void {
    ensureMessages(conversationId)
    const list = messagesByConversation.value[conversationId]
    if (list.some((item) => item.isStreamingDraft)) return
    list.push(draftAssistantMessage(conversationId))
  }

  function appendAssistantChunk(conversationId: string, chunk: string): void {
    ensureMessages(conversationId)
    const list = messagesByConversation.value[conversationId]
    const draft = list.find((item) => item.isStreamingDraft)
    if (!draft) {
      beginAssistantDraft(conversationId)
      appendAssistantChunk(conversationId, chunk)
      return
    }
    draft.content += chunk
  }

  function finalizeAssistantMessage(conversationId: string, text: string): void {
    ensureMessages(conversationId)
    const list = messagesByConversation.value[conversationId]
    const draftIndex = list.findIndex((item) => item.isStreamingDraft)
    const nextSeq = (lastNonDraftMessage(list)?.sequence_no || 0) + 1

    const finalMessage: Message = {
      id: `local-assistant-${Date.now()}`,
      conversation_id: conversationId,
      role: 'assistant',
      content: text,
      sequence_no: nextSeq,
      provider: null,
      model: null,
      created_at: nowIso()
    }

    if (draftIndex >= 0) {
      list.splice(draftIndex, 1, finalMessage)
    } else {
      list.push(finalMessage)
    }

    void saveMessage(finalMessage)
  }

  async function hydrateFromIndexedDb(): Promise<void> {
    const [conversationRows, messageRows, thinkRows] = await Promise.all([
      loadConversations(),
      loadAllMessages(),
      loadThinkStates()
    ])

    conversations.value = conversationRows.map((item) => ({ ...item, isStreaming: false }))

    const grouped: Record<string, Message[]> = {}
    for (const msg of messageRows) {
      if (!grouped[msg.conversation_id]) grouped[msg.conversation_id] = []
      grouped[msg.conversation_id].push(msg)
    }

    Object.keys(grouped).forEach((key) => {
      grouped[key].sort((a, b) => a.sequence_no - b.sequence_no)
    })

    messagesByConversation.value = grouped

    const thinkMap: Record<string, ThinkState> = {}
    for (const item of thinkRows) {
      thinkMap[item.conversationId] = item
    }
    thinkStatesByConversation.value = thinkMap

    enterDraftMode()
  }

  async function syncConversationsFromServer(): Promise<void> {
    const response = await listConversations()
    const serverRows = response.data || []
    conversations.value = serverRows.map((item) => ({ ...item, isStreaming: false }))
    await saveConversations(conversations.value)
    enterDraftMode()
  }

  async function createPendingConversationAction(firstPrompt: string): Promise<string> {
    const title = buildConversationTitleFromFirstPrompt(firstPrompt)
    const response = await createConversation({
      title,
      provider: 'glm',
      model: 'glm-4.7'
    })

    const created = response.data
    const pending: PendingConversationMeta = {
      id: created.id,
      title,
      provider: created.provider,
      model: created.model,
      created_at: created.created_at,
      updated_at: created.updated_at,
      last_active_at: created.last_active_at
    }

    pendingConversations.value[created.id] = pending
    ensureMessages(created.id)
    activeConversationId.value = created.id
    uiMode.value = 'conversation'
    return created.id
  }

  async function loadMessages(conversationId: string): Promise<void> {
    ensureMessages(conversationId)
    const response = await getMessages(conversationId)
    const serverMessages = response.data || []
    const localMessages = messagesByConversation.value[conversationId] || []

    if (localMessages.length === 0) {
      messagesByConversation.value[conversationId] = serverMessages
      await saveMessages(serverMessages)
      return
    }

    const mergedBySequence = new Map<number, Message>()
    for (const item of serverMessages) {
      mergedBySequence.set(item.sequence_no, item)
    }
    for (const item of localMessages) {
      if (item.isStreamingDraft) continue
      if (!mergedBySequence.has(item.sequence_no)) {
        mergedBySequence.set(item.sequence_no, item)
      }
    }

    const merged = Array.from(mergedBySequence.values()).sort((a, b) => a.sequence_no - b.sequence_no)
    const localDraft = localMessages.find((item) => item.isStreamingDraft)
    if (localDraft) {
      merged.push(localDraft)
    }

    messagesByConversation.value[conversationId] = merged
    await saveMessages(merged)
  }

  async function deleteConversationAction(conversationId: string): Promise<void> {
    await deleteConversation(conversationId)

    conversations.value = conversations.value.filter((item) => item.id !== conversationId)
    delete messagesByConversation.value[conversationId]
    delete thinkStatesByConversation.value[conversationId]
    delete pendingConversations.value[conversationId]

    if (activeConversationId.value === conversationId) {
      enterDraftMode()
    }

    await deleteConversationData(conversationId)
  }

  return {
    uiMode,
    conversations,
    activeConversationId,
    pendingConversations,
    messagesByConversation,
    thinkStatesByConversation,
    activeConversation,
    activeMessages,
    activeThinkState,
    enterDraftMode,
    setActiveConversation,
    upsertConversation,
    revealPendingConversation,
    dropPendingConversation,
    setConversationStreaming,
    setThinkState,
    appendUserMessage,
    beginAssistantDraft,
    appendAssistantChunk,
    finalizeAssistantMessage,
    hydrateFromIndexedDb,
    syncConversationsFromServer,
    createPendingConversationAction,
    loadMessages,
    deleteConversationAction,
    buildConversationTitleFromFirstPrompt
  }
})
