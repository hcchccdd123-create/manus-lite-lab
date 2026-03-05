import { openDB } from 'idb'
import type { Conversation, Message, ThinkState } from '@/types/chat'

const DB_NAME = 'manus-lite-web'
const DB_VERSION = 1

export const dbPromise = openDB(DB_NAME, DB_VERSION, {
  upgrade(db) {
    if (!db.objectStoreNames.contains('conversations')) {
      db.createObjectStore('conversations', { keyPath: 'id' })
    }
    if (!db.objectStoreNames.contains('messages')) {
      const messages = db.createObjectStore('messages', { keyPath: 'id' })
      messages.createIndex('by_conversation', 'conversation_id')
    }
    if (!db.objectStoreNames.contains('think_states')) {
      db.createObjectStore('think_states', { keyPath: 'conversationId' })
    }
  }
})

function toPlain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export async function saveConversation(conversation: Conversation): Promise<void> {
  const db = await dbPromise
  await db.put('conversations', toPlain(conversation))
}

export async function saveConversations(conversations: Conversation[]): Promise<void> {
  const db = await dbPromise
  const tx = db.transaction('conversations', 'readwrite')
  for (const item of conversations) {
    await tx.store.put(toPlain(item))
  }
  await tx.done
}

export async function loadConversations(): Promise<Conversation[]> {
  const db = await dbPromise
  return db.getAll('conversations') as Promise<Conversation[]>
}

export async function saveMessage(message: Message): Promise<void> {
  const db = await dbPromise
  await db.put('messages', toPlain(message))
}

export async function saveMessages(messages: Message[]): Promise<void> {
  const db = await dbPromise
  const tx = db.transaction('messages', 'readwrite')
  for (const item of messages) {
    await tx.store.put(toPlain(item))
  }
  await tx.done
}

export async function loadAllMessages(): Promise<Message[]> {
  const db = await dbPromise
  return db.getAll('messages') as Promise<Message[]>
}

export async function saveThinkState(thinkState: ThinkState): Promise<void> {
  const db = await dbPromise
  await db.put('think_states', toPlain(thinkState))
}

export async function loadThinkStates(): Promise<ThinkState[]> {
  const db = await dbPromise
  return db.getAll('think_states') as Promise<ThinkState[]>
}
