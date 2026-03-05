<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { ElMessageBox } from 'element-plus'

import { useChatStore } from '@/stores/chat'
import ConversationItem from './ConversationItem.vue'

const chatStore = useChatStore()
const { conversations, activeConversationId } = storeToRefs(chatStore)

async function createConversation() {
  chatStore.enterDraftMode()
}

function selectConversation(id: string) {
  chatStore.setActiveConversation(id)
}

async function removeConversation(id: string) {
  try {
    await ElMessageBox.confirm(
      'Deleting this thread will remove local history and archive it on backend. Continue?',
      'Delete Conversation',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        customClass: 'dark-message-box',
        confirmButtonClass: 'danger-confirm-btn',
        cancelButtonClass: 'dark-cancel-btn',
        type: 'warning'
      }
    )
    await chatStore.deleteConversationAction(id)
  } catch {
    // canceled
  }
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
        @remove="removeConversation"
      />
    </div>
  </aside>
</template>
