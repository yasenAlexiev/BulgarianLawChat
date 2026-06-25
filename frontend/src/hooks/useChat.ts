import { useCallback, useRef, useState } from 'react'
import { ApiError, askQuestion } from '../api/client'
import type { SourceCitation } from '../types/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceCitation[]
  cleanedQuery?: string
  error?: boolean
}

const EXAMPLE_QUESTIONS = [
  'При какви условия работодателят може да уволни без предизвестие по чл. 330 от КТ?',
  'Какво обезщетение дължи работодателят при незаконно уволнение по чл. 225 КТ?',
  'Какви са сроковете за погасяване на вземания по ЗЗД?',
]

function createId(): string {
  return crypto.randomUUID()
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    const question = text.trim()
    if (!question || isLoading) return

    const userMessage: ChatMessage = {
      id: createId(),
      role: 'user',
      content: question,
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const result = await askQuestion({ question })
      const assistantMessage: ChatMessage = {
        id: createId(),
        role: 'assistant',
        content: result.answer,
        sources: result.sources,
        cleanedQuery: result.cleaned_query,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const detail =
        err instanceof ApiError
          ? err.message
          : 'Възникна неочаквана грешка. Проверете дали API сървърът работи.'
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: 'assistant',
          content: detail,
          error: true,
        },
      ])
    } finally {
      setIsLoading(false)
      abortRef.current = null
    }
  }, [isLoading])

  const clearChat = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isLoading,
    exampleQuestions: EXAMPLE_QUESTIONS,
    sendMessage,
    clearChat,
  }
}
