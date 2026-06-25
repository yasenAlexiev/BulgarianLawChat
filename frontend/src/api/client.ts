import type { AskRequest, AskResponse } from '../types/api'

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
