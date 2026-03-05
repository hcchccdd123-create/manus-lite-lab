<script setup lang="ts">
import { useMarkdown } from '@/composables/useMarkdown'
import type { Message } from '@/types/chat'

const props = defineProps<{
  messages: Message[]
}>()

const { renderMarkdown } = useMarkdown()
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
      <div class="message-body markdown" v-html="renderMarkdown(message.content)" />
    </article>
  </div>
</template>
