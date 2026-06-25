export interface SourceCitation {
  chunk_id: string
  law: string
  article: string
  paragraph: string | null
  text: string
  metadata: Record<string, unknown>
  score: number
}

export interface AskResponse {
  question: string
  cleaned_query: string
  answer: string
  sources: SourceCitation[]
}

export interface AskRequest {
  question: string
  retrieval_top_k?: number
  context_top_k?: number
  rerank?: boolean | null
}

export interface StreamMetadataEvent {
  question: string
  cleaned_query: string
  sources: SourceCitation[]
}

export interface StreamTokenEvent {
  token: string
}

export interface StreamErrorEvent {
  error: string
}
