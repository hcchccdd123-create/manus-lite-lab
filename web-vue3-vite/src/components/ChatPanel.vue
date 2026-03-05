<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'

import Composer from './Composer.vue'
import MessageList from './MessageList.vue'
import ThinkPanel from './ThinkPanel.vue'
import { useChatStore } from '@/stores/chat'
import { useStreamsStore } from '@/stores/streams'

const chatStore = useChatStore()
const streamsStore = useStreamsStore()
const { uiMode, activeConversation, activeConversationId, activeMessages, activeThinkState } = storeToRefs(chatStore)

const input = ref('')
const isThinkExpanded = ref(false)
const deepThinkingEnabled = ref(true)
const chatPanelRef = ref<HTMLElement | null>(null)
const messageContainer = ref<HTMLElement | null>(null)
const messageAutoScrollEnabled = ref(true)
const isProgrammaticMessageScroll = ref(false)
let releaseMessageScrollLockId: number | null = null

const hasThinkContent = computed(() => Boolean(activeThinkState.value?.rawText))
const showRestoreMessageScroll = computed(() => !messageAutoScrollEnabled.value)
const activeMessageContentSignature = computed(() =>
  activeMessages.value
    .map((item) => `${item.id}:${item.content.length}:${item.isStreamingDraft ? 1 : 0}`)
    .join('|')
)

function clearReleaseMessageScrollLock() {
  if (releaseMessageScrollLockId === null) return
  cancelAnimationFrame(releaseMessageScrollLockId)
  releaseMessageScrollLockId = null
}

function scrollMessagesToBottom() {
  const container = messageContainer.value
  if (!container) return
  isProgrammaticMessageScroll.value = true
  container.scrollTop = container.scrollHeight
  clearReleaseMessageScrollLock()
  releaseMessageScrollLockId = requestAnimationFrame(() => {
    isProgrammaticMessageScroll.value = false
    releaseMessageScrollLockId = null
  })
}

async function sendMessage() {
  let target = activeConversationId.value
  const text = input.value.trim()
  if (!text) return

  if (!target) {
    target = await chatStore.createPendingConversationAction(text)
  }

  input.value = ''
  void streamsStore.startStreaming(target, text, {
    enableThinking: deepThinkingEnabled.value
  })
  await nextTick()
  messageAutoScrollEnabled.value = true
  scrollMessagesToBottom()
}

const isDraftMode = computed(() => uiMode.value === 'draft' || !activeConversationId.value)

function openThinkPanel() {
  if (!hasThinkContent.value) return
  isThinkExpanded.value = true
}

function closeThinkPanel() {
  isThinkExpanded.value = false
}

function toggleDeepThinking(nextValue: boolean) {
  deepThinkingEnabled.value = nextValue
}

function onMessageScroll() {
  const container = messageContainer.value
  if (!container || isProgrammaticMessageScroll.value) return
  const nearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 20
  messageAutoScrollEnabled.value = nearBottom
}

function restoreMessageAutoScroll() {
  messageAutoScrollEnabled.value = true
  scrollMessagesToBottom()
}

watch(
  () => activeMessageContentSignature.value,
  async () => {
    if (isDraftMode.value || !messageAutoScrollEnabled.value) return
    await nextTick()
    scrollMessagesToBottom()
  },
  { flush: 'post' }
)

watch(
  () => activeConversationId.value,
  async () => {
    isThinkExpanded.value = false
    messageAutoScrollEnabled.value = true
    await nextTick()
    scrollMessagesToBottom()
  }
)

watch(
  () => hasThinkContent.value,
  (visible) => {
    if (!visible) {
      isThinkExpanded.value = false
    }
  }
)

onBeforeUnmount(() => {
  clearReleaseMessageScrollLock()
})
</script>

<template>
  <section ref="chatPanelRef" class="chat-panel" :class="{ 'chat-panel--draft': isDraftMode }">
    <header class="chat-header">
      <h2>{{ activeConversation?.title || 'New conversation' }}</h2>
      <p v-if="activeConversation?.isStreaming" class="streaming-label">Generating response...</p>
    </header>

    <div v-if="isDraftMode" class="draft-stage">
      <div class="composer-wrap centered">
        <Composer
          v-model="input"
          :disabled="false"
          :deep-thinking-enabled="deepThinkingEnabled"
          @toggle-deep-thinking="toggleDeepThinking"
          @submit="sendMessage"
        />
      </div>
    </div>

    <template v-else>
      <div class="message-scroll-wrap">
        <div ref="messageContainer" class="message-scroll" @scroll.passive="onMessageScroll">
          <MessageList :messages="activeMessages" />
        </div>
        <button
          v-if="showRestoreMessageScroll"
          type="button"
          class="message-scroll-bottom-btn"
          title="恢复自动滚动并回到底部"
          aria-label="恢复自动滚动并回到底部"
          @click="restoreMessageAutoScroll"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="M10 4v9" />
            <path d="M6.5 10.5L10 14l3.5-3.5" />
            <path d="M5 16h10" />
          </svg>
        </button>
      </div>

      <div class="composer-wrap">
        <button
          v-if="hasThinkContent && !isThinkExpanded"
          type="button"
          class="think-mobile-entry"
          title="Expand Thinking"
          aria-label="Expand Thinking"
          @click="openThinkPanel"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="M4 10h12" />
            <path d="M10 4v12" />
          </svg>
        </button>
        <Composer
          v-model="input"
          :disabled="false"
          :deep-thinking-enabled="deepThinkingEnabled"
          @toggle-deep-thinking="toggleDeepThinking"
          @submit="sendMessage"
        />
        <ThinkPanel
          :think-state="activeThinkState"
          :expanded="isThinkExpanded"
          :overlay-target="chatPanelRef"
          @open="openThinkPanel"
          @close="closeThinkPanel"
        />
      </div>
    </template>
  </section>
</template>
