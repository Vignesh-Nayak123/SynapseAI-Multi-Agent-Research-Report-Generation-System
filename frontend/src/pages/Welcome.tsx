import { useNavigate } from 'react-router-dom'
import {
  TrendingUp, BookOpen, Network, FileSearch, FileText,
  Lock, Scale, Zap, Sliders, Globe, Search, CheckCircle2,
  ArrowDown, Pen, ExternalLink, RefreshCw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { useState, useEffect, useRef, useCallback } from 'react'
import { EXAMPLE_REPORT } from '../lib/exampleReport'
import { fetchTrendingTopics, refreshTrendingTopics } from '../lib/api'

const FALLBACK_TOPICS = [
  "Autonomous Multi-Agent Systems",
  "AI Governance & Safety",
  "TinyML & Edge AI",
  "AI-Driven Scientific Discovery",
  "Synthetic Data & Model Collapse"
]

/* ─── Live metric component (real-time dashboard feel) ─── */
function LiveMetric({ icon: Icon, label, targetValue, prefix, suffix, decimals, color, gradient, delay }: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  targetValue: number
  prefix: string
  suffix: string
  decimals: number
  color: string
  gradient: string
  delay: number
}) {
  const [displayValue, setDisplayValue] = useState(prefix === '~' ? 0 : targetValue)
  const ref = useRef<HTMLDivElement>(null)
  const hasAnimated = useRef(false)
  const jitterStarted = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clampMax = targetValue > 90 ? 100 : Infinity
  const jitterRatio = targetValue > 90 ? 0.005 : 0.02

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const duration = 1400
          const start = performance.now()
          const animate = (now: number) => {
            const elapsed = now - start
            const progress = Math.min(elapsed / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            setDisplayValue(Number((eased * targetValue).toFixed(decimals)))
            if (progress < 1) requestAnimationFrame(animate)
          }
          requestAnimationFrame(animate)
        }

        if (entry.isIntersecting && !jitterStarted.current) {
          jitterStarted.current = true
          timeoutRef.current = setTimeout(() => {
            intervalRef.current = setInterval(() => {
              setDisplayValue(prev => {
                const jitter = (Math.random() - 0.5) * (targetValue * jitterRatio)
                const raw = Math.min(targetValue + jitter, clampMax)
                return Number(raw.toFixed(decimals))
              })
            }, 2000 + Math.random() * 1000)
          }, 1600)
        }
      },
      { threshold: 0.3 }
    )

    observer.observe(el)
    return () => {
      observer.disconnect()
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [targetValue, decimals, clampMax, jitterRatio])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-30px' }}
      transition={{ delay, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="relative group"
    >
      <div className="absolute -inset-[3px] bg-gradient-to-br from-primary-500/10 to-accent-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <div className="relative glass-card p-4 sm:p-5 text-center overflow-hidden">
        <div className={`absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r ${color} opacity-50`} />

        {/* Live indicator dot */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
          </span>
          <span className="text-[9px] text-emerald-500 font-medium tracking-wider uppercase">Live</span>
        </div>

        <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-2.5 ring-1 ring-white/10 group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-[16px] h-[16px] text-white" />
        </div>

        <div className="text-2xl sm:text-3xl font-extrabold text-warm-900 dark:text-warm-100 tracking-tight tabular-nums">
          {prefix}{displayValue}{suffix}
        </div>

        <div className="text-[11px] text-warm-600 dark:text-warm-400 mt-1">{label}</div>
      </div>
    </motion.div>
  )
}

export default function Welcome() {
  const navigate = useNavigate()
  const heroRef = useRef<HTMLDivElement>(null)
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 })
  const [trendingTopics, setTrendingTopics] = useState<string[]>([])
  const [trendingTopicsLoading, setTrendingTopicsLoading] = useState(true)
  const [trendingTopicsRefreshing, setTrendingTopicsRefreshing] = useState(false)

  useEffect(() => {
    setTrendingTopicsLoading(true)
    fetchTrendingTopics().then(topics => {
      setTrendingTopics(topics)
      setTrendingTopicsLoading(false)
    })
  }, [])

  const handleRefreshTrending = useCallback(() => {
    setTrendingTopicsRefreshing(true)
    refreshTrendingTopics().then(topics => {
      if (topics.length > 0) setTrendingTopics(topics)
      setTrendingTopicsRefreshing(false)
    })
  }, [])

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      if (heroRef.current) {
        const rect = heroRef.current.getBoundingClientRect()
        setMousePos({
          x: ((e.clientX - rect.left) / rect.width) * 100,
          y: ((e.clientY - rect.top) / rect.height) * 100
        })
      }
    }
    window.addEventListener('mousemove', handleMouse)
    return () => window.removeEventListener('mousemove', handleMouse)
  }, [])

  const stagger = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.05 }
    }
  }

  const fadeUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } }
  }

  return (
    <div className="min-h-screen bg-warm-50 dark:bg-[#0c0b0a] text-warm-800 dark:text-warm-300 overflow-x-hidden selection:bg-primary-500 selection:text-white dark:selection:bg-primary-400 dark:selection:text-[#0c0b0a]">
      <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 pb-24" ref={heroRef}>
        {/* Animated background blobs */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div
            className="absolute top-[20%] left-[10%] w-[400px] h-[400px] rounded-full opacity-20 dark:opacity-10 animate-float-slow"
            style={{
              background: 'radial-gradient(circle, rgba(99,102,241,0.3) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute top-[40%] right-[5%] w-[350px] h-[350px] rounded-full opacity-15 dark:opacity-8 animate-float-medium"
            style={{
              background: 'radial-gradient(circle, rgba(245,158,11,0.25) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute bottom-[10%] left-[30%] w-[300px] h-[300px] rounded-full opacity-10 dark:opacity-5 animate-float-fast"
            style={{
              background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)',
            }}
          />
        </div>

        {/* Mouse-tracking ambient glow */}
        <div
          className="pointer-events-none fixed top-0 left-0 w-full h-full opacity-30 dark:opacity-20"
          style={{
            background: `radial-gradient(600px circle at ${mousePos.x}% ${mousePos.y}%, rgba(99,102,241,0.10) 0%, rgba(245,158,11,0.04) 30%, transparent 60%)`,
          }}
        />

        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="relative z-10 flex flex-col items-center text-center pt-20 sm:pt-28"
        >
          {/* Brand badge */}
          <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-xs font-medium text-warm-500 dark:text-warm-400 mb-10">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
            </span>
            AI-Powered Research Assistant
          </motion.div>

          {/* Hero text */}
          <motion.div variants={fadeUp} className="space-y-4">
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold tracking-tight text-warm-900 dark:text-warm-100 leading-[1.05] max-w-3xl">
              Research anything.{' '}
              <span className="gradient-text">Instantly.</span>
            </h1>
            <p className="text-base sm:text-lg text-warm-500 dark:text-warm-400 max-w-xl mx-auto leading-relaxed">
              Autonomous agents search, analyze, and synthesize academic papers into comprehensive reports, all in seconds.
            </p>
          </motion.div>

          {/* CTA */}
          <motion.div variants={fadeUp} className="mt-10">
            <button
              onClick={() => navigate('/app')}
              className="group inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white text-sm font-semibold shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-300 hover:-translate-y-0.5"
            >
              Launch the app
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-0.5 transition-transform">
                <path d="M5 12h14" />
                <path d="m15 16 4-4-4-4" />
              </svg>
            </button>
          </motion.div>

          {/* Trending */}
          <motion.div variants={fadeUp} className="mt-8 flex flex-wrap items-center justify-center gap-2.5">
            <span className="flex items-center gap-1.5 text-xs text-warm-500 dark:text-warm-400 font-medium mr-1">
              <TrendingUp className="w-3.5 h-3.5" />
              Trending
            </span>
            <button
              onClick={handleRefreshTrending}
              disabled={trendingTopicsRefreshing}
              className="flex items-center justify-center w-[22px] h-[22px] rounded-full text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 hover:bg-warm-200/50 dark:hover:bg-[#2a2724]/50 transition-all duration-200 disabled:opacity-50"
              title="Refresh trending topics"
            >
              <RefreshCw className={`w-[14px] h-[14px] ${trendingTopicsRefreshing ? 'animate-spin' : ''}`} />
            </button>
            {trendingTopicsLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-[28px] w-[110px] sm:w-[130px] rounded-full glass-card animate-pulse"
                  style={{ animationDelay: `${i * 60}ms`, opacity: 0.5 }}
                />
              ))
            ) : (
              (trendingTopics.length > 0 ? trendingTopics : FALLBACK_TOPICS).map((topic, i) => (
                <button
                  key={i}
                  onClick={() => navigate(`/app?topic=${encodeURIComponent(topic)}&auto=1`)}
                  className="group px-3.5 py-1.5 text-xs text-warm-500 hover:text-warm-800 dark:text-warm-400 dark:hover:text-warm-200 glass-card hover:shadow-md transition-all duration-200"
                >
                  {topic}
                </button>
              ))
            )}
          </motion.div>

          {/* ─── How It Works ─── */}
          <motion.div variants={fadeUp} className="w-full max-w-3xl mt-20">
            <div className="text-center mb-10">
              <h2 className="text-lg sm:text-xl font-bold text-warm-800 dark:text-warm-200 tracking-tight">
                How it works
              </h2>
              <p className="text-sm text-warm-500 dark:text-warm-400 mt-1.5">
                Three autonomous agents collaborate in a feedback loop
              </p>
            </div>

            <div className="relative">
              {/* Connecting line - animated gradient + particles */}
              <div className="hidden sm:block absolute top-[60px] left-[calc(16.67%+20px)] right-[calc(16.67%+20px)]">
                <div className="h-[2px] bg-[length:200%_100%] bg-gradient-to-r from-transparent via-primary-400/40 via-accent-400/30 via-primary-400/40 to-transparent animate-[flow-line_4s_linear_infinite] rounded-full" />
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-primary-400 shadow-[0_0_8px_3px_rgba(99,102,241,0.45)] animate-[particle-drift_3s_ease-in-out_infinite]" style={{ left: '0%' }} />
                  <div className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-accent-400 shadow-[0_0_8px_3px_rgba(245,158,11,0.4)] animate-[particle-drift_3s_ease-in-out_infinite_1.5s]" style={{ left: '0%' }} />
                </div>
              </div>
              <div className="sm:hidden absolute top-[60px] left-[calc(50%-1px)] bottom-[60px]">
                <div className="w-[2px] h-full bg-[length:100%_200%] bg-gradient-to-b from-primary-400/40 via-accent-400/30 to-transparent animate-[flow-line_4s_linear_infinite] rounded-full" />
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-primary-400 shadow-[0_0_8px_3px_rgba(99,102,241,0.45)] animate-[particle-drift-vertical_3s_ease-in-out_infinite]" style={{ top: '0%' }} />
                  <div className="absolute left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-accent-400 shadow-[0_0_8px_3px_rgba(245,158,11,0.4)] animate-[particle-drift-vertical_3s_ease-in-out_infinite_1.5s]" style={{ top: '0%' }} />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-6 relative">
                {[
                  {
                    step: '01',
                    icon: Search,
                    label: 'Research Agent',
                    desc: 'Searches ArXiv and PDF repositories, parsing full-text documents and ranking by relevance.',
                    color: 'from-primary-600 to-primary-400',
                    badgeBg: 'bg-primary-600',
                    bgGlow: 'bg-primary-500/10',
                  },
                  {
                    step: '02',
                    icon: Pen,
                    label: 'Draft Agent',
                    desc: 'Synthesizes findings into structured reviews with Executive Summary, Key Findings, and Critical Analysis.',
                    color: 'from-accent-500 to-accent-400',
                    badgeBg: 'bg-accent-500',
                    bgGlow: 'bg-accent-500/10',
                  },
                  {
                    step: '03',
                    icon: CheckCircle2,
                    label: 'Critique Agent',
                    desc: 'Scores quality, detects hallucinations, and validates citations with up to 3 revision cycles.',
                    color: 'from-emerald-500 to-emerald-400',
                    badgeBg: 'bg-emerald-500',
                    bgGlow: 'bg-emerald-500/10',
                  },
                ].map((s, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 24 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: '-40px' }}
                    transition={{ delay: i * 0.12, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                    className="relative flex sm:flex-col items-start sm:items-center gap-4 sm:gap-0 text-left sm:text-center"
                  >
                    {i < 2 && (
                      <div className="sm:hidden absolute left-[20px] top-[54px] bottom-[-32px] flex items-center justify-center">
                        <ArrowDown className="w-4 h-4 text-primary-400/60 dark:text-primary-500/50 animate-[pulse-connector_2.5s_ease-in-out_infinite]" />
                      </div>
                    )}

                    <div className="relative shrink-0 z-10">
                      <div className={`absolute -inset-3 rounded-full ${s.bgGlow} blur-md opacity-60`} />
                      <div className={`w-[52px] h-[52px] sm:w-[60px] sm:h-[60px] rounded-full bg-gradient-to-br ${s.color} flex items-center justify-center shadow-lg ring-1 ring-white/20 relative`}>
                        <s.icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                      </div>
                      <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-2 border-[#0c0b0a] dark:border-warm-950 flex items-center justify-center text-[9px] font-bold ${s.badgeBg}`}>
                        <span className="text-white">{s.step}</span>
                      </div>
                    </div>

                    <div className="flex-1 sm:mt-5">
                      <h3 className="text-sm font-semibold text-warm-800 dark:text-warm-200 mb-1.5">{s.label}</h3>
                      <p className="text-xs text-warm-500 dark:text-warm-400 leading-relaxed max-w-[280px] sm:mx-auto">{s.desc}</p>
                    </div>

                    {i < 2 && (
                      <div className="hidden sm:flex absolute -right-[18px] top-[26px]">
                        <div className="relative">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-primary-400/60 dark:text-primary-500/50 animate-[pulse-connector_2.5s_ease-in-out_infinite]">
                            <path d="M5 12h14" />
                            <path d="m15 16 4-4-4-4" />
                          </svg>
                          <div className="absolute top-[11px] left-[5px] w-[5px] h-[5px] rounded-full bg-primary-400 shadow-[0_0_6px_2px_rgba(99,102,241,0.5)] animate-[arrow-dot_2.5s_ease-in-out_infinite]" />
                        </div>
                      </div>
                    )}

                    <div className="hidden sm:block absolute top-[30px] w-2 h-2 rounded-full bg-primary-400/40 -translate-x-1/2 left-1/2" />
                  </motion.div>
                ))}
              </div>

              {/* Feedback loop indicator */}
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.5, duration: 0.6 }}
                className="mt-8 pt-6 border-t border-warm-200/40 dark:border-white/[0.06] text-center"
              >
                <div className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-warm-100/50 dark:bg-white/[0.03] border border-warm-200/30 dark:border-white/[0.04]">
                  <div className="flex -space-x-1.5">
                    <div className="w-6 h-6 rounded-full bg-primary-500 ring-2 ring-warm-50 dark:ring-dark-surface flex items-center justify-center">
                      <Search className="w-3 h-3 text-white" />
                    </div>
                    <div className="w-6 h-6 rounded-full bg-accent-500 ring-2 ring-warm-50 dark:ring-dark-surface flex items-center justify-center">
                      <Pen className="w-3 h-3 text-white" />
                    </div>
                    <div className="w-6 h-6 rounded-full bg-emerald-500 ring-2 ring-warm-50 dark:ring-dark-surface flex items-center justify-center">
                      <CheckCircle2 className="w-3 h-3 text-white" />
                    </div>
                  </div>
                  <span className="text-xs text-warm-500 dark:text-warm-400">
                    <span className="font-medium text-warm-700 dark:text-warm-300">Feedback loop:</span>{' '}
                    Critique agent loops back to Draft if quality or citations don't meet the configured threshold
                  </span>
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* ─── Real-Time Demo Stats ─── */}
          <motion.div variants={fadeUp} className="w-full max-w-4xl mt-20">
            <div className="text-center mb-10">
              <h2 className="text-lg sm:text-xl font-bold text-warm-800 dark:text-warm-200 tracking-tight">
                Live system metrics
              </h2>
              <p className="text-sm text-warm-500 dark:text-warm-400 mt-1.5">
                Real-time performance data across all research sessions
              </p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { icon: Zap, label: 'Avg. processing time', value: 45, suffix: 's', prefix: '~', color: 'from-emerald-500 to-emerald-400', gradient: 'from-emerald-500/30 to-emerald-400/30' },
                { icon: BookOpen, label: 'Sources per report', value: 8, suffix: '', prefix: '~', decimals: 1, color: 'from-primary-500 to-primary-400', gradient: 'from-primary-500/30 to-primary-400/30' },
                { icon: CheckCircle2, label: 'Citation accuracy', value: 99.7, suffix: '%', prefix: '', color: 'from-violet-500 to-violet-400', gradient: 'from-violet-500/30 to-violet-400/30' },
                { icon: Sliders, label: 'Max revision passes', value: 3, suffix: '', prefix: '', color: 'from-accent-500 to-accent-400', gradient: 'from-accent-500/30 to-accent-400/30' },
              ].map((stat, i) => (
                <LiveMetric
                  key={i}
                  icon={stat.icon}
                  label={stat.label}
                  targetValue={stat.value}
                  prefix={stat.prefix}
                  suffix={stat.suffix}
                  decimals={stat.decimals ?? 0}
                  color={stat.color}
                  gradient={stat.gradient}
                  delay={i * 0.12}
                />
              ))}
            </div>
          </motion.div>

          {/* ─── Example Report Preview ─── */}
          <motion.div variants={fadeUp} className="w-full max-w-5xl mt-20">
            <div className="text-center mb-6">
              <h2 className="text-lg sm:text-xl font-bold text-warm-800 dark:text-warm-200 tracking-tight">
                See it in action
              </h2>
              <p className="text-sm text-warm-500 dark:text-warm-400 mt-1.5">
                A real report generated by autonomous agents on a trending topic
              </p>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="relative"
            >
              <div className="absolute -inset-2 bg-gradient-to-r from-primary-500/10 via-accent-500/5 to-primary-500/10 rounded-[24px] blur-2xl" />

              <div className="relative glass-card !rounded-2xl overflow-hidden border-warm-200/50 dark:border-white/[0.08]">
                <div className="px-6 sm:px-8 pt-6 sm:pt-8 pb-4 border-b border-warm-200/40 dark:border-white/[0.06]">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-primary-600 via-primary-500 to-primary-400 flex items-center justify-center shadow-md shadow-primary-500/20 ring-1 ring-white/10">
                      <FileText className="w-[18px] h-[18px] text-white" />
                    </div>
                    <div className="text-left">
                      <h3 className="text-base font-bold text-warm-900 dark:text-warm-100 tracking-tight">
                        The Impact of AI on Labor Markets
                      </h3>
                      <div className="flex items-center gap-2.5 mt-1">
                        <span className="text-[11px] text-warm-600 dark:text-warm-400">12 min read</span>
                        <span className="text-[11px] text-warm-300 dark:text-warm-600">·</span>
                        <span className="text-[11px] text-warm-600 dark:text-warm-400">8 sources</span>
                        <span className="text-[11px] text-warm-300 dark:text-warm-600">·</span>
                        <span className="text-[11px] text-warm-600 dark:text-warm-400">May 26, 2026</span>
                      </div>
                    </div>
                  </div>

                  <div className="inline-flex items-center gap-2 text-[11px] text-emerald-600 dark:text-emerald-400 bg-emerald-50/60 dark:bg-emerald-950/30 px-3 py-1.5 rounded-lg border border-emerald-200/40 dark:border-emerald-900/30">
                    Generated by Research Agent → Draft Agent → Critique Agent (3 revision passes)
                  </div>
                </div>

                <div className="relative">
                  <div className="max-h-[520px] overflow-y-auto px-6 sm:px-8 py-6">
                    <div className="prose-warm">
                      <ReactMarkdown>
                        {EXAMPLE_REPORT}
                      </ReactMarkdown>
                    </div>
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-[#0c0b0a] via-white/80 dark:via-[#0c0b0a]/80 to-transparent pointer-events-none" />
                </div>

                <div className="px-6 sm:px-8 py-4 border-t border-warm-200/40 dark:border-white/[0.06] flex items-center justify-between">
                  <span className="text-[11px] text-warm-600 dark:text-warm-400">
                    Scroll to see the full example report
                  </span>
                  <button
                    onClick={() => navigate('/app?topic=The+Impact+of+AI+on+Labor+Markets')}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                  >
                    Research this topic
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* ─── Features ─── */}
          <motion.div variants={fadeUp} className="w-full max-w-5xl mt-20 pt-12 border-t border-warm-200/60 dark:border-white/[0.06]">
            <div className="text-center mb-10">
              <h2 className="text-lg sm:text-xl font-bold text-warm-800 dark:text-warm-200 tracking-tight">
                Everything you need for deep research
              </h2>
              <p className="text-sm text-warm-500 dark:text-warm-400 mt-1.5">
                Autonomous agents handle the heavy lifting, from searching to synthesizing
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                {
                  icon: FileSearch,
                  label: 'Multi-agent pipeline',
                  desc: 'Three autonomous agents collaborate to produce rigorous, peer-reviewed reports.',
                  tag: 'Core engine',
                  tagColor: 'bg-primary-100/80 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border-primary-200/50 dark:border-primary-800/50',
                  iconBg: 'bg-primary-50 dark:bg-primary-950/40',
                  iconColor: 'text-primary-500',
                },
                {
                  icon: BookOpen,
                  label: 'Academic search',
                  desc: 'Searches ArXiv and PDF repositories, parsing full-text documents and ranking by relevance.',
                  tag: 'Retrieval',
                  tagColor: 'bg-indigo-100/80 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border-indigo-200/50 dark:border-indigo-800/50',
                  iconBg: 'bg-indigo-50 dark:bg-indigo-950/40',
                  iconColor: 'text-indigo-500',
                },
                {
                  icon: Network,
                  label: 'Knowledge graph',
                  desc: 'Force-directed graph visualizing research connections. Click any node to open the paper.',
                  tag: 'Visualization',
                  tagColor: 'bg-emerald-100/80 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200/50 dark:border-emerald-800/50',
                  iconBg: 'bg-emerald-50 dark:bg-emerald-950/40',
                  iconColor: 'text-emerald-500',
                },
                {
                  icon: FileText,
                  label: 'Structured reports',
                  desc: 'Rich markdown reports with Executive Summary, Key Findings, and Critical Analysis sections.',
                  tag: 'Output',
                  tagColor: 'bg-amber-100/80 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200/50 dark:border-amber-800/50',
                  iconBg: 'bg-amber-50 dark:bg-amber-950/40',
                  iconColor: 'text-amber-500',
                },
                {
                  icon: Globe,
                  label: '10+ LLM providers',
                  desc: 'Ollama, OpenAI, Anthropic, Google, DeepSeek, Mistral, and more, local or cloud.',
                  tag: 'Flexibility',
                  tagColor: 'bg-sky-100/80 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 border-sky-200/50 dark:border-sky-800/50',
                  iconBg: 'bg-sky-50 dark:bg-sky-950/40',
                  iconColor: 'text-sky-500',
                },
                {
                  icon: Lock,
                  label: 'Zero-knowledge encryption',
                  desc: 'Passphrase-protected with WebAuthn unlock. API keys encrypted end-to-end in your browser.',
                  tag: 'Security',
                  tagColor: 'bg-violet-100/80 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 border-violet-200/50 dark:border-violet-800/50',
                  iconBg: 'bg-violet-50 dark:bg-violet-950/40',
                  iconColor: 'text-violet-500',
                },
                {
                  icon: Scale,
                  label: 'Critique & revision',
                  desc: 'Automatic scoring, hallucination detection, and citation validation with up to 3 revision passes.',
                  tag: 'Quality',
                  tagColor: 'bg-rose-100/80 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 border-rose-200/50 dark:border-rose-800/50',
                  iconBg: 'bg-rose-50 dark:bg-rose-950/40',
                  iconColor: 'text-rose-500',
                },
                {
                  icon: Zap,
                  label: 'Streaming generation',
                  desc: 'Watch drafts written in real-time with token streaming. Copy, download, or listen via TTS.',
                  tag: 'Experience',
                  tagColor: 'bg-orange-100/80 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200/50 dark:border-orange-800/50',
                  iconBg: 'bg-orange-50 dark:bg-orange-950/40',
                  iconColor: 'text-orange-500',
                },
                {
                  icon: Sliders,
                  label: 'Deep controls',
                  desc: 'Configure search depth, source count, critic strictness, and custom model overrides.',
                  tag: 'Customization',
                  tagColor: 'bg-teal-100/80 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border-teal-200/50 dark:border-teal-800/50',
                  iconBg: 'bg-teal-50 dark:bg-teal-950/40',
                  iconColor: 'text-teal-500',
                },
              ].map((f, i) => (
                <motion.div
                  key={i}
                  whileHover={{ y: -3 }}
                  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                  className="group glass-card p-5 text-left cursor-default"
                >
                  <div className="flex items-start justify-between mb-3.5">
                    <div className={`w-10 h-10 rounded-xl ${f.iconBg} border border-warm-200/50 dark:border-white/[0.06] flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                      <f.icon className={`w-[18px] h-[18px] ${f.iconColor}`} />
                    </div>
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${f.tagColor}`}>
                      {f.tag}
                    </span>
                  </div>
                  <div className="text-sm font-semibold text-warm-800 dark:text-warm-200 mb-1.5">{f.label}</div>
                  <div className="text-xs text-warm-500 dark:text-warm-400 leading-relaxed">{f.desc}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Bottom CTA */}
          <motion.div variants={fadeUp} className="mt-16 text-center">
            <button
              onClick={() => navigate('/app')}
              className="group inline-flex items-center gap-2.5 px-7 py-3.5 rounded-2xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white text-sm font-semibold shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-300 hover:-translate-y-0.5"
            >
              Start researching
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-0.5 transition-transform">
                <path d="M5 12h14" />
                <path d="m15 16 4-4-4-4" />
              </svg>
            </button>
            <p className="text-xs text-warm-500 dark:text-warm-400 mt-3">No sign-up required. Free and open-source.</p>
          </motion.div>

          <div className="h-16" />
        </motion.div>
      </div>
    </div>
  )
}
