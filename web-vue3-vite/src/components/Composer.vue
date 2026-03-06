<script setup lang="ts">
import { ref } from 'vue'

const modelValue = defineModel<string>({ required: true })
const props = defineProps<{
  disabled?: boolean
  deepThinkingEnabled?: boolean
  runtimeMode?: 'chat' | 'agent'
  webSearchEnabled?: boolean
}>()

const emits = defineEmits<{
  submit: []
  toggleDeepThinking: [enabled: boolean]
  toggleRuntimeMode: [mode: 'chat' | 'agent']
  toggleWebSearch: [enabled: boolean]
}>()

const textarea = ref<HTMLTextAreaElement | null>(null)

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emits('submit')
  }
}

function onToggleDeepThinking() {
  emits('toggleDeepThinking', !props.deepThinkingEnabled)
}

function onToggleRuntimeMode() {
  emits('toggleRuntimeMode', props.runtimeMode === 'agent' ? 'chat' : 'agent')
}

function onToggleWebSearch() {
  emits('toggleWebSearch', !props.webSearchEnabled)
}
</script>

<template>
  <div class="composer">
    <label class="composer-field">
      <textarea
        ref="textarea"
        v-model="modelValue"
        placeholder="Message Manus Lite..."
        rows="3"
        :disabled="props.disabled"
        @keydown="onKeydown"
      />
      <button
        type="button"
        class="runtime-mode-toggle"
        :class="{ active: props.runtimeMode === 'agent' }"
        :title="props.runtimeMode === 'agent' ? 'Runtime: Agent' : 'Runtime: Chat'"
        :disabled="props.disabled"
        @click="onToggleRuntimeMode"
      >
        {{ props.runtimeMode === 'agent' ? 'Agent' : 'Chat' }}
      </button>
      <button
        type="button"
        class="web-search-toggle"
        :class="{ active: props.webSearchEnabled }"
        :title="props.webSearchEnabled ? 'Web Search: On' : 'Web Search: Off'"
        :disabled="props.disabled"
        @click="onToggleWebSearch"
      >
        Web
      </button>
      <button
        type="button"
        class="deep-thinking-toggle"
        :class="{ active: props.deepThinkingEnabled }"
        :aria-pressed="props.deepThinkingEnabled ? 'true' : 'false'"
        :title="props.deepThinkingEnabled ? 'Deep Thinking: On' : 'Deep Thinking: Off'"
        :disabled="props.disabled"
        @click="onToggleDeepThinking"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path d="M10 3.4a5.6 5.6 0 0 0-3.9 9.6c.6.6 1 1.3 1.2 2H12.7c.2-.7.6-1.4 1.2-2A5.6 5.6 0 0 0 10 3.4Z" />
          <path d="M7.7 16.2h4.6" />
          <path d="M8.3 18h3.4" />
        </svg>
      </button>
      <button type="button" class="send-fab" :disabled="props.disabled || !modelValue.trim()" @click="$emit('submit')">
        <span aria-hidden="true">↑</span>
      </button>
    </label>
  </div>
</template>
