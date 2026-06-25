import type { ChatMessage } from '../hooks/useChat'
import { MarkdownAnswer } from './MarkdownAnswer'
import { SourcesPanel } from './SourcesPanel'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <article
      className={`message ${isUser ? 'message-user' : 'message-assistant'}${message.error ? ' message-error' : ''}`}
    >
      <div className="message-avatar" aria-hidden>
        {isUser ? 'В' : '§'}
      </div>
      <div className="message-body">
        <div className="message-meta">
          {isUser ? 'Вие' : 'Правен асистент'}
        </div>
        <div className="message-content">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <MarkdownAnswer content={message.content} />
          )}
        </div>
        {!isUser && message.sources && (
          <SourcesPanel sources={message.sources} />
        )}
      </div>
    </article>
  )
}
