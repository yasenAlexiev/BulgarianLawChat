import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../hooks/useChat'
import { LoadingIndicator } from './LoadingIndicator'
import { MessageBubble } from './MessageBubble'
import { WelcomeScreen } from './WelcomeScreen'

interface ChatMessagesProps {
  messages: ChatMessage[]
  isLoading: boolean
  exampleQuestions: string[]
  onExampleSelect: (question: string) => void
}

export function ChatMessages({
  messages,
  isLoading,
  exampleQuestions,
  onExampleSelect,
}: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const lastMessage = messages[messages.length - 1]
  const hasStreamingMessage = lastMessage?.isStreaming && lastMessage.content === ''

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const isEmpty = messages.length === 0 && !isLoading

  return (
    <div className="chat-messages">
      {isEmpty ? (
        <WelcomeScreen examples={exampleQuestions} onSelect={onExampleSelect} />
      ) : (
        <div className="messages-list">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && hasStreamingMessage && <LoadingIndicator />}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
