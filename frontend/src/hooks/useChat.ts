import { useCallback, useRef, useState } from 'react'
import { ApiError, askQuestionStream } from '../api/client'
import type { SourceCitation } from '../types/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceCitation[]
  cleanedQuery?: string
  error?: boolean
  isStreaming?: boolean
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

  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    const question = text.trim()
    if (!question || isLoading) return

    const userMessage: ChatMessage = {
      id: createId(),
      role: 'user',
      content: question,
    }

    const assistantMessageId = createId()

    setMessages((prev) => [
      ...prev,
      userMessage,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        isStreaming: true,
      },
    ])
    setIsLoading(true)

    abortRef.current = new AbortController()

    try {
      await askQuestionStream(
        { question },
        {
          onMetadata: (metadata) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      sources: metadata.sources,
                      cleanedQuery: metadata.cleaned_query,
                    }
                  : msg
              )
            )
          },
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            )
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            )
          },
          onError: (error) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: error, error: true, isStreaming: false }
                  : msg
              )
            )
          },
        },
        abortRef.current.signal
      )
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
          )
        )
      } else {
        const detail =
          err instanceof ApiError
            ? err.message
            : 'Възникна неочаквана грешка. Проверете дали API сървърът работи.'
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: detail, error: true, isStreaming: false }
              : msg
          )
        )
      }
    } finally {
      setIsLoading(false)
      abortRef.current = null
    }
  }, [isLoading])

  const clearChat = useCallback(() => {
    stopStreaming()
    setMessages([])
  }, [stopStreaming])

  return {
    messages,
    isLoading,
    exampleQuestions: EXAMPLE_QUESTIONS,
    sendMessage,
    clearChat,
    stopStreaming,
  }
}
