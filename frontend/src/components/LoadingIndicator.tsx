export function LoadingIndicator() {
  return (
    <article className="message message-assistant message-loading">
      <div className="message-avatar" aria-hidden>
        §
      </div>
      <div className="message-body">
        <div className="message-meta">Правен асистент</div>
        <div className="typing-dots" aria-label="Генериране на отговор">
          <span />
          <span />
          <span />
        </div>
      </div>
    </article>
  )
}
