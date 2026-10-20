import { motion } from 'framer-motion'
import { CheckCircle2, Search, PenTool, Scale, XCircle, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'

const STEPS = [
  { id: 'research', label: "Searching databases", icon: Search, color: "text-primary-500", bg: "bg-primary-50 dark:bg-primary-950/40", agent: "Researcher", gradient: "from-primary-500 to-primary-400" },
  { id: 'draft', label: "Synthesizing report", icon: PenTool, color: "text-accent-500", bg: "bg-accent-50 dark:bg-accent-950/40", agent: "Writer", gradient: "from-accent-500 to-accent-400" },
  { id: 'critique', label: "Reviewing & refining", icon: Scale, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/40", agent: "Critic", gradient: "from-emerald-500 to-emerald-400" }
]

const LOG_MESSAGES: Record<string, string[]> = {
  research: ["Querying ArXiv...", "Filtering by relevance...", "Analyzing abstracts...", "Cross-referencing sources...", "Ranking papers..."],
  draft: ["Structuring arguments...", "Writing sections...", "Connecting concepts...", "Formatting citations...", "Refining language..."],
  critique: ["Checking logic...", "Verifying citations...", "Polishing output...", "Final review...", "Validating sources..."]
}

interface Props {
  onStop?: () => void
}

export function LoadingState({ onStop }: Props) {
  const [activeStepId, setActiveStepId] = useState('research')
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set())
  const [log, setLog] = useState<string>("")
  const [logIdx, setLogIdx] = useState(0)
  const [dots, setDots] = useState("")
  const [metrics, setMetrics] = useState({ cpu: 45, sources: 0 })

  // Step updates from backend
  useEffect(() => {
    const handleProgress = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail.status === 'running') {
        setActiveStepId(detail.step)
        setLogIdx(0)
      } else if (detail.status === 'completed') {
        setCompletedSteps(prev => new Set(prev).add(detail.step))
      }
    }
    window.addEventListener('research-progress', handleProgress)
    return () => window.removeEventListener('research-progress', handleProgress)
  }, [])

  // Animated dots
  useEffect(() => {
    const interval = setInterval(() => setDots(prev => prev.length >= 3 ? "" : prev + "."), 400)
    return () => clearInterval(interval)
  }, [])

  // Simulate logs and metrics
  useEffect(() => {
    const msgs = LOG_MESSAGES[activeStepId] || LOG_MESSAGES.research
    const interval = setInterval(() => {
      setLog(msgs[logIdx % msgs.length])
      setLogIdx(prev => prev + 1)
      setMetrics(prev => ({
        cpu: Math.min(90, Math.max(20, prev.cpu + (Math.random() * 10 - 5))),
        sources: activeStepId === 'research' ? prev.sources + 1 : prev.sources
      }))
    }, 2000)
    return () => clearInterval(interval)
  }, [activeStepId, logIdx])

  const activeStep = STEPS.find(s => s.id === activeStepId) || STEPS[0]

  return (
    <div className="py-8 space-y-6 max-w-2xl mx-auto">
      {/* Stop button */}
      {onStop && (
        <div className="flex justify-end">
          <button
            onClick={onStop}
            className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-400 transition-colors px-3 py-1.5 rounded-lg glass-card border-red-200/50 dark:border-red-900/50 hover:bg-red-50/60 dark:hover:bg-red-950/20 shadow-sm"
          >
            <XCircle className="w-3.5 h-3.5" />
            Stop
          </button>
        </div>
      )}

      {/* Active step card */}
      <motion.div
        key={activeStepId}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="glass-card p-5"
      >
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl ${activeStep.bg} border border-warm-200/50 dark:border-white/[0.06] flex items-center justify-center shadow-sm`}>
            <activeStep.icon className={`w-[22px] h-[22px] ${activeStep.color}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-warm-400">{activeStep.agent}</span>
              <span className="text-[10px] text-warm-300">·</span>
              <span className="text-[10px] text-warm-400">{Math.floor(metrics.cpu)}% CPU</span>
              {activeStepId === 'research' && (
                <>
                  <span className="text-[10px] text-warm-300">·</span>
                  <span className="text-[10px] text-warm-400">{metrics.sources} sources</span>
                </>
              )}
            </div>
            <p className="text-sm font-semibold text-warm-800 dark:text-warm-200 mt-0.5">
              {activeStep.label}
              <span className="inline-flex ml-0.5 text-primary-500">{dots}</span>
            </p>
          </div>
          {/* Step indicators */}
          <div className="flex items-center gap-2">
            {STEPS.map(step => (
              <div
                key={step.id}
                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                  completedSteps.has(step.id)
                    ? 'bg-emerald-500 shadow-sm shadow-emerald-500/30'
                    : step.id === activeStepId
                      ? 'bg-primary-500 animate-pulse shadow-sm shadow-primary-500/30'
                      : 'bg-warm-200/50 dark:bg-white/[0.08]'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4 h-1 bg-warm-200/50 dark:bg-white/[0.06] rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary-500 via-primary-400 to-accent-500 rounded-full"
            initial={{ width: '0%' }}
            animate={{
              width: completedSteps.size === 0 ? '20%' : completedSteps.size === 1 ? '50%' : '80%',
            }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      </motion.div>

      {/* Pipeline steps */}
      <div className="flex gap-3">
        {STEPS.map((step, i) => {
          const isDone = completedSteps.has(step.id)
          const isCurrent = activeStepId === step.id && !isDone
          return (
            <div key={step.id} className="flex-1 flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                isDone
                  ? 'bg-emerald-500 shadow-sm shadow-emerald-500/30'
                  : isCurrent
                    ? 'bg-primary-500 shadow-sm shadow-primary-500/30'
                    : 'bg-warm-100/60 dark:bg-white/[0.06]'
              }`}>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-white" />
                ) : (
                  <step.icon className={`w-4 h-4 ${isCurrent ? 'text-white' : 'text-warm-400'}`} />
                )}
              </div>
              <span className={`text-[11px] truncate ${
                isDone
                  ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                  : isCurrent
                    ? 'text-primary-600 dark:text-primary-400 font-medium'
                    : 'text-warm-400'
              }`}>
                {step.label}
              </span>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-px ${isDone ? 'bg-emerald-500' : 'bg-warm-200/50 dark:bg-white/[0.06]'}`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Terminal log */}
      <div className="bg-[#0e0d0c] rounded-xl border border-white/[0.06] overflow-hidden shadow-sm">
        <div className="flex items-center gap-1.5 px-3 py-2.5 bg-[#161514] border-b border-white/[0.06]">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#554f46]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#554f46]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#554f46]" />
          </div>
          <span className="text-[10px] text-[#8b8375] ml-3 font-mono tracking-wide">agent.log</span>
          {activeStep && (
            <span className="text-[10px] text-[#554f46] ml-auto font-mono">{activeStep.agent.toLowerCase()}@{activeStep.id}</span>
          )}
        </div>
        <div className="p-4 font-mono text-xs min-h-[120px]">
          <div className="flex gap-2">
            <span className="text-[#554f46] shrink-0 select-none">▸</span>
            <span className="text-[#b0a99b]">{log}</span>
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.6, repeat: Infinity }}
              className="w-2 h-4 bg-primary-500 inline-block align-middle ml-0.5"
            />
          </div>
          <div className="mt-3 flex items-center gap-2 text-[#554f46]">
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
            <span>Processing...</span>
          </div>
        </div>
      </div>
    </div>
  )
}
