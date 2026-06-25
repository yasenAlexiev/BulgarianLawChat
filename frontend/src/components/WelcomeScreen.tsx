interface WelcomeScreenProps {
  examples: string[]
  onSelect: (question: string) => void
}

export function WelcomeScreen({ examples, onSelect }: WelcomeScreenProps) {
  return (
    <div className="welcome">
      <div className="welcome-hero">
        <div className="welcome-badge">RAG · pgvector · OpenAI</div>
        <h2>Задайте въпрос за българското законодателство</h2>
        <p>
          Асистентът търси в нормативната база и отговаря с цитати от
          съответните закони, членове и алинеи.
        </p>
      </div>

      <div className="example-grid">
        {examples.map((question) => (
          <button
            key={question}
            type="button"
            className="example-card"
            onClick={() => onSelect(question)}
          >
            <span className="example-icon" aria-hidden>
              ?
            </span>
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
