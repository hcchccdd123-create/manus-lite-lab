<script setup lang="ts">
import type { Conversation } from '@/types/chat'

const props = defineProps<{
  conversation: Conversation
  active: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
  remove: [id: string]
}>()

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    emit('select', props.conversation.id)
  }
}
</script>

<template>
  <div
    class="conversation-item"
    :class="{ active }"
    role="button"
    tabindex="0"
    @click="emit('select', conversation.id)"
    @keydown="onKeydown"
  >
    <span class="status-wrap">
      <span v-if="conversation.isStreaming" class="spinner" />
    </span>

    <div class="conversation-body">
      <div class="title-row">
        <span class="title">{{ conversation.title || 'Untitled' }}</span>
        <button
          class="delete-conversation-btn"
          type="button"
          title="Delete conversation"
          @click.stop="emit('remove', conversation.id)"
        >
          ×
        </button>
      </div>
      <span class="time">{{ new Date(conversation.last_active_at).toLocaleTimeString() }}</span>
    </div>
  </div>
</template>
