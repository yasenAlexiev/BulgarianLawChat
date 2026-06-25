import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const submit = () => {
    if (!value.trim() || disabled) return
    onSend(value)
    setValue('')
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="chat-input-shell">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Задайте въпрос за българско законодателство…"
          rows={1}
          disabled={disabled}
          aria-label="Въпрос"
        />
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !value.trim()}
          aria-label="Изпрати"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden>
            <path d="M3.4 20.4 22 12 3.4 3.6l1.7 7.2L17 12l-11.9 1.2-1.7 7.2z" />
          </svg>
        </button>
      </div>
      <p className="input-hint">
        Enter за изпращане · Shift+Enter за нов ред · Отговорите са информативни, не правен съвет
      </p>
    </form>
  )
}
