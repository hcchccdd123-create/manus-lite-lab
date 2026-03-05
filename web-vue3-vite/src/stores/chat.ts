import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { createConversation, getMessages, listConversations } from '@/api/conversations'
import {
  loadAllMessages,
  loadConversations,
  loadThinkStates,
  saveConversation,
  saveConversations,
  saveMessage,
  saveMessages,
  saveThinkState
} from '@/persistence/indexeddb'
import type { Conversation, Message, ThinkState } from '@/types/chat'

function nowIso(): string {
  return new Date().toISOString()
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

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const activeConversationId = ref<string | null>(null)
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

  function setActiveConversation(id: string): void {
    activeConversationId.value = id
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
    const nextSeq = (list[list.length - 1]?.sequence_no || 0) + 1
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
    const nextSeq = (list.filter((item) => !item.isStreamingDraft).at(-1)?.sequence_no || 0) + 1

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

    if (conversations.value.length > 0 && !activeConversationId.value) {
      activeConversationId.value = conversations.value[0].id
    }
  }

  async function syncConversationsFromServer(): Promise<void> {
    const response = await listConversations()
    const serverRows = response.data || []
    conversations.value = serverRows.map((item) => ({ ...item, isStreaming: false }))
    if (!activeConversationId.value && conversations.value.length > 0) {
      activeConversationId.value = conversations.value[0].id
    }
    await saveConversations(conversations.value)
  }

  async function createConversationAction(): Promise<Conversation> {
    const response = await createConversation({
      title: 'New chat',
      provider: 'ollama',
      model: 'qwen3.5:0.8b'
    })
    const conversation = { ...response.data, isStreaming: false } as Conversation
    upsertConversation(conversation)
    ensureMessages(conversation.id)
    activeConversationId.value = conversation.id
    return conversation
  }

  async function loadMessages(conversationId: string): Promise<void> {
    ensureMessages(conversationId)
    const response = await getMessages(conversationId)
    messagesByConversation.value[conversationId] = response.data || []
    await saveMessages(messagesByConversation.value[conversationId])
  }

  return {
    conversations,
    activeConversationId,
    messagesByConversation,
    thinkStatesByConversation,
    activeConversation,
    activeMessages,
    activeThinkState,
    setActiveConversation,
    upsertConversation,
    setConversationStreaming,
    setThinkState,
    appendUserMessage,
    beginAssistantDraft,
    appendAssistantChunk,
    finalizeAssistantMessage,
    hydrateFromIndexedDb,
    syncConversationsFromServer,
    createConversationAction,
    loadMessages
  }
})
