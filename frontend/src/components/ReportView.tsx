import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import {
  ExternalLink, FileText, Copy, Check, Download,
  Volume2, StopCircle, Maximize2, Minimize2, Quote,
  Bookmark, ChevronDown, Eye, ArrowUp, Clock,
  Layers, Globe, BookOpen, Printer, Sparkles,
  MessageSquare, Hash, BarChart3,
  Lightbulb, Unlink,
} from 'lucide-react'
import { useState, useEffect, useRef, useMemo } from 'react'
import type { ResearchResponse, CitationStyle, TimelineEntry } from '../types'
import { KnowledgeGraph } from './KnowledgeGraph'
import { ErrorBoundary } from './ErrorBoundary'
import { ImageGallery } from './ImageGallery'
import { ChatPanel } from './ChatPanel'
import { resolveDois, explainReport, fetchTimeline, generatePrintHtml } from '../lib/api'

interface Props {
  data: ResearchResponse
  provider?: string
  model?: string
}

/* ─── Helpers ─── */

function extractDomain(url: string): string {
  try { return new URL(url).hostname.replace('www.', '') }
  catch { return url }
}

function estimateReadingTime(text: string): number {
  const wpm = 200
  return Math.max(1, Math.ceil(text.split(/\s+/).length / wpm))
}

