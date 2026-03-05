<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useMarkdown } from '@/composables/useMarkdown'
import type { ThinkState } from '@/types/chat'

const props = defineProps<{
  thinkState: ThinkState | null
  expanded: boolean
  overlayTarget?: HTMLElement | null
}>()

const emits = defineEmits<{
  open: []
  close: []
}>()

const { renderMarkdown } = useMarkdown()

const hasContent = computed(() => Boolean(props.thinkState?.rawText))
const miniAnchorRef = ref<HTMLElement | null>(null)
const miniAnchorRect = ref<DOMRect | null>(null)
const miniContentRef = ref<HTMLElement | null>(null)
const dockPanelRef = ref<HTMLElement | null>(null)
const dockContentRef = ref<HTMLElement | null>(null)

const autoScrollEnabled = ref(true)
const isProgrammaticScroll = ref(false)
const dockMotion = ref({
  x: 0,
  y: 24,
  scale: 0.92
})

let miniRafId: number | null = null
let dockRafId: number | null = null

const showRestoreAutoScroll = computed(
  () => props.expanded && Boolean(props.thinkState?.isThinking) && !autoScrollEnabled.value
)
const teleportTarget = computed(() => props.overlayTarget ?? 'body')
const dockMotionStyle = computed(() => ({
  '--think-origin-x': `${dockMotion.value.x}px`,
  '--think-origin-y': `${dockMotion.value.y}px`,
  '--think-origin-scale': dockMotion.value.scale.toString()
}))

function clearMiniRaf(): void {
  if (miniRafId !== null) {
    cancelAnimationFrame(miniRafId)
    miniRafId = null
  }
}

function clearDockRaf(): void {
  if (dockRafId !== null) {
    cancelAnimationFrame(dockRafId)
    dockRafId = null
  }
}

function scheduleMiniScrollToBottom(): void {
  if (!props.thinkState?.isThinking) return
  clearMiniRaf()
  miniRafId = requestAnimationFrame(() => {
    if (!miniContentRef.value) return
    miniContentRef.value.scrollTop = miniContentRef.value.scrollHeight
    miniRafId = null
  })
}

function scrollDockToBottom(): void {
  if (!dockContentRef.value) return
  isProgrammaticScroll.value = true
  dockContentRef.value.scrollTop = dockContentRef.value.scrollHeight
  clearDockRaf()
  dockRafId = requestAnimationFrame(() => {
    isProgrammaticScroll.value = false
    dockRafId = null
  })
}

function onDockScroll(): void {
  if (!props.thinkState?.isThinking || !autoScrollEnabled.value || isProgrammaticScroll.value) return
  autoScrollEnabled.value = false
}

function restoreAutoScroll(): void {
  autoScrollEnabled.value = true
  scrollDockToBottom()
}

function syncDockMotionFromMini(): void {
  const dock = dockPanelRef.value
  if (!dock) return

  const dockRect = dock.getBoundingClientRect()
  const miniRect = miniAnchorRect.value || miniAnchorRef.value?.getBoundingClientRect() || null
  if (!miniRect || !dockRect.width) {
    dockMotion.value = {
      x: 0,
      y: 24,
      scale: 0.92
    }
    return
  }

  const miniCenterX = miniRect.left + miniRect.width / 2
  const miniCenterY = miniRect.top + miniRect.height / 2
  const dockCenterX = dockRect.left + dockRect.width / 2
  const dockCenterY = dockRect.top + dockRect.height / 2

  dockMotion.value = {
    x: miniCenterX - dockCenterX,
    y: miniCenterY - dockCenterY,
    scale: Math.max(0.1, Math.min(1, miniRect.width / dockRect.width))
  }
}

function openFromMiniAnchor(): void {
  miniAnchorRect.value = miniAnchorRef.value?.getBoundingClientRect() || null
  emits('open')
}

watch(
  () => props.thinkState?.rawText,
  async () => {
    scheduleMiniScrollToBottom()
    if (!props.expanded || !props.thinkState?.isThinking || !autoScrollEnabled.value) return
    await nextTick()
    scrollDockToBottom()
  }
)

watch(
  () => props.expanded,
  async (expanded) => {
    if (!expanded) {
      miniAnchorRect.value = null
      return
    }
    autoScrollEnabled.value = true
    await nextTick()
    syncDockMotionFromMini()
    scrollDockToBottom()
  }
)

watch(
  () => props.overlayTarget,
  async () => {
    if (!props.expanded) return
    await nextTick()
    syncDockMotionFromMini()
  }
)

function onWindowResize(): void {
  if (!props.expanded) return
  syncDockMotionFromMini()
}

onMounted(() => {
  window.addEventListener('resize', onWindowResize, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  clearMiniRaf()
  clearDockRaf()
})
</script>

<template>
  <section v-if="hasContent" class="think-layer">
    <button
      v-if="!expanded"
      ref="miniAnchorRef"
      type="button"
      class="think-mini-anchor think-mini-shell"
      title="Expand Thinking"
      aria-label="Expand Thinking"
      @click="openFromMiniAnchor"
    >
      <div class="think-mini-canvas">
        <div class="think-mini-frame">
          <header class="think-mini-header">
            <div class="left">
              <span v-if="thinkState?.isThinking" class="spinner" />
              <span>Thinking</span>
            </div>
            <span class="think-mini-badge">400x400</span>
          </header>
          <div
            ref="miniContentRef"
            class="think-mini-scroll markdown"
            v-html="renderMarkdown(thinkState?.rawText || '')"
          />
        </div>
      </div>
    </button>

    <teleport :to="teleportTarget">
      <transition name="think-dock">
        <div v-if="expanded" class="think-dock-layer">
          <section ref="dockPanelRef" class="think-dock-panel" :style="dockMotionStyle">
            <header class="think-dock-header">
              <div class="think-dock-title">
                <span v-if="thinkState?.isThinking" class="spinner" />
                <span>Thinking</span>
              </div>
              <button type="button" class="think-dock-close" @click="emits('close')">
                <svg viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M5 10h10" />
                </svg>
              </button>
            </header>

            <div class="think-dock-content-wrap">
              <div
                ref="dockContentRef"
                class="think-dock-content markdown"
                v-html="renderMarkdown(thinkState?.rawText || '')"
                @scroll.passive="onDockScroll"
              />
              <button
                v-if="showRestoreAutoScroll"
                type="button"
                class="think-scroll-bottom-btn"
                title="Scroll to bottom and resume auto-scroll"
                aria-label="Scroll to bottom and resume auto-scroll"
                @click="restoreAutoScroll"
              >
                <svg viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M10 4v9" />
                  <path d="M6.5 10.5L10 14l3.5-3.5" />
                  <path d="M5 16h10" />
                </svg>
              </button>
            </div>
          </section>
        </div>
      </transition>
    </teleport>
  </section>
</template>
