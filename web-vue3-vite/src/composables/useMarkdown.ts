import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

export function useMarkdown() {
  function renderMarkdown(text: string): string {
    return DOMPurify.sanitize(md.render(text || ''))
  }

  return { renderMarkdown }
}