function formatDate(ts?: number): string {
  const d = ts ? new Date(ts) : new Date()
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/* ─── Strip markdown for speech ─── */

function stripMarkdown(text: string): string {
  return text
    // Remove code blocks (```...```)
    .replace(/```[\s\S]*?```/g, '')
    // Remove inline code (`code`)
    .replace(/`[^`]+`/g, '')
    // Remove images (![alt](url))
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    // Replace links [text](url) with just text
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    // Remove heading markers (#, ##, ###, etc.)
    .replace(/^#{1,6}\s+/gm, '')
    // Remove bold/italic markers
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    // Remove horizontal rules
    .replace(/^-{3,}\s*$/gm, '')
    // Remove blockquote markers
    .replace(/^>\s+/gm, '')
    // Remove list markers (-, *, +, numbers)
    .replace(/^[\s]*[-*+]\s+/gm, '')
    .replace(/^[\s]*\d+\.\s+/gm, '')
    // Remove citation references like [S1], [1], etc.
    .replace(/\[S\d+\]/g, '')
    .replace(/\^\[\d+\]/g, '')
    // Collapse multiple newlines
    .replace(/\n{3,}/g, '\n\n')
    // Collapse multiple spaces
    .replace(/ {2,}/g, ' ')
    .trim()
}

function isArxivUrl(url: string): boolean {
  return /arxiv\.org/i.test(url)
}

/* ─── Citation Format Transformers ─── */

function transformCitations(text: string, style: CitationStyle): string {
  if (style === 'inline') return text

  // Map [S#] references to formatted citations
  const citationMap = new Map<string, string>()
  let idx = 1

  // APA: (Author, Year)
  if (style === 'apa') {
    return text.replace(/\[S(\d+)\]/g, (_, num) => {
      const key = `S${num}`
      if (!citationMap.has(key)) {
        citationMap.set(key, `(Author et al., n.d.)`)
      }
      return citationMap.get(key)!
    })
  }

  // MLA: (Author page)
  if (style === 'mla') {
    return text.replace(/\[S(\d+)\]/g, (_, num) => {
      const key = `S${num}`
      if (!citationMap.has(key)) {
        citationMap.set(key, `(Author ${num})`)
      }
      return citationMap.get(key)!
    })
  }

  // Chicago: superscript numbers
  if (style === 'chicago') {
    return text.replace(/\[S(\d+)\]/g, (_, num) => `[${num}]`)
  }

  // IEEE: bracketed numbers
  if (style === 'ieee') {
    return text.replace(/\[S(\d+)\]/g, (_, num) => `[${num}]`)
  }

  return text
}

/* ─── Component ─── */

export function ReportView({ data, provider, model }: Props) {
  const [copied, setCopied] = useState(false)
  const [showGraph, setShowGraph] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [showBackToTop, setShowBackToTop] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [showChat, setShowChat] = useState(false)
  const [showTimeline, setShowTimeline] = useState(false)
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [timelineLoading, setTimelineLoading] = useState(false)
  const [citationStyle, setCitationStyle] = useState<CitationStyle>('inline')
  const [doiMap, setDoiMap] = useState<Record<string, string | null>>({})
  const [showExplain, setShowExplain] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explainLoading, setExplainLoading] = useState(false)

  const readingTime = useMemo(() => estimateReadingTime(data.final_report || ''), [data.final_report])
  const sources = useMemo(() => (
    Array.isArray(data.sources)
      ? [...new Set(data.sources.filter(s => typeof s === 'string').map(s => s.trim()).filter(Boolean))]
      : []
  ), [data.sources])

  const transformedReport = useMemo(
    () => citationStyle === 'inline' ? data.final_report : transformCitations(data.final_report, citationStyle),
    [data.final_report, citationStyle]
  )

  /* ─── Lifecycle ─── */
  useEffect(() => {
    setSpeechSupported('speechSynthesis' in window)
    return () => window.speechSynthesis.cancel()
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const onScroll = () => {
      const p = el.scrollHeight > el.clientHeight
        ? Math.min(el.scrollTop / (el.scrollHeight - el.clientHeight), 1) : 0
      setScrollProgress(p)
      setShowBackToTop(el.scrollTop > 500)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  // Resolve DOIs for arXiv sources
  useEffect(() => {
    const arxivSources = sources.filter(isArxivUrl)
    if (arxivSources.length > 0) {
      resolveDois(arxivSources).then(setDoiMap).catch((e) => console.warn('DOI resolve failed', e))
    }
  }, [sources])

  /* ─── Handlers ─── */
  const handleCopy = () => {
    navigator.clipboard.writeText(data.final_report || '')
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([data.final_report || ''], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'research-report.md'
    document.body.appendChild(a); a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const toggleSpeech = () => {
    if (isSpeaking) { window.speechSynthesis.cancel(); setIsSpeaking(false) }
    else {
      const text = stripMarkdown(data.final_report || 'No content.')
      const u = new SpeechSynthesisUtterance(text)
      u.onend = () => setIsSpeaking(false); u.rate = 1.1
      window.speechSynthesis.speak(u); setIsSpeaking(true)
    }
  }

  const scrollToTop = () => scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' })

  // ── PDF Print Export ──
  const handlePrintPdf = async () => {
    const html = await generatePrintHtml(data.topic || 'Research Report', data.final_report || '', sources)
    if (html) {
      const win = window.open('', '_blank')
      if (win) {
        win.document.write(html)
        win.document.close()
        win.focus()
        win.print()
      }
    }
  }

  // ── Timeline ──
  const handleToggleTimeline = async () => {
    if (timeline.length > 0) { setShowTimeline(!showTimeline); return }
    setShowTimeline(true)
    setTimelineLoading(true)
    const data_timeline = await fetchTimeline(data.final_report || '', sources)
    setTimeline(data_timeline)
    setTimelineLoading(false)
  }

  // ── Explain Mode ──
  const handleToggleExplain = async () => {
    if (explanation) { setShowExplain(!showExplain); return }
    setShowExplain(true)
    setExplainLoading(true)
    const brief = await explainReport(data.final_report || '')
    setExplanation(brief)
    setExplainLoading(false)
  }

  /* ─── Render ─── */
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-[#0c0b0a]' : ''}`}
    >
      {/* Scroll progress */}
      <div className="fixed left-0 top-0 w-full h-[3px] z-[60] pointer-events-none">
        <div className="h-full bg-gradient-to-r from-primary-600 via-primary-400 to-accent-500 transition-all duration-150 ease-out"
          style={{ width: `${scrollProgress * 100}%` }} />
      </div>

      <div ref={scrollRef} className={`${isFullscreen ? 'h-full overflow-y-auto relative z-20' : ''}`}>
        <div className={isFullscreen ? 'max-w-5xl mx-auto px-6 sm:px-10 py-8' : ''}>
          {/* HEADER */}
          <div className="mb-6 group">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-3 mb-2.5">
                  <div className="relative shrink-0">
                    <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary-600 via-primary-500 to-primary-400 flex items-center justify-center shadow-lg shadow-primary-500/25 ring-1 ring-white/10">
                      <FileText className="w-5 h-5 text-white" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#0c0b0a] flex items-center justify-center">
                      <Check className="w-2.5 h-2.5 text-white" />
                    </div>
                  </div>
                  <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-warm-900 dark:text-warm-100 tracking-tight line-clamp-2 leading-tight">
                      {data.topic || 'Research Report'}
                    </h1>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                      <span className="text-xs text-warm-400 flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />{readingTime} min read
                      </span>
                      <span className="text-warm-300 dark:text-warm-600 hidden sm:inline">·</span>
                      <span className="text-xs text-warm-400 flex items-center gap-1.5">
                        <Layers className="w-3 h-3" />{sources.length} source{sources.length !== 1 ? 's' : ''}
                      </span>
                      <span className="text-warm-300 dark:text-warm-600 hidden sm:inline">·</span>
                      <span className="text-xs text-warm-400 flex items-center gap-1.5">
                        <Globe className="w-3 h-3" />{formatDate()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-0.5 shrink-0 bg-white/40 dark:bg-white/[0.03] rounded-2xl p-1 border border-warm-200/40 dark:border-white/[0.06] shadow-sm flex-wrap">
                {speechSupported && (
                  <button onClick={toggleSpeech}
                    className={`p-2 rounded-xl transition-all duration-200 ${isSpeaking ? 'text-primary-600 bg-primary-50 dark:bg-primary-950/40' : 'text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-white/70 dark:hover:bg-white/[0.06]'}`}
                    title={isSpeaking ? 'Stop reading' : 'Read aloud'}>
                    {isSpeaking ? <StopCircle className="w-[16px] h-[16px]" /> : <Volume2 className="w-[16px] h-[16px]" />}
                  </button>
                )}
                <button onClick={handlePrintPdf}
                  className="p-2 rounded-xl text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-white/70 dark:hover:bg-white/[0.06] transition-all duration-200"
                  title="Print as PDF">
                  <Printer className="w-[16px] h-[16px]" />
                </button>
                <button onClick={handleDownload}
                  className="p-2 rounded-xl text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-white/70 dark:hover:bg-white/[0.06] transition-all duration-200"
                  title="Download markdown">
                  <Download className="w-[16px] h-[16px]" />
                </button>
                <button onClick={handleCopy}
                  className="p-2 rounded-xl text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-white/70 dark:hover:bg-white/[0.06] transition-all duration-200 relative"
                  title="Copy report">
                  {copied ? <Check className="w-[16px] h-[16px] text-emerald-500" /> : <Copy className="w-[16px] h-[16px]" />}
                </button>
                <button onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-xl text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-white/70 dark:hover:bg-white/[0.06] transition-all duration-200 hidden sm:block"
                  title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}>
                  {isFullscreen ? <Minimize2 className="w-[16px] h-[16px]" /> : <Maximize2 className="w-[16px] h-[16px]" />}
                </button>
              </div>
            </div>

            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-2 mt-3 px-1">
              {/* Citation style */}
              <div className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-white/50 dark:bg-white/[0.04] border border-warm-200/30 dark:border-white/[0.06]">
                <Hash className="w-3 h-3 text-warm-400" />
                <select
                  value={citationStyle}
                  onChange={(e) => setCitationStyle(e.target.value as CitationStyle)}
                  className="text-[10px] bg-transparent text-warm-600 dark:text-warm-400 focus:outline-none cursor-pointer border-none"
                >
                  <option value="inline">Inline [S#]</option>
                  <option value="apa">APA</option>
                  <option value="mla">MLA</option>
                  <option value="chicago">Chicago</option>
                  <option value="ieee">IEEE</option>
                </select>
              </div>

              {/* Explain button */}
              <button onClick={handleToggleExplain}
                className={`flex items-center gap-1 px-2.5 py-1.5 text-[10px] rounded-lg transition-all duration-200 ${
                  showExplain
                    ? 'bg-primary-100 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 border border-primary-200/50 dark:border-primary-800/50'
                    : 'bg-white/50 dark:bg-white/[0.04] text-warm-500 dark:text-warm-400 border border-warm-200/30 dark:border-white/[0.06] hover:bg-warm-100/60 dark:hover:bg-white/[0.08]'
                }`}>
                <Sparkles className="w-3 h-3" />
                {explainLoading ? 'Loading...' : 'Brief'}
              </button>

              {/* Timeline button */}
              <button onClick={handleToggleTimeline}
                className={`flex items-center gap-1 px-2.5 py-1.5 text-[10px] rounded-lg transition-all duration-200 ${
                  showTimeline
                    ? 'bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300 border border-amber-200/50 dark:border-amber-800/50'
                    : 'bg-white/50 dark:bg-white/[0.04] text-warm-500 dark:text-warm-400 border border-warm-200/30 dark:border-white/[0.06] hover:bg-warm-100/60 dark:hover:bg-white/[0.08]'
                }`}>
                <BarChart3 className="w-3 h-3" />
                Timeline
              </button>

              {/* Chat button */}
              <button onClick={() => setShowChat(!showChat)}
                className={`flex items-center gap-1 px-2.5 py-1.5 text-[10px] rounded-lg transition-all duration-200 ${
                  showChat
                    ? 'bg-primary-100 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 border border-primary-200/50 dark:border-primary-800/50'
                    : 'bg-white/50 dark:bg-white/[0.04] text-warm-500 dark:text-warm-400 border border-warm-200/30 dark:border-white/[0.06] hover:bg-warm-100/60 dark:hover:bg-white/[0.08]'
                }`}>
                <MessageSquare className="w-3 h-3" />
                Ask
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-8 lg:gap-10 items-start">
            {/* LEFT COLUMN */}
            <div className="min-w-0 space-y-6">
              {/* Explain mode */}
              {showExplain && explanation && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass-card !rounded-2xl p-5 overflow-hidden"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-semibold text-warm-700 dark:text-warm-300">Executive Brief</span>
                  </div>
                  <div className="text-xs text-warm-600 dark:text-warm-400 leading-relaxed prose-warm max-h-[300px] overflow-y-auto">
                    <ReactMarkdown>{explanation}</ReactMarkdown>
                  </div>
                </motion.div>
              )}

              {/* Timeline */}
              {showTimeline && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass-card !rounded-2xl p-5 overflow-hidden"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart3 className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-semibold text-warm-700 dark:text-warm-300">Research Timeline</span>
                  </div>
                  {timelineLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                  ) : timeline.length > 0 ? (
                    <div className="relative pl-6 space-y-4">
                      {timeline.map((entry, i) => (
                        <div key={i} className="relative">
                          <div className="absolute -left-6 top-0.5 w-3 h-3 rounded-full bg-primary-500 ring-2 ring-white dark:ring-[#0c0b0a]" />
                          {i < timeline.length - 1 && (
                            <div className="absolute -left-[19.5px] top-3.5 w-0.5 h-full bg-primary-200 dark:bg-primary-900" />
                          )}
                          <p className="text-[11px] font-bold text-primary-600 dark:text-primary-400">{entry.year}</p>
                          <p className="text-[11px] text-warm-600 dark:text-warm-400 mt-0.5 leading-relaxed">{entry.label}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-warm-400 py-4 text-center">No timeline data available</p>
                  )}
                </motion.div>
              )}

              {/* Report content */}
              <div className="glass-card !rounded-2xl p-6 sm:p-8 lg:p-10">
                <div className="prose-warm">
                  <ReactMarkdown
                    components={{
                      a: ({ href, children, ...props }) => (
                        <a href={href} target="_blank" rel="noreferrer"
                          className="inline items-center gap-1 text-primary-600 dark:text-primary-400 no-underline border-b border-primary-300/30 dark:border-primary-700/30 hover:border-primary-400 dark:hover:border-primary-500 transition-colors" {...props}>
                          {children}<ExternalLink className="w-3 h-3 inline-block opacity-60 ml-0.5" />
                        </a>
                      ),
                      pre: ({ children }) => (
                        <div className="relative group/code">
                          <div className="absolute top-3 right-3 opacity-0 group-hover/code:opacity-100 transition-opacity">
                            <span className="text-[10px] text-warm-400 font-mono bg-black/30 px-2 py-1 rounded-md">code</span>
                          </div>
                          <pre className="!mt-0">{children}</pre>
                        </div>
                      ),
                    }}
                  >
                    {transformedReport || '*No report content available.*'}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Report footer */}
              <div className="flex items-center justify-center gap-3 py-4 text-warm-400">
                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-warm-200/50 dark:via-white/[0.06] to-transparent" />
                <span className="text-[11px] font-medium tracking-wider uppercase flex items-center gap-2">
                  <BookOpen className="w-3 h-3" />End of report
                </span>
                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-warm-200/50 dark:via-white/[0.06] to-transparent" />
              </div>
            </div>

            {/* RIGHT COLUMN */}
            <div className="lg:sticky lg:top-6 space-y-6">
              
              {/* KNOWLEDGE GRAPH */}
              <div className="mb-4">
                <div className={`rounded-2xl overflow-hidden border transition-all duration-300 ${
                  showGraph ? 'border-warm-200/50 dark:border-white/[0.08] shadow-md shadow-primary-500/5' : 'border-warm-200/30 dark:border-white/[0.04] shadow-sm'
                }`}>
                  <button onClick={() => setShowGraph(!showGraph)}
                    className="w-full flex items-center justify-between px-4 py-3 bg-warm-100/60 dark:bg-white/[0.03] hover:bg-warm-200/50 dark:hover:bg-white/[0.06] transition-colors" aria-expanded={showGraph}>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-950/40 dark:to-primary-900/20 flex items-center justify-center ring-1 ring-primary-200/30 dark:ring-primary-800/20">
                        <Eye className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                      </div>
                      <span className="text-sm font-semibold text-warm-800 dark:text-warm-200">Knowledge Graph</span>
                    </div>
                    <motion.div animate={{ rotate: showGraph ? 180 : 0 }} transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}>
                      <ChevronDown className="w-4 h-4 text-warm-400" />
                    </motion.div>
                  </button>
                  <motion.div initial={false} animate={{ height: showGraph ? 'auto' : 0, opacity: showGraph ? 1 : 0 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }} className="overflow-hidden">
                    <ErrorBoundary>
                      <KnowledgeGraph topic={data.topic || 'Research Topic'} sources={sources} graphData={data.graph_data} />
                    </ErrorBoundary>
                  </motion.div>
                </div>
              </div>

              {/* Chat Panel */}
              <ErrorBoundary>
                {showChat && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                  >
                    <ChatPanel report={data.final_report || ''} sources={sources} provider={provider} model={model} />
                  </motion.div>
                )}
              </ErrorBoundary>

              {/* References header */}
              <div className="flex items-center gap-3 px-1">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-50 to-accent-100 dark:from-accent-950/30 dark:to-accent-900/20 flex items-center justify-center ring-1 ring-accent-200/30 dark:ring-accent-800/20">
                  <Bookmark className="w-4 h-4 text-accent-600 dark:text-accent-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-warm-800 dark:text-warm-200">References</h3>
                  <p className="text-[11px] text-warm-400">{sources.length} source{sources.length !== 1 ? 's' : ''}</p>
                </div>
              </div>

              {/* Reference cards with DOI badges */}
              <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-1">
                {sources.map((source, i) => {
                  const domain = extractDomain(source)
                  const isArxiv = isArxivUrl(source)
                  const arxivId = isArxiv ? source.match(/\d+\.\d+/)?.[0] : null
                  const doi = arxivId ? doiMap[arxivId] : null
                  return (
                    <div key={i} id={`ref-${i}`}
                      onClick={() => window.open(source, '_blank')}
                      className="group relative px-4 py-3.5 rounded-xl border cursor-pointer transition-all duration-200 bg-white/50 dark:bg-white/[0.03] border-warm-200/40 dark:border-white/[0.06] hover:border-warm-300 dark:hover:border-white/[0.12] hover:shadow-md hover:-translate-y-0.5">
                      <div className="flex items-start gap-3 relative">
                        <span className="w-7 h-7 rounded-xl flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5 transition-all duration-200 bg-warm-200/60 dark:bg-white/[0.08] text-warm-500 dark:text-warm-400 group-hover:bg-primary-100 dark:group-hover:bg-primary-950/40 group-hover:text-primary-600 dark:group-hover:text-primary-400 group-hover:scale-105">
                          {i + 1}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-warm-700 dark:text-warm-300 line-clamp-2 leading-relaxed break-all">
                            {source}
                          </p>
                          <div className="flex items-center gap-2 mt-2 flex-wrap">
                            <Globe className="w-3 h-3 text-warm-300 dark:text-warm-600 shrink-0" />
                            <span className="text-[10px] text-warm-400 font-mono truncate">{domain}</span>
                            {/* DOI Badge */}
                            {doi && (
                              <a href={`https://doi.org/${doi}`} target="_blank" rel="noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-100/80 dark:bg-emerald-950/30 text-[9px] text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200/80 dark:hover:bg-emerald-900/30 transition-colors shrink-0">
                                <Unlink className="w-2 h-2" />DOI
                              </a>
                            )}
                            {isArxiv && !doi && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-warm-100/60 dark:bg-white/[0.06] text-warm-400 dark:text-warm-500 shrink-0">arXiv</span>
                            )}
                            <ExternalLink className="w-3 h-3 text-warm-300 dark:text-warm-600 opacity-0 group-hover:opacity-100 transition-all duration-200 ml-auto group-hover:text-primary-500 shrink-0" />
                          </div>
                        </div>
                      </div>
                      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-primary-500/0 via-primary-500/0 group-hover:via-primary-500/30 to-primary-500/0 transition-all duration-300" />
                    </div>
                  )
                })}
                {sources.length === 0 && (
                  <div className="text-center py-16 px-4">
                    <Quote className="w-8 h-8 text-warm-200 dark:text-warm-700 mx-auto mb-3" />
                    <p className="text-sm text-warm-400">No references available</p>
                    <p className="text-[11px] text-warm-500 mt-1">Sources will appear here once the research is complete</p>
                  </div>
                )}
              </div>

              {sources.length > 0 && (
                <div className="flex items-center gap-2 px-1 pt-2 border-t border-warm-200/30 dark:border-white/[0.04]">
                  <span className="text-[10px] text-warm-400">{sources.length} source{sources.length !== 1 ? 's' : ''} — click to open</span>
                </div>
              )}

              {/* Media Gallery */}
              <ErrorBoundary>
                <ImageGallery images={data.images || []} graphs={data.graphs || []} topic={data.topic || ''} />
              </ErrorBoundary>
            </div>
          </div>
          <div className="h-16 sm:h-20" />
        </div>
      </div>

      {/* Back to top */}
      <AnimatePresence>
        {showBackToTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            onClick={scrollToTop}
            className="fixed bottom-8 right-8 z-50 w-11 h-11 rounded-2xl bg-primary-500 text-white shadow-lg shadow-primary-500/30 flex items-center justify-center hover:bg-primary-600 active:scale-90 transition-all duration-200 ring-1 ring-white/10">
            <ArrowUp className="w-[18px] h-[18px]" />
          </motion.button>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
