import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import {
  Send, Bot, User, Loader2, AlertCircle, MessageSquare,
  Copy, Check, ExternalLink, Sparkles,
  RefreshCw, Trash2,
} from 'lucide-react'
import type { ChatMessage } from '../types'
import { chatFollowup } from '../lib/api'

interface Props {
  report: string
  sources: string[]
  provider?: string
  model?: string
}

/* ─── Helpers ─── */

function formatRelativeTime(ts: number): string {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function extractDomain(url: string): string {
  try { return new URL(url).hostname.replace('www.', '') }
  catch { return url }
}

/* ─── Suggested Questions ─── */

const SUGGESTED_QUESTIONS = [
  'Summarize the key findings',
  'What are the limitations?',
  'What are the main conclusions?',
]

/* ─── Copy Button ─── */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [text])

  return (
    <button
      onClick={handleCopy}
      className="opacity-0 group-hover/message:opacity-100 transition-all duration-200 p-1 rounded-md text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-warm-200/50 dark:hover:bg-white/[0.06]"
      title="Copy message"
    >
      {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
    </button>
  )
}

/* ─── Source Citation Badge ─── */

function SourceBadge({ index, sources }: { index: number; sources: string[] }) {
  const source = sources[index - 1]
  if (!source) return <span className="text-primary-600 dark:text-primary-400 font-medium">[S{index}]</span>

  return (
    <a
      href={source}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary-50/80 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 hover:bg-primary-100/80 dark:hover:bg-primary-900/30 transition-colors no-underline"
      title={`Open source ${index}: ${extractDomain(source)}`}
    >
      S{index}
      <ExternalLink className="w-2 h-2 opacity-60" />
    </a>
  )
}

/* ─── Render message content with source badges ─── */

function MessageContent({ content, sources }: { content: string; sources: string[] }) {
  // Render markdown with linked source citations
  const processed = useMemo(() => {
    // Replace [S#] references with badges
    return content.replace(/\[S(\d+)\]/g, (_, num) => {
      const i = parseInt(num, 10)
      const source = sources[i - 1]
      if (!source) return `[S${i}]`
      // Return a placeholder that ReactMarkdown won't touch, then replace in children
      return `[S${i}](${source})`
    })
  }, [content, sources])

  return (
    <div className="prose-warn text-xs leading-relaxed [&_p]:my-1 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5 [&_code]:text-[10px] [&_code]:bg-warm-100 dark:[&_code]:bg-white/[0.08] [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-warm-100 dark:[&_pre]:bg-white/[0.06] [&_pre]:p-2.5 [&_pre]:rounded-lg [&_pre]:my-2 [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:text-[10px] [&_blockquote]:border-l-2 [&_blockquote]:border-warm-300 dark:[&_blockquote]:border-warm-600 [&_blockquote]:pl-3 [&_blockquote]:my-1 [&_blockquote]:text-warm-500 dark:[&_blockquote]:text-warm-400 [&_blockquote]:italic [&_h1]:text-sm [&_h1]:font-bold [&_h2]:text-xs [&_h2]:font-semibold [&_h3]:text-xs [&_h3]:font-semibold [&_strong]:font-semibold [&_a]:text-primary-600 dark:[&_a]:text-primary-400 [&_a]:underline [&_a]:underline-offset-2 [&_a]:decoration-primary-300/30 dark:[&_a]:decoration-primary-700/30 [&_a]:hover:decoration-primary-500 [&_table]:w-full [&_table]:text-[10px] [&_th]:bg-warm-100 dark:[&_th]:bg-white/[0.06] [&_th]:px-2 [&_th]:py-1 [&_th]:font-medium [&_td]:px-2 [&_td]:py-1 [&_td]:border-t [&_td]:border-warm-200/40 dark:[&_td]:border-white/[0.06] [&_hr]:my-3 [&_hr]:border-warm-200/40 dark:[&_hr]:border-white/[0.06]"
    >
      <ReactMarkdown
        components={{
          a: ({ href, children, ...props }) => {
            // Check if this is a source citation link ([S#](url))
            const childText = String(children)
            const sMatch = childText.match(/^S(\d+)$/)
            if (sMatch && href) {
              const i = parseInt(sMatch[1], 10)
              return (
                <a href={href} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary-50/80 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 hover:bg-primary-100/80 dark:hover:bg-primary-900/30 transition-colors no-underline"
                  title={`Open source ${i}: ${extractDomain(href)}`}
                  {...props}
                >
                  S{i}
                  <ExternalLink className="w-2 h-2 opacity-60" />
                </a>
              )
            }
            return (
              <a href={href} target="_blank" rel="noreferrer" className="text-primary-600 dark:text-primary-400 underline underline-offset-2 decoration-primary-300/30 dark:decoration-primary-700/30 hover:decoration-primary-500 transition-colors" {...props}>
                {children}
                <ExternalLink className="w-2.5 h-2.5 inline-block ml-0.5 opacity-60" />
              </a>
            )
          },
          code: ({ className, children, ...props }) => {
            const isInline = !className
            if (isInline) {
              return <code className="text-[10px] bg-warm-100 dark:bg-white/[0.08] px-1 py-0.5 rounded font-mono" {...props}>{children}</code>
            }
            return (
              <div className="relative group/code my-2">
                <div className="absolute top-2 right-2 opacity-0 group-hover/code:opacity-100 transition-opacity">
                  <button
                    onClick={() => navigator.clipboard.writeText(String(children).replace(/\n$/, ''))}
                    className="text-[9px] text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 bg-black/20 dark:bg-white/10 px-1.5 py-0.5 rounded font-mono transition-colors"
                  >
                    copy
                  </button>
                </div>
                <pre className="bg-warm-100 dark:bg-white/[0.06] p-2.5 rounded-lg overflow-x-auto">
                  <code className="text-[10px] font-mono leading-relaxed" {...props}>{children}</code>
                </pre>
              </div>
            )
          },
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  )
}

/* ─── Message Bubble ─── */

function MessageBubble({ msg, sources }: { msg: ChatMessage; sources: string[] }) {
  const isUser = msg.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      className={`group/message flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`shrink-0 w-7 h-7 rounded-xl flex items-center justify-center ring-1 transition-colors ${
        isUser
          ? 'bg-primary-100 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 ring-primary-200/50 dark:ring-primary-800/30'
          : 'bg-warm-100 dark:bg-white/[0.06] text-warm-500 dark:text-warm-400 ring-warm-200/30 dark:ring-white/[0.06]'
      }`}>
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Bubble */}
      <div className={`group relative max-w-[85%] min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-2.5 shadow-sm ${
          isUser
            ? 'bg-primary-500 text-white rounded-tr-md'
            : 'bg-warm-100/80 dark:bg-white/[0.06] text-warm-700 dark:text-warm-300 rounded-tl-md border border-warm-200/30 dark:border-white/[0.04]'
        }`}>
          {isUser ? (
            <p className="text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <MessageContent content={msg.content} sources={sources} />
          )}
        </div>

        {/* Footer: timestamp + actions */}
        <div className={`flex items-center gap-1.5 mt-1 px-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="text-[9px] text-warm-400/60 dark:text-warm-500/60 font-medium">
            {formatRelativeTime(msg.timestamp)}
          </span>
          {!isUser && (
            <CopyButton text={msg.content} />
          )}
        </div>
      </div>
    </motion.div>
  )
}

/* ─── Typing Indicator ─── */

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-3"
    >
      <div className="shrink-0 w-7 h-7 rounded-xl bg-warm-100 dark:bg-white/[0.06] flex items-center justify-center ring-1 ring-warm-200/30 dark:ring-white/[0.06]">
        <Bot className="w-3.5 h-3.5 text-warm-500 dark:text-warm-400" />
      </div>
      <div className="bg-warm-100/80 dark:bg-white/[0.06] rounded-2xl rounded-tl-md px-4 py-3 border border-warm-200/30 dark:border-white/[0.04]">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </motion.div>
  )
}

