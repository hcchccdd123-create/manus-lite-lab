import { reactive } from 'vue'
import { defineStore } from 'pinia'

import { openChatStream } from '@/api/chat'
import { consumeSseStream, splitThinkDelta } from '@/composables/useSseStream'
import { useChatStore } from './chat'
import type { StreamSession } from '@/types/chat'

const controllers = new Map<string, AbortController>()

function splitFinalText(fullText: string): { normalText: string; thinkText: string } {
  const thinkMatches = [...fullText.matchAll(/<think>([\s\S]*?)<\/think>/g)]
  const thinkText = thinkMatches.map((item) => item[1]).join('\n').trim()
  const normalText = fullText.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
  return { normalText, thinkText }
}

function defaultSession(conversationId: string): StreamSession {
  return {
    conversationId,
    status: 'idle',
    assistantBuffer: '',
    thinkBuffer: '',
    parserMode: 'normal',
    tagBuffer: '',
    hasReceivedFirstChunk: false
  }
}

export const useStreamsStore = defineStore('streams', () => {
  const sessions = reactive<Record<string, StreamSession>>({})
  const errors = reactive<Record<string, string>>({})

  function getSession(conversationId: string): StreamSession {
    if (!sessions[conversationId]) {
      sessions[conversationId] = defaultSession(conversationId)
    }
    return sessions[conversationId]
  }

  function resetSession(conversationId: string): void {
    sessions[conversationId] = defaultSession(conversationId)
  }

  async function startStreaming(conversationId: string, message: string): Promise<void> {
    const chatStore = useChatStore()
    const session = getSession(conversationId)

    if (session.status === 'streaming') {
      throw new Error('This conversation is already streaming')
    }

    errors[conversationId] = ''
    session.status = 'streaming'
    session.assistantBuffer = ''
    session.thinkBuffer = ''
    session.parserMode = 'normal'
    session.tagBuffer = ''
    session.hasReceivedFirstChunk = false

    chatStore.appendUserMessage(conversationId, message)
    chatStore.beginAssistantDraft(conversationId)
    chatStore.setConversationStreaming(conversationId, true)
    chatStore.setThinkState(conversationId, {
      rawText: '',
      isThinking: true,
      isCollapsed: false
    })

    const controller = new AbortController()
    controllers.set(conversationId, controller)

    try {
      const reader = await openChatStream(
        {
          session_id: conversationId,
          message,
          enable_thinking: true
        },
        controller.signal
      )

      await consumeSseStream(reader, (event) => {
        if (event.event === 'message.start') {
          let requestId = ''
          try {
            requestId = JSON.parse(event.data).request_id || ''
          } catch {
            requestId = ''
          }
          chatStore.setConversationStreaming(conversationId, true, requestId)
          return
        }

        if (event.event === 'message.delta') {
          let delta = ''
          try {
            delta = JSON.parse(event.data).delta || ''
          } catch {
            delta = event.data || ''
          }

          if (!delta) return

          if (!session.hasReceivedFirstChunk) {
            session.hasReceivedFirstChunk = true
            chatStore.revealPendingConversation(conversationId)
            chatStore.setConversationStreaming(conversationId, true)
          }

          const split = splitThinkDelta(delta, session.parserMode, session.tagBuffer)
          session.parserMode = split.mode
          session.tagBuffer = split.tagBuffer

          if (split.thinkText) {
            session.thinkBuffer += split.thinkText
            chatStore.setThinkState(conversationId, {
              rawText: session.thinkBuffer,
              isThinking: true,
              isCollapsed: false
            })
          }

          if (split.normalText) {
            session.assistantBuffer += split.normalText
            chatStore.appendAssistantChunk(conversationId, split.normalText)
          }
          return
        }

        if (event.event === 'message.thinking') {
          let thinkingDelta = ''
          try {
            thinkingDelta = JSON.parse(event.data).delta || ''
          } catch {
            thinkingDelta = event.data || ''
          }
          if (!thinkingDelta) return
          if (!session.hasReceivedFirstChunk) {
            session.hasReceivedFirstChunk = true
            chatStore.revealPendingConversation(conversationId)
            chatStore.setConversationStreaming(conversationId, true)
          }
          session.thinkBuffer += thinkingDelta
          chatStore.setThinkState(conversationId, {
            rawText: session.thinkBuffer,
            isThinking: true,
            isCollapsed: false
          })
          return
        }

        if (event.event === 'message.end') {
          let finalText = session.assistantBuffer
          let finalThinking = session.thinkBuffer
          try {
            const payload = JSON.parse(event.data)
            finalText = payload.text || finalText
            finalThinking = payload.thinking || finalThinking
          } catch {
            finalText = session.assistantBuffer
          }

          const split = splitFinalText(finalText)
          chatStore.finalizeAssistantMessage(conversationId, split.normalText || session.assistantBuffer)
          chatStore.setConversationStreaming(conversationId, false)
          chatStore.setThinkState(conversationId, {
            rawText: finalThinking || split.thinkText || session.thinkBuffer,
            isThinking: false,
            isCollapsed: true
          })

          session.status = 'done'
          if (!session.hasReceivedFirstChunk) {
            chatStore.dropPendingConversation(conversationId)
          }
          return
        }

        if (event.event === 'error') {
          errors[conversationId] = event.data || 'Stream failed'
          session.status = 'error'
          chatStore.setConversationStreaming(conversationId, false)
          chatStore.setThinkState(conversationId, { isThinking: false, isCollapsed: true })
          if (!session.hasReceivedFirstChunk) {
            chatStore.dropPendingConversation(conversationId)
          }
        }
      })

      if (session.status === 'streaming') {
        session.status = 'done'
        chatStore.setConversationStreaming(conversationId, false)
        chatStore.setThinkState(conversationId, { isThinking: false, isCollapsed: true })
      }
    } catch (error) {
      session.status = 'error'
      errors[conversationId] = error instanceof Error ? error.message : 'Stream failed'
      chatStore.setConversationStreaming(conversationId, false)
      chatStore.setThinkState(conversationId, { isThinking: false, isCollapsed: true })
      if (!session.hasReceivedFirstChunk) {
        chatStore.dropPendingConversation(conversationId)
      }
    } finally {
      controllers.delete(conversationId)
    }
  }

  function abortStreaming(conversationId: string): void {
    const controller = controllers.get(conversationId)
    if (controller) {
      controller.abort()
      controllers.delete(conversationId)
    }
    const chatStore = useChatStore()
    chatStore.setConversationStreaming(conversationId, false)
    chatStore.setThinkState(conversationId, { isThinking: false, isCollapsed: true })
    const session = getSession(conversationId)
    session.status = 'done'
  }

  return {
    sessions,
    errors,
    getSession,
    resetSession,
    startStreaming,
    abortStreaming
  }
})
