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

function stripOptionalSseSpace(value: string): string {
  return value.startsWith(' ') ? value.slice(1) : value
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
          dataLines.push(stripOptionalSseSpace(line.slice(5)))
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

const OPEN_TAG = '<think>'
const CLOSE_TAG = '</think>'

function getTrailingTagPrefix(text: string, fullTag: string): string {
  const maxPrefixLength = fullTag.length - 1
  const maxCheckLength = Math.min(maxPrefixLength, text.length)

  for (let len = maxCheckLength; len > 0; len -= 1) {
    if (text.endsWith(fullTag.slice(0, len))) {
      return fullTag.slice(0, len)
    }
  }

  return ''
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
  let tagBuffer = ''

  while (i < text.length) {
    if (currentMode === 'normal') {
      const start = text.indexOf(OPEN_TAG, i)
      if (start === -1) {
        const tail = text.slice(i)
        const carry = getTrailingTagPrefix(tail, OPEN_TAG)
        normalText += carry ? tail.slice(0, -carry.length) : tail
        tagBuffer = carry
        i = text.length
      } else {
        normalText += text.slice(i, start)
        i = start + OPEN_TAG.length
        currentMode = 'think'
      }
    } else {
      const end = text.indexOf(CLOSE_TAG, i)
      if (end === -1) {
        const tail = text.slice(i)
        const carry = getTrailingTagPrefix(tail, CLOSE_TAG)
        thinkText += carry ? tail.slice(0, -carry.length) : tail
        tagBuffer = carry
        i = text.length
      } else {
        thinkText += text.slice(i, end)
        i = end + CLOSE_TAG.length
        currentMode = 'normal'
      }
    }
  }

  return {
    normalText,
    thinkText,
    mode: currentMode,
    tagBuffer
  }
}
