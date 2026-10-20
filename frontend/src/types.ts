export type ResearchRequest = {
  topic: string
  max_depth: number
  num_papers: number
  provider: string
  openrouter_api_key?: string
  api_key?: string
  model?: string
  critic_strictness?: number

  // Uploaded PDF content for additional context
  uploaded_content?: string

  // Zero-knowledge encrypted API key fields
  encrypted_api_key?: string
  encryption_iv?: string
  encryption_salt?: string
  encryption_passphrase?: string
}

export type ImageResult = {
  title: string
  image_url: string
  thumbnail_url?: string
  source_url: string
  source_domain: string
  width?: number
  height?: number
}

export type ResearchResponse = {
  final_report: string
  sources: string[]
  topic: string
  graph_data?: {
    nodes: Array<{ id: string; type?: string; label?: string; url?: string }>
    links: Array<{ source: string; target: string; weight?: number }>
  }
  images?: ImageResult[]
  graphs?: ImageResult[]
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export type TimelineEntry = {
  year: number
  label: string
}

export type CitationStyle = 'inline' | 'apa' | 'mla' | 'chicago' | 'ieee'

