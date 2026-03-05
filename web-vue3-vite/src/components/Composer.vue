<script setup lang="ts">
import { ref } from 'vue'

const modelValue = defineModel<string>({ required: true })
defineProps<{
  disabled?: boolean
}>()

const emits = defineEmits<{
  submit: []
}>()

const textarea = ref<HTMLTextAreaElement | null>(null)

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emits('submit')
  }
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
        :disabled="disabled"
        @keydown="onKeydown"
      />
      <button class="send-fab" :disabled="disabled || !modelValue.trim()" @click="$emit('submit')">
        <span aria-hidden="true">↑</span>
      </button>
    </label>
  </div>
</template>
