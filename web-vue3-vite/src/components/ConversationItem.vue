<script setup lang="ts">
import type { Conversation } from '@/types/chat'

defineProps<{
  conversation: Conversation
  active: boolean
}>()

defineEmits<{
  select: [id: string]
}>()
</script>

<template>
  <button class="conversation-item" :class="{ active }" @click="$emit('select', conversation.id)">
    <span class="status-wrap">
      <span v-if="conversation.isStreaming" class="spinner" />
    </span>
    <span class="title">{{ conversation.title || 'Untitled' }}</span>
    <span class="time">{{ new Date(conversation.last_active_at).toLocaleTimeString() }}</span>
  </button>
</template>
