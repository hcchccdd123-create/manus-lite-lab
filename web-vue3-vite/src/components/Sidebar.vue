<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useChatStore } from '@/stores/chat'
import ConversationItem from './ConversationItem.vue'

const chatStore = useChatStore()
const { conversations, activeConversationId } = storeToRefs(chatStore)

async function createConversation() {
  await chatStore.createConversationAction()
}

function selectConversation(id: string) {
  chatStore.setActiveConversation(id)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <h1>Manus Lite</h1>
      <p>Threaded chat</p>
    </div>

    <div class="thread-header">
      <h2>Threads</h2>
      <button class="new-chat-btn" @click="createConversation">+ New</button>
    </div>

    <div class="conversation-list">
      <ConversationItem
        v-for="item in conversations"
        :key="item.id"
        :conversation="item"
        :active="item.id === activeConversationId"
        @select="selectConversation"
      />
    </div>

    <button class="settings-btn" type="button">Settings</button>
  </aside>
</template>
