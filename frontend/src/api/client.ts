import type {
  AskRequest,
  AskResponse,
  StreamErrorEvent,
  StreamMetadataEvent,
  StreamTokenEvent,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function askQuestion(body: AskRequest): Promise<AskResponse> {
  const response = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) detail = payload.detail
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, response.status)
  }

  return response.json() as Promise<AskResponse>
}

export interface StreamCallbacks {
  onMetadata: (metadata: StreamMetadataEvent) => void
  onToken: (token: string) => void
  onDone: () => void
  onError: (error: string) => void
}

export async function askQuestionStream(
  body: AskRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/ask/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) detail = payload.detail
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new ApiError('Response body is not readable', 500)
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7)
        } else if (line.startsWith('data: ')) {
          const data = line.slice(6)
          try {
            switch (currentEvent) {
              case 'metadata':
                callbacks.onMetadata(JSON.parse(data) as StreamMetadataEvent)
                break
              case 'token': {
                const tokenEvent = JSON.parse(data) as StreamTokenEvent
                callbacks.onToken(tokenEvent.token)
                break
              }
              case 'done':
                callbacks.onDone()
                break
              case 'error': {
                const errorEvent = JSON.parse(data) as StreamErrorEvent
                callbacks.onError(errorEvent.error)
                break
              }
            }
          } catch {
            /* ignore parse errors */
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
