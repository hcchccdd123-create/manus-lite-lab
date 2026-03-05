<script setup lang="ts">
import { computed } from 'vue'
import { useMarkdown } from '@/composables/useMarkdown'
import type { ThinkState } from '@/types/chat'

const props = defineProps<{
  thinkState: ThinkState | null
}>()

const emits = defineEmits<{
  toggle: []
  expand: []
}>()

const { renderMarkdown } = useMarkdown()

const hasContent = computed(() => Boolean(props.thinkState?.rawText))
</script>

<template>
  <section v-if="hasContent" class="think-panel">
    <header class="think-header">
      <div class="left">
        <span v-if="thinkState?.isThinking" class="spinner" />
        <span>Thinking</span>
      </div>
      <div class="actions">
        <button @click="emits('toggle')">{{ thinkState?.isCollapsed ? 'Expand' : 'Collapse' }}</button>
        <button @click="emits('expand')">Zoom</button>
      </div>
    </header>
    <div v-show="!thinkState?.isCollapsed" class="think-content markdown" v-html="renderMarkdown(thinkState?.rawText || '')" />
  </section>
</template>
