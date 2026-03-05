import { request } from './client'
import type { Conversation, Message } from '@/types/chat'

export function createConversation(payload: Partial<Conversation>) {
  return request<Conversation>('/api/v1/conversations', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function listConversations() {
  return request<Conversation[]>('/api/v1/conversations?status=active&limit=100&offset=0')
}

export function getMessages(conversationId: string) {
  return request<Message[]>(`/api/v1/conversations/${conversationId}/messages?limit=200`)
}

export function patchConversation(conversationId: string, payload: Record<string, unknown>) {
  return request<Conversation>(`/api/v1/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function deleteConversation(conversationId: string) {
  return request<Conversation>(`/api/v1/conversations/${conversationId}`, {
    method: 'DELETE'
  })
}
