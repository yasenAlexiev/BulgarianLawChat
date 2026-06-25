import { ChatInput } from './components/ChatInput'
import { ChatMessages } from './components/ChatMessages'
import { useChat } from './hooks/useChat'
import './index.css'

export default function App() {
  const { messages, isLoading, exampleQuestions, sendMessage, clearChat } =
    useChat()

  const hasMessages = messages.length > 0

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            §
          </div>
          <div>
            <h1>Bulgarian Law Chat</h1>
            <p>Търсене и отговори върху нормативни актове</p>
          </div>
        </div>
        {hasMessages && (
          <button type="button" className="clear-button" onClick={clearChat}>
            Нов разговор
          </button>
        )}
      </header>

      <main className="chat-main">
        <ChatMessages
          messages={messages}
          isLoading={isLoading}
          exampleQuestions={exampleQuestions}
          onExampleSelect={sendMessage}
        />
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </main>
    </div>
  )
}