/* ─── Suggested Question Chips ─── */

function SuggestedQuestions({ onSelect, disabled }: { onSelect: (q: string) => void; disabled: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
      <span className="text-[10px] text-warm-400 font-medium flex items-center gap-1">
        <Sparkles className="w-2.5 h-2.5" />
        Try:
      </span>
      {SUGGESTED_QUESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          disabled={disabled}
          className="px-2.5 py-1 text-[10px] rounded-full bg-warm-100/60 dark:bg-white/[0.05] text-warm-500 dark:text-warm-400 hover:bg-primary-50 dark:hover:bg-primary-950/20 hover:text-primary-600 dark:hover:text-primary-400 hover:border-primary-300/30 dark:hover:border-primary-700/30 border border-warm-200/30 dark:border-white/[0.06] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {q}
        </button>
      ))}
    </div>
  )
}

/* ─── Main Component ─── */

export function ChatPanel({ report, sources, provider, model }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const isNearBottomRef = useRef(true)
  const [showSuggestions, setShowSuggestions] = useState(true)

  // Track whether user is near the bottom of the scroll container
  const updateIsNearBottom = useCallback(() => {
    const el = messagesContainerRef.current
    if (!el) return
    const threshold = 80 // px from bottom
    isNearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < threshold
  }, [])

  // Only auto-scroll if user is near the bottom
  const scrollToBottom = useCallback((smooth: boolean = true) => {
    if (!isNearBottomRef.current) return
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
  }, [])

  // Auto-scroll on new messages/streaming tokens only if user was near bottom
  useEffect(() => {
    scrollToBottom(true)
  }, [messages, scrollToBottom])

  // Also scroll when loading state changes (e.g. stream starts)
  useEffect(() => {
    if (isLoading) scrollToBottom(false)
  }, [isLoading, scrollToBottom])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px'
    }
  }, [input])

  const addMessage = useCallback((content: string, role: 'user' | 'assistant') => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      role,
      content,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, msg])
    return msg
  }, [])

  const handleSend = useCallback(async (text?: string) => {
    const question = (text || input).trim()
    if (!question || isLoading) return

    addMessage(question, 'user')
    setInput('')
    setIsLoading(true)
    setError(null)
    setShowSuggestions(false)

    try {
      const answer = await chatFollowup(question, report, sources, provider, model)
      addMessage(answer, 'assistant')
      setShowSuggestions(true)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to get response'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, report, sources, provider, model, addMessage])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleClear = useCallback(() => {
    setMessages([])
    setError(null)
    setShowSuggestions(true)
  }, [])

  const handleRetry = useCallback(() => {
    setError(null)
    // Re-send the last user message
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
    if (lastUserMsg) {
      setIsLoading(true)
      setShowSuggestions(false)
      chatFollowup(lastUserMsg.content, report, sources, provider, model)
        .then(answer => {
          addMessage(answer, 'assistant')
          setShowSuggestions(true)
        })
        .catch(err => {
          setError(err instanceof Error ? err.message : 'Failed to get response')
        })
        .finally(() => setIsLoading(false))
    }
  }, [messages, report, sources, provider, model, addMessage])

  return (
    <div className="rounded-2xl border border-warm-200/40 dark:border-white/[0.06] overflow-hidden bg-white/50 dark:bg-white/[0.02] shadow-sm">
      {/* ── Header ── */}
      <div className="flex items-center justify-between gap-2 px-4 py-3 bg-warm-100/60 dark:bg-white/[0.03] border-b border-warm-200/40 dark:border-white/[0.06]">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-950/30 dark:to-primary-900/20 flex items-center justify-center ring-1 ring-primary-200/30 dark:ring-primary-800/20 shrink-0">
            <MessageSquare className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-warm-800 dark:text-warm-200">Ask Follow-up</h3>
            <p className="text-[10px] text-warm-400 truncate">
              {provider && provider !== 'ollama' ? `${provider}${model ? ` · ${model}` : ''}` : 'Ask about this research'}
            </p>
          </div>
        </div>

        {/* Clear button */}
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="shrink-0 p-1.5 rounded-lg text-warm-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50/50 dark:hover:bg-red-950/30 transition-all duration-200"
            title="Clear conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* ── Messages Area ── */}
      <div
        ref={messagesContainerRef}
        onScroll={updateIsNearBottom}
        className="min-h-[240px] max-h-[420px] overflow-y-auto scroll-smooth"
        style={{ scrollbarWidth: 'thin' }}>
        {messages.length === 0 && !isLoading ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-950/30 dark:to-primary-900/20 flex items-center justify-center ring-1 ring-primary-200/30 dark:ring-primary-800/20 mb-4">
              <MessageSquare className="w-6 h-6 text-primary-500 dark:text-primary-400" />
            </div>
            <p className="text-sm font-semibold text-warm-700 dark:text-warm-300 mb-1">
              Ask about this research
            </p>
            <p className="text-[11px] text-warm-400 max-w-[240px] leading-relaxed">
              Get clarifications, summaries, or dive deeper into any aspect of the report.
            </p>

            {showSuggestions && (
              <div className="mt-5 flex flex-wrap justify-center gap-1.5 max-w-[280px]">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-3 py-1.5 text-[11px] rounded-full bg-warm-100/60 dark:bg-white/[0.05] text-warm-500 dark:text-warm-400 hover:bg-primary-50 dark:hover:bg-primary-950/20 hover:text-primary-600 dark:hover:text-primary-400 hover:border-primary-300/30 dark:hover:border-primary-700/30 border border-warm-200/30 dark:border-white/[0.06] transition-all duration-200"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 space-y-4">
            <AnimatePresence mode="popLayout">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} sources={sources} />
              ))}
            </AnimatePresence>

            <AnimatePresence mode="wait">
              {isLoading && <TypingIndicator />}
            </AnimatePresence>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="flex items-start gap-2.5 p-3 rounded-xl bg-red-50/80 dark:bg-red-950/20 border border-red-200/50 dark:border-red-900/50"
                >
                  <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-red-600 dark:text-red-400 leading-relaxed">{error}</p>
                    <button
                      onClick={handleRetry}
                      className="mt-1.5 inline-flex items-center gap-1 text-[10px] font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                    >
                      <RefreshCw className="w-2.5 h-2.5" />
                      Try again
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Suggested questions (after responses) ── */}
      <AnimatePresence>
        {showSuggestions && messages.length > 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <SuggestedQuestions onSelect={handleSend} disabled={isLoading} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Input Area ── */}
      <div className="border-t border-warm-200/40 dark:border-white/[0.06] p-3">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            rows={1}
            className="flex-1 min-w-0 px-3 py-2.5 text-xs rounded-xl border border-warm-200/50 dark:border-white/[0.08] bg-warm-50/60 dark:bg-white/[0.04] text-warm-700 dark:text-warm-300 placeholder:text-warm-400 focus:outline-none focus:ring-1 focus:ring-primary-500/30 resize-none leading-relaxed transition-all duration-200"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="px-3 py-2.5 rounded-xl bg-primary-500 text-white hover:bg-primary-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 active:scale-95 shrink-0 shadow-sm shadow-primary-500/20 hover:shadow-md hover:shadow-primary-500/30"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-[9px] text-warm-400/60 mt-1.5 px-1">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
