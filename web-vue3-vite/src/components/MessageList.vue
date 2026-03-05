<script setup lang="ts">
import { useMarkdown } from '@/composables/useMarkdown'
import type { Message } from '@/types/chat'

const props = defineProps<{
  messages: Message[]
}>()

const { renderMarkdown } = useMarkdown()

function isAssistantThinkingPlaceholder(message: Message): boolean {
  return Boolean(message.isStreamingDraft && message.role === 'assistant' && !message.content.trim())
}
</script>

<template>
  <div class="message-list">
    <article
      v-for="message in props.messages"
      :key="message.id"
      class="message-item"
      :class="[`role-${message.role}`, { draft: message.isStreamingDraft }]"
    >
      <header class="message-role">{{ message.role }}</header>
      <div v-if="isAssistantThinkingPlaceholder(message)" class="assistant-draft-placeholder">
        <span class="spinner assistant-draft-spinner" />
        <span>思考中...</span>
      </div>
      <div v-else class="message-body markdown" v-html="renderMarkdown(message.content)" />
    </article>
  </div>
</template>
