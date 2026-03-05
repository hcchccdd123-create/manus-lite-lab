import { nextTick } from 'vue'

export function useAutoScroll() {
  async function scrollToBottom(container: HTMLElement | null): Promise<void> {
    if (!container) return
    await nextTick()
    container.scrollTop = container.scrollHeight
  }

  return { scrollToBottom }
}
