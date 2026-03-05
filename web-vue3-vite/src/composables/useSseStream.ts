export interface ParsedEvent {
  event: string
  data: string
}

function findEventBoundary(buffer: string): number {
  const lf = buffer.indexOf('\n\n')
  const crlf = buffer.indexOf('\r\n\r\n')

  if (lf === -1) return crlf
  if (crlf === -1) return lf
  return Math.min(lf, crlf)
}

function boundaryLengthAt(buffer: string, index: number): number {
  return buffer.startsWith('\r\n\r\n', index) ? 4 : 2
}

export async function consumeSseStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (evt: ParsedEvent) => void
): Promise<void> {
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    while (true) {
      const index = findEventBoundary(buffer)
      if (index < 0) break

      const raw = buffer.slice(0, index)
      buffer = buffer.slice(index + boundaryLengthAt(buffer, index))

      let eventName = 'message'
      const dataLines: string[] = []
      for (const line of raw.split(/\r?\n/)) {
        if (!line || line.startsWith(':')) continue
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trim())
        }
      }

      if (dataLines.length > 0 || eventName !== 'message') {
        onEvent({ event: eventName, data: dataLines.join('\n') })
      }
    }
  }
}

export interface ThinkSplitResult {
  normalText: string
  thinkText: string
  mode: 'normal' | 'think'
  tagBuffer: string
}

export function splitThinkDelta(
  chunk: string,
  mode: 'normal' | 'think',
  existingTagBuffer: string
): ThinkSplitResult {
  const text = existingTagBuffer + chunk
  let i = 0
  let currentMode = mode
  let normalText = ''
  let thinkText = ''

  while (i < text.length) {
    if (currentMode === 'normal') {
      const start = text.indexOf('<think>', i)
      if (start === -1) {
        normalText += text.slice(i)
        i = text.length
      } else {
        normalText += text.slice(i, start)
        i = start + '<think>'.length
        currentMode = 'think'
      }
    } else {
      const end = text.indexOf('</think>', i)
      if (end === -1) {
        thinkText += text.slice(i)
        i = text.length
      } else {
        thinkText += text.slice(i, end)
        i = end + '</think>'.length
        currentMode = 'normal'
      }
    }
  }

  let tagBuffer = ''
  const suffixCandidates = ['<think>', '</think>', '<think', '</think']
  for (const candidate of suffixCandidates) {
    if (text.endsWith(candidate)) {
      tagBuffer = candidate
      if (candidate && normalText.endsWith(candidate)) {
        normalText = normalText.slice(0, -candidate.length)
      }
      if (candidate && thinkText.endsWith(candidate)) {
        thinkText = thinkText.slice(0, -candidate.length)
      }
      break
    }
  }

  return {
    normalText,
    thinkText,
    mode: currentMode,
    tagBuffer
  }
}
