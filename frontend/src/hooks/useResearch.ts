import { useState, useEffect, useRef } from 'react'
import type { ResearchRequest, ResearchResponse } from '../types'

export type HistoryItem = ResearchResponse & {
  id: string
  topic: string
  timestamp: number
  depth: number
  provider: string
  model?: string
}

export function useResearch() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentResult, setCurrentResult] = useState<ResearchResponse | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [queueLength, setQueueLength] = useState(0)
  const [queuedTopics, setQueuedTopics] = useState<string[]>([])
  const queueRef = useRef<ResearchRequest[]>([])
  const processingRef = useRef(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('research_history')
    if (saved) {
      try {
        setHistory(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to parse history', e)
      }
    }
  }, [])

  const saveToHistory = (item: HistoryItem) => {
    const newHistory = [item, ...history].slice(0, 50) // Keep last 50
    setHistory(newHistory)
    localStorage.setItem('research_history', JSON.stringify(newHistory))
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem('research_history')
  }

  const stopResearch = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setIsLoading(false)
    }
    processingRef.current = false
    queueRef.current = []
    setQueueLength(0)
    setQueuedTopics([])
    setError('Research stopped by user')
  }


  const executeResearch = async (request: ResearchRequest) => {
    if (processingRef.current) {
      queueRef.current = [...queueRef.current, request]
      const topics = queueRef.current.map(r => r.topic)
      setQueueLength(queueRef.current.length)
      setQueuedTopics(topics)
      return
    }

    processingRef.current = true
    setIsLoading(true)
    setError(null)
    setCurrentResult(null)

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const controller = new AbortController()
    abortControllerRef.current = controller
    let receivedResult = false

    try {

      const baseUrl = (
        import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      ).replace(/\/+$/, '')

      const response = await fetch(`${baseUrl}/research/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(
          `Failed to start research(${response.status}): ${detail} `
        )
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by this browser')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        buffer += decoder.decode(value ?? new Uint8Array(), {
          stream: !done,
        })

        const events = buffer.split(/\r?\n\r?\n/)
        buffer = done ? '' : events.pop() ?? ''

        for (const event of events) {
          const dataLine = event
            .split(/\r?\n/)
            .find(line => line.startsWith('data:'))

          if (!dataLine) continue

          let data: any

          try {
            data = JSON.parse(dataLine.slice(5).trim())
          } catch (e) {
            console.warn('Invalid JSON in research stream:', e, dataLine)
            continue
          }

          if (data.type === 'error') {
            throw new Error(data.message || 'Research failed')
          }

          if (data.type === 'progress') {
            window.dispatchEvent(
              new CustomEvent('research-progress', { detail: data })
            )
          } else if (data.type === 'token') {
            window.dispatchEvent(
              new CustomEvent('research-token', { detail: data })
            )
          } else if (data.type === 'result') {
            const result = data.data as ResearchResponse

            if (!result) {
              throw new Error('Research completed without a result payload')
            }

            receivedResult = true
            setCurrentResult(result)

            saveToHistory({
              ...result,
              id: crypto.randomUUID(),
              topic: request.topic,
              depth: request.max_depth,
              provider: request.provider,
              model: request.model,
              timestamp: Date.now(),
            })
          }
        }

        if (done) break
      }

      if (!receivedResult) {
        throw new Error(
          'The research stream ended without a result. Check the backend logs.'
        )
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Research aborted')
        return
      }

      const msg = err instanceof Error
        ? err.message
        : 'Unknown error occurred'

      setError(msg)
      console.error('Research failed:', err)
    } finally {
      setIsLoading(false)
      processingRef.current = false

      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }

      if (queueRef.current.length > 0) {
        const next = queueRef.current.shift()!
        setQueueLength(queueRef.current.length)
        setQueuedTopics(queueRef.current.map(r => r.topic))
        void executeResearch(next)
      }
    }
  }



  return {
    isLoading,
    error,
    currentResult,
    history,
    queueLength,
    queuedTopics,
    executeResearch,
    stopResearch,
    clearHistory,
    setCurrentResult, // Allow setting result from history
  }
}
