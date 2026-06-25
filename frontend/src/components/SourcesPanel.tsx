import { useState } from 'react'
import type { SourceCitation } from '../types/api'

interface SourcesPanelProps {
  sources: SourceCitation[]
}

function formatCitation(source: SourceCitation): string {
  const parts = [source.law, source.article]
  if (source.paragraph) parts.push(source.paragraph)
  return parts.join(' · ')
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className="sources-panel">
      <button
        type="button"
        className="sources-toggle"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="sources-icon" aria-hidden>
          §
        </span>
        <span>
          {sources.length} {sources.length === 1 ? 'източник' : 'източника'}
        </span>
        <span className={`chevron ${expanded ? 'open' : ''}`} aria-hidden>
          ▾
        </span>
      </button>

      {expanded && (
        <ul className="sources-list">
          {sources.map((source) => {
            const sourceUrl =
              typeof source.metadata?.source_url === 'string'
                ? source.metadata.source_url
                : null

            return (
              <li key={source.chunk_id} className="source-card">
                <div className="source-header">
                  <span className="source-cite">{formatCitation(source)}</span>
                  <span className="source-score">
                    {(source.score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="source-text">{source.text}</p>
                {sourceUrl && (
                  <a
                    className="source-link"
                    href={sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Отвори в lex.bg
                  </a>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
