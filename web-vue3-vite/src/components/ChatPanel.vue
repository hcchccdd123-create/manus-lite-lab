<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'

import Composer from './Composer.vue'
import MessageList from './MessageList.vue'
import ThinkModal from './ThinkModal.vue'
import ThinkPanel from './ThinkPanel.vue'
import { useChatStore } from '@/stores/chat'
import { useStreamsStore } from '@/stores/streams'
import { useAutoScroll } from '@/composables/useAutoScroll'

const chatStore = useChatStore()
const streamsStore = useStreamsStore()
const { uiMode, activeConversation, activeConversationId, activeMessages, activeThinkState } = storeToRefs(chatStore)

const input = ref('')
const showThinkModal = ref(false)
const messageContainer = ref<HTMLElement | null>(null)

const { scrollToBottom } = useAutoScroll()

async function sendMessage() {
  let target = activeConversationId.value
  const text = input.value.trim()
  if (!text) return

  if (!target) {
    target = await chatStore.createPendingConversationAction(text)
  }

  input.value = ''
  void streamsStore.startStreaming(target, text)
  await nextTick()
  await scrollToBottom(messageContainer.value)
}

const isDraftMode = computed(() => uiMode.value === 'draft' || !activeConversationId.value)

function toggleThinkCollapse() {
  const think = activeThinkState.value
  if (!think || !activeConversationId.value) return
  chatStore.setThinkState(activeConversationId.value, { isCollapsed: !think.isCollapsed })
}

watch(
  () => [activeConversationId.value, activeMessages.value.length, activeThinkState.value?.rawText],
  async () => {
    if (isDraftMode.value) return
    await scrollToBottom(messageContainer.value)
  },
  { deep: true }
)
</script>

<template>
  <section class="chat-panel" :class="{ 'chat-panel--draft': isDraftMode }">
    <header class="chat-header">
      <h2>{{ activeConversation?.title || 'New conversation' }}</h2>
      <p v-if="activeConversation?.isStreaming" class="streaming-label">Generating response...</p>
    </header>

    <div v-if="isDraftMode" class="draft-stage">
      <div class="composer-wrap centered">
        <Composer v-model="input" :disabled="false" @submit="sendMessage" />
      </div>
    </div>

    <template v-else>
      <ThinkPanel :think-state="activeThinkState" @toggle="toggleThinkCollapse" @expand="showThinkModal = true" />

      <div ref="messageContainer" class="message-scroll">
        <MessageList :messages="activeMessages" />
      </div>

      <div class="composer-wrap">
        <Composer v-model="input" :disabled="false" @submit="sendMessage" />
      </div>
    </template>

    <ThinkModal
      :open="showThinkModal"
      :text="activeThinkState?.rawText || ''"
      @close="showThinkModal = false"
    />
  </section>
</template>
