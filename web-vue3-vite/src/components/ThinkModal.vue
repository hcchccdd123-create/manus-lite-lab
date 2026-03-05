<script setup lang="ts">
import { useMarkdown } from '@/composables/useMarkdown'

defineProps<{
  open: boolean
  text: string
}>()

defineEmits<{
  close: []
}>()

const { renderMarkdown } = useMarkdown()
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="think-modal-mask" @click.self="$emit('close')">
      <div class="think-modal">
        <div class="think-modal-header">
          <h3>Thinking detail</h3>
          <button @click="$emit('close')">Close</button>
        </div>
        <div class="think-modal-content markdown" v-html="renderMarkdown(text)" />
      </div>
    </div>
  </teleport>
</template>
