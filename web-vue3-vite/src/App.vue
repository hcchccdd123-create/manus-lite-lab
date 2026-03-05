<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'

import Sidebar from '@/components/Sidebar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const { activeConversationId } = storeToRefs(chatStore)

onMounted(async () => {
  await chatStore.hydrateFromIndexedDb()

  try {
    await chatStore.syncConversationsFromServer()
  } catch (error) {
    console.warn('Failed to sync conversations from backend', error)
  }
})

watch(
  () => activeConversationId.value,
  async (id) => {
    if (!id) return
    if (chatStore.pendingConversations[id]) return
    const existing = chatStore.messagesByConversation[id]
    if (existing && existing.length > 0) return
    try {
      await chatStore.loadMessages(id)
    } catch (error) {
      console.warn(`Failed to load messages for ${id}`, error)
    }
  },
  { immediate: false }
)
</script>

<template>
  <div class="app-shell">
    <Sidebar />
    <ChatPanel />
  </div>
</template>
