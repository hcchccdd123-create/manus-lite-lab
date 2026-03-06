import { getBaseURL } from './client'

export interface StreamPayload {
  session_id: string
  message: string
  runtime_mode?: 'chat' | 'agent'
  provider?: 'ollama' | 'glm' | 'codex'
  model?: string
  enable_thinking?: boolean
  enable_web_search?: boolean
}

export async function openChatStream(payload: StreamPayload, signal?: AbortSignal) {
  const response = await fetch(`${getBaseURL()}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal
  })

  if (!response.ok || !response.body) {
    throw new Error(`Streaming request failed: ${response.status}`)
  }

  return response.body.getReader()
}
