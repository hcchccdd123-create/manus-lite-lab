export type ConversationStatus = 'active' | 'archived'
export type UiMode = 'draft' | 'conversation'

export interface Conversation {
  id: string
  title: string
  status: ConversationStatus
  provider: 'ollama' | 'glm' | 'codex'
  model: string
  system_prompt: string | null
  memory_mode: string
  memory_window_size: number
  summary_message_count: number
  created_at: string
  updated_at: string
  last_active_at: string
  isStreaming: boolean
  streamRequestId?: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  sequence_no: number
  provider: string | null
  model: string | null
  created_at: string
  isStreamingDraft?: boolean
}

export interface ThinkState {
  conversationId: string
  isThinking: boolean
  isCollapsed: boolean
  rawText: string
  updatedAt: string
}

export interface StreamSession {
  conversationId: string
  status: 'idle' | 'streaming' | 'error' | 'done'
  requestId?: string
  assistantBuffer: string
  thinkBuffer: string
  parserMode: 'normal' | 'think'
  tagBuffer: string
  hasReceivedFirstChunk: boolean
  terminationReason?: string
}

export interface PendingConversationMeta {
  id: string
  title: string
  provider: 'ollama' | 'glm' | 'codex'
  model: string
  created_at: string
  updated_at: string
  last_active_at: string
}
