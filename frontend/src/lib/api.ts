import type { ResearchRequest, ResearchResponse } from '../types'

const API_BASE = () => (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

const TRENDING_CACHE_KEY = 'multi-agent-research-system-trending-topics'

function loadTrendingCache(): string[] | null {
  try {
    const cached = localStorage.getItem(TRENDING_CACHE_KEY)
    if (!cached) return null
    const parsed = JSON.parse(cached)
    if (Array.isArray(parsed) && parsed.length > 0) return parsed
    return null
  } catch {
    return null
  }
}

function saveTrendingCache(topics: string[]): void {
  try {
    localStorage.setItem(TRENDING_CACHE_KEY, JSON.stringify(topics))
  } catch {
    // localStorage might be full or unavailable
  }
}

async function fetchTrendingFromApi(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE()}/trending`)
    if (!response.ok) return []
    const data = (await response.json()) as { topics: string[] }
    return data.topics ?? []
  } catch {
    return []
  }
}

export async function fetchTrendingTopics(): Promise<string[]> {
  // Return cached data immediately if available
  const cached = loadTrendingCache()
  if (cached) {
    // Refresh the cache in the background for next visit
    fetchTrendingFromApi().then(fresh => {
      if (fresh.length > 0) saveTrendingCache(fresh)
    }).catch(() => {})
    return cached
  }

  // No cache — fetch fresh and cache it
  const fresh = await fetchTrendingFromApi()
  if (fresh.length > 0) saveTrendingCache(fresh)
  return fresh
}

export async function refreshTrendingTopics(): Promise<string[]> {
  // Always fetch fresh from API, bypass cache
  const fresh = await fetchTrendingFromApi()
  if (fresh.length > 0) saveTrendingCache(fresh)
  return fresh
}

export async function runResearch(payload: ResearchRequest): Promise<ResearchResponse> {
  const response = await fetch(`${API_BASE()}/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const detail = await safeParseError(response)
    throw new Error(detail ?? 'Something went wrong while running the research workflow')
  }

  return response.json() as Promise<ResearchResponse>
}

async function safeParseError(response: Response): Promise<string | null> {
  try {
    const payload = (await response.json()) as { detail?: string }
    return payload.detail ?? null
  } catch (error) {
    return null
  }
}

// ── ArXiv DOI Resolution ──

export async function resolveDois(urls: string[]): Promise<Record<string, string | null>> {
  try {
    const response = await fetch(`${API_BASE()}/resolve-dois`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(urls),
    })
    if (!response.ok) return {}
    const data = (await response.json()) as { dois: Record<string, string | null> }
    return data.dois ?? {}
  } catch {
    return {}
  }
}

// ── PDF Upload ──

export type UploadResult = {
  filename: string
  content: string
  char_count: number
}

export async function uploadPdf(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE()}/upload-pdf`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const detail = await safeParseError(response)
    throw new Error(detail ?? 'Failed to upload PDF')
  }
  return response.json() as Promise<UploadResult>
}

// ── Explain / Simplify ──

export async function explainReport(report: string, mode: 'brief' | 'eli5' = 'brief'): Promise<string> {
  try {
    const response = await fetch(`${API_BASE()}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report, mode }),
    })
    if (!response.ok) throw new Error('Explain failed')
    const data = (await response.json()) as { explanation: string }
    return data.explanation ?? report
  } catch {
    return report
  }
}

// ── Research Timeline ──

export type TimelineData = { year: number; label: string }[]

export async function fetchTimeline(report: string, sources: string[]): Promise<TimelineData> {
  try {
    const response = await fetch(`${API_BASE()}/timeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report, sources }),
    })
    if (!response.ok) return []
    const data = (await response.json()) as { timeline: TimelineData }
    return data.timeline ?? []
  } catch {
    return []
  }
}

// ── Follow-up Chat (non-streaming) ──

export async function chatFollowup(
  question: string,
  report: string,
  sources: string[],
  provider?: string,
  model?: string,
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE()}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, report, sources, provider, model }),
    })
    if (!response.ok) throw new Error('Chat failed')
    const data = (await response.json()) as { answer: string }
    return data.answer ?? 'No response'
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Chat failed'
    throw new Error(msg)
  }
}

// ── Generate HTML for PDF ──

export async function generatePrintHtml(topic: string, report: string, sources: string[]): Promise<string> {
  try {
    const response = await fetch(`${API_BASE()}/generate-html`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, report, sources }),
    })
    if (!response.ok) throw new Error('HTML generation failed')
    const data = (await response.json()) as { html: string }
    return data.html ?? ''
  } catch {
    return ''
  }
}
