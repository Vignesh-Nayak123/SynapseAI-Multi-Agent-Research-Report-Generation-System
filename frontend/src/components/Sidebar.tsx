import { useState, useEffect } from 'react'
import { Plus, MessageSquare, Moon, Sun, History, ChevronLeft, Lock, Unlock, Fingerprint, Trash2, Copy, Check, ShieldAlert, Eye, ArrowLeft, Save, Search, X } from 'lucide-react'
import { BrandIcon } from './BrandIcon'
import { setFavicon } from '../lib/favicon'
import type { HistoryItem } from '../hooks/useResearch'
import { formatDistanceToNow } from 'date-fns'

interface Props {
  history: HistoryItem[]
  onSelect: (item: HistoryItem) => void
  onClear: () => void
  onNewChat: () => void
  passphrase: string
  onPassphraseChange: (val: string) => void
  hasBiometricCredential: boolean
  isUnlocking: boolean
  biometricError: string | null
  onRegisterBiometric: () => void
  onUnlockBiometric: () => void
  onClearBiometric: () => void
  recoveryCode: string | null
  onDismissRecoveryCode: () => void
  onRecoverWithCode: (code: string) => Promise<void>
  passphraseHint: string
  onSaveHint: (hint: string) => void
  onShowRecoveryCode: () => void
}

export function Sidebar({
  history,
  onSelect,
  onClear,
  onNewChat,
  passphrase,
  onPassphraseChange,
  hasBiometricCredential,
  isUnlocking,
  onRegisterBiometric,
  onUnlockBiometric,
  onClearBiometric,
  biometricError,
  recoveryCode,
  onDismissRecoveryCode,
  onRecoverWithCode,
  passphraseHint,
  onSaveHint,
  onShowRecoveryCode,
}: Props) {
  const [collapsed, setCollapsed] = useState(false)
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark')
    }
    return false
  })
  const [showRecoveryInput, setShowRecoveryInput] = useState(false)
  const [recoveryInputValue, setRecoveryInputValue] = useState('')
  const [recoveryCopied, setRecoveryCopied] = useState(false)
  const [recoveryRecovering, setRecoveryRecovering] = useState(false)
  const [showHintInput, setShowHintInput] = useState(false)
  const [hintDraft, setHintDraft] = useState(passphraseHint)
  const [historySearch, setHistorySearch] = useState('')

  useEffect(() => {
    setHintDraft(passphraseHint)
  }, [passphraseHint])

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      localStorage.theme = 'dark'
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.theme = 'light'
    }
    setFavicon(isDark ? 'dark' : 'light')
  }, [isDark])

  const toggleTheme = () => setIsDark(!isDark)

  const handleCopyRecoveryCode = async () => {
    if (!recoveryCode) return
    try {
      await navigator.clipboard.writeText(recoveryCode)
      setRecoveryCopied(true)
      setTimeout(() => setRecoveryCopied(false), 2000)
    } catch {
      // Fallback
    }
  }

  const handleRecover = async () => {
    if (!recoveryInputValue.trim()) return
    setRecoveryRecovering(true)
    try {
      await onRecoverWithCode(recoveryInputValue.trim().toLowerCase())
      setShowRecoveryInput(false)
      setRecoveryInputValue('')
    } catch {
      // Error is shown via biometricError in parent
    } finally {
      setRecoveryRecovering(false)
    }
  }

  const handleSaveHintClick = () => {
    onSaveHint(hintDraft)
    setShowHintInput(false)
  }

  return (
    <div className={`relative h-full shrink-0 transition-all duration-300 ease-out ${collapsed ? 'w-[60px]' : 'w-64'}`}>
      <div className="h-full bg-white/90 dark:bg-[#161514]/90 backdrop-blur-xl border-r border-warm-200/50 dark:border-white/[0.06] flex flex-col shadow-sm">
        {/* Header */}
        <div className={collapsed ? 'p-3 flex flex-col items-center gap-2' : 'p-4 pb-3'}>
          {collapsed ? (
            <button onClick={onNewChat} className="p-2.5 rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 text-white hover:from-primary-500 hover:to-primary-400 shadow-sm shadow-primary-500/20 hover:shadow-md hover:shadow-primary-500/30 transition-all duration-200 active:scale-95">
              <Plus className="w-4 h-4" />
            </button>
          ) : (
            <>                <div className="flex items-center justify-between mb-4 px-0.5">
                <div className="flex items-center gap-2.5">
                  <div className="shrink-0">
                    <BrandIcon size={32} />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-warm-800 dark:text-warm-200">Multi-Agent Research System</span>
                    <p className="text-[11px] text-warm-400 -mt-0.5">AI-Powered</p>
                  </div>
                </div>
              </div>
              <button
                onClick={onNewChat}
                className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white rounded-xl text-sm font-medium transition-all duration-200 shadow-sm shadow-primary-500/20 hover:shadow-md hover:shadow-primary-500/30 active:scale-[0.98]"
              >
                <Plus className="w-3.5 h-3.5" />
                New chat
              </button>
            </>
          )}
        </div>

        {/* History */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className={collapsed ? 'px-2 py-3 flex flex-col items-center gap-1' : 'p-3 pt-2'}>
            {!collapsed && (
              <div className="flex items-center justify-between px-2 mb-2">
                <span className="text-[11px] font-medium text-warm-400 dark:text-warm-500 uppercase tracking-wider flex items-center gap-1.5">
                  <History className="w-3 h-3" />
                  History
                </span>
                {history.length > 0 && (
                  <button onClick={onClear} className="text-[10px] text-warm-400 hover:text-red-500 transition-colors px-1.5 py-0.5 rounded hover:bg-red-50/50 dark:hover:bg-red-950/30">
                    Clear
                  </button>
                )}
              </div>
            )}

            {/* ── Semantic History Search ── */}
            {!collapsed && history.length > 0 && (
              <div className="relative mb-2 px-2">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-3 h-3 text-warm-400 pointer-events-none" />
                <input
                  type="text"
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  placeholder="Search history..."
                  className="w-full pl-8 pr-3 py-1.5 text-[11px] rounded-lg bg-warm-50/60 dark:bg-white/[0.04] border border-warm-200/40 dark:border-white/[0.06] text-warm-700 dark:text-warm-300 placeholder:text-warm-400 focus:outline-none focus:ring-1 focus:ring-primary-500/30 transition-all duration-200"
                />
                {historySearch && (
                  <button
                    onClick={() => setHistorySearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-warm-400 hover:text-warm-600 dark:hover:text-warm-300"
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>
            )}

            {(() => {
              const filtered = historySearch
                ? history.filter(item =>
                    item.topic.toLowerCase().includes(historySearch.toLowerCase())
                  )
                : history

              if (filtered.length === 0) {
                return !collapsed && (
                  <div className="text-center py-12">
                    <div className="w-10 h-10 rounded-xl bg-warm-100/60 dark:bg-white/[0.04] flex items-center justify-center mx-auto mb-3">
                      {historySearch ? <Search className="w-4 h-4 text-warm-400" /> : <MessageSquare className="w-4 h-4 text-warm-400" />}
                    </div>
                    <p className="text-xs text-warm-400">{historySearch ? 'No matching results' : 'No history yet'}</p>
                    <p className="text-[10px] text-warm-300 mt-1">{historySearch ? `No topics match "${historySearch}"` : 'Start a research to see it here'}</p>
                  </div>
                )
              }

              if (collapsed) {
                return (
                  <div className="space-y-1.5">
                    {filtered.slice(0, 8).map((item) => (
                      <button
                        key={item.id}
                        onClick={() => onSelect(item)}
                        className="w-9 h-9 rounded-xl bg-warm-50/60 dark:bg-white/[0.04] border border-warm-200/50 dark:border-white/[0.06] hover:border-primary-300/50 dark:hover:border-primary-700/50 hover:shadow-sm transition-all duration-200 flex items-center justify-center shrink-0"
                        title={item.topic}
                      >
                        <MessageSquare className="w-3.5 h-3.5 text-warm-400" />
                      </button>
                    ))}
                  </div>
                )
              }

              return (
                <div className="space-y-0.5">
                  {filtered.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => onSelect(item)}
                      className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-warm-50/60 dark:hover:bg-white/[0.03] transition-all duration-200 group border border-transparent hover:border-warm-200/50 dark:hover:border-white/[0.06]"
                    >
                      <div className="flex items-start gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-warm-100/60 dark:bg-white/[0.05] flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-primary-100/80 dark:group-hover:bg-primary-950/30 transition-colors">
                          <MessageSquare className="w-3.5 h-3.5 text-warm-400 group-hover:text-primary-500 transition-colors" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-warm-700 dark:text-warm-300 line-clamp-1 group-hover:text-warm-900 dark:group-hover:text-warm-100 transition-colors">
                            {item.topic}
                          </p>
                          <p className="text-[11px] text-warm-400 mt-0.5">
                            {formatDistanceToNow(item.timestamp, { addSuffix: true })}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )
            })()}
          </div>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full border border-warm-200/50 dark:border-white/[0.08] bg-white dark:bg-[#161514] flex items-center justify-center text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 shadow-sm hover:shadow transition-all duration-200 z-10"
        >
          <ChevronLeft className={`w-3 h-3 transition-transform duration-200 ${collapsed ? 'rotate-180' : ''}`} />
        </button>

        {/* Footer */}
        <div className="border-t border-warm-200/50 dark:border-white/[0.06]">
          {/* Zero-knowledge section */}
          {!collapsed && (
            <div className="px-3 pt-3 pb-1.5">
              <label className="text-[10px] font-medium text-warm-400 dark:text-warm-500 uppercase tracking-wider flex items-center gap-1 mb-2">
                {passphrase ? (
                  <><Lock className="w-2.5 h-2.5 text-emerald-500" /> Encryption active</>
                ) : hasBiometricCredential ? (
                  <><Fingerprint className="w-2.5 h-2.5 text-primary-500" /> Biometric ready</>
                ) : (
                  <><Unlock className="w-2.5 h-2.5 text-warm-400" /> Session passphrase</>
                )}
              </label>

              {/* Biometric error */}
              {biometricError && (
                <div className="mb-2 px-2.5 py-1.5 bg-red-50/80 dark:bg-red-950/20 backdrop-blur-sm border border-red-200/50 dark:border-red-900/50 rounded-lg text-[10px] text-red-600 dark:text-red-400 leading-tight">
                  {biometricError}
                </div>
              )}

              {/* Recovery code display */}
              {recoveryCode && (
                <div className="mb-2 p-2.5 bg-amber-50/80 dark:bg-amber-950/20 backdrop-blur-sm border border-amber-200/50 dark:border-amber-800/50 rounded-xl space-y-2">
                  <div className="flex items-start gap-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[10px] font-semibold text-amber-700 dark:text-amber-400 leading-tight">
                        Recovery code saved
                      </p>
                      <p className="text-[9px] text-amber-600 dark:text-amber-500 leading-tight mt-0.5">
                        Save this somewhere safe — it's your only backup.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-stretch gap-1">
                    <div className="flex-1 min-w-0 px-2 py-1.5 bg-white/80 dark:bg-black/30 border border-amber-200/50 dark:border-amber-800/50 rounded-lg font-mono text-[10px] text-amber-800 dark:text-amber-300 tracking-wide select-all break-all leading-relaxed">
                      {recoveryCode}
                    </div>
                    <button
                      type="button"
                      onClick={handleCopyRecoveryCode}
                      className="px-2 py-1.5 rounded-lg bg-amber-100/80 dark:bg-amber-900/20 border border-amber-200/50 dark:border-amber-800/50 text-amber-600 dark:text-amber-400 hover:bg-amber-200/80 dark:hover:bg-amber-800/20 transition-all duration-200 shrink-0"
                    >
                      {recoveryCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[9px] text-amber-600 dark:text-amber-500 font-medium">
                      Optional hint (reminds you of your passphrase)
                    </label>
                    <div className="flex items-stretch gap-1">
                      <input
                        type="text"
                        value={hintDraft}
                        onChange={(e) => setHintDraft(e.target.value)}
                        placeholder="e.g., my usual research password"
                        maxLength={100}
                        className="flex-1 min-w-0 px-2 py-1.5 text-[10px] rounded-lg border border-amber-200/50 dark:border-amber-800/50 bg-white/80 dark:bg-black/30 text-amber-700 dark:text-amber-300 placeholder:text-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-500/30 transition-all duration-200"
                      />
                      <button
                        type="button"
                        onClick={handleSaveHintClick}
                        className="px-2 py-1 rounded-lg bg-amber-100/80 dark:bg-amber-900/20 border border-amber-200/50 dark:border-amber-800/50 text-amber-600 dark:text-amber-400 hover:bg-amber-200/80 dark:hover:bg-amber-800/20 transition-all duration-200 shrink-0"
                      >
                        <Save className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={onDismissRecoveryCode}
                    className="w-full py-1.5 text-[10px] font-medium text-amber-600 dark:text-amber-400 bg-amber-100/80 dark:bg-amber-900/20 hover:bg-amber-200/80 dark:hover:bg-amber-800/20 rounded-lg transition-all duration-200"
                  >
                    I've saved it — dismiss
                  </button>
                </div>
              )}

              {/* Biometric unlock view */}
              {hasBiometricCredential && !passphrase && !recoveryCode && !showRecoveryInput && (
                <>
                  <button
                    type="button"
                    onClick={onUnlockBiometric}
                    disabled={isUnlocking}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-primary-50/80 dark:bg-primary-950/20 backdrop-blur-sm border border-primary-200/50 dark:border-primary-800/50 rounded-lg text-xs font-medium text-primary-700 dark:text-primary-300 hover:bg-primary-100/80 dark:hover:bg-primary-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {isUnlocking ? (
                      <>
                        <span className="w-3 h-3 border-2 border-primary-400 border-t-transparent rounded-full animate-spin" />
                        Unlocking...
                      </>
                    ) : (
                      <>
                        <Fingerprint className="w-3.5 h-3.5" />
                        Unlock with biometric
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowRecoveryInput(true)}
                    className="w-full text-[10px] text-warm-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors mt-1.5 py-1"
                  >
                    Lost biometric? Use recovery code
                  </button>
                </>
              )}

              {/* Recovery input */}
              {hasBiometricCredential && !passphrase && showRecoveryInput && (
                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => { setShowRecoveryInput(false); setRecoveryInputValue('') }}
                    className="flex items-center gap-1 text-[10px] text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 transition-colors"
                  >
                    <ArrowLeft className="w-2.5 h-2.5" />
                    Back to biometric unlock
                  </button>

                  <p className="text-[10px] font-medium text-warm-600 dark:text-warm-400">
                    {passphraseHint ? (
                      <>Hint: <span className="text-warm-500 dark:text-warm-500 italic">{passphraseHint}</span></>
                    ) : (
                      'Enter your recovery code to unlock'
                    )}
                  </p>

                  <div className="flex items-stretch gap-1">
                    <input
                      type="text"
                      value={recoveryInputValue}
                      onChange={(e) => setRecoveryInputValue(e.target.value.toLowerCase())}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleRecover() }}
                      placeholder="e.g., apple-coral-quill-tiger-zeal"
                      autoFocus
                      className="flex-1 min-w-0 px-2.5 py-1.5 text-[10px] rounded-lg border border-warm-200/50 dark:border-white/[0.08] bg-warm-50/60 dark:bg-white/[0.04] text-warm-700 dark:text-warm-300 focus:outline-none focus:ring-1 focus:ring-primary-500/30 placeholder:text-warm-400 font-mono transition-all duration-200"
                    />
                    <button
                      type="button"
                      onClick={handleRecover}
                      disabled={recoveryRecovering || !recoveryInputValue.trim()}
                      className="px-2.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-white text-[10px] font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shrink-0"
                    >
                      {recoveryRecovering ? (
                        <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin block" />
                      ) : (
                        'Recover'
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Passphrase active view */}
              {passphrase && !recoveryCode && (
                <>
                  <div className="flex items-stretch gap-1.5">
                    <input
                      type="password"
                      value={passphrase}
                      onChange={(e) => onPassphraseChange(e.target.value)}
                      readOnly={hasBiometricCredential}
                      className={`flex-1 min-w-0 px-2.5 py-1.5 text-xs rounded-lg border transition-all duration-200 ${
                        hasBiometricCredential
                          ? 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-200/50 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-300 cursor-default'
                          : 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-200/50 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-300'
                      } focus:outline-none focus:ring-1 focus:ring-primary-500/30`}
                    />
                    {!hasBiometricCredential && (
                      <button
                        type="button"
                        onClick={onRegisterBiometric}
                        disabled={isUnlocking}
                        className="px-2 py-1.5 rounded-lg bg-primary-50/80 dark:bg-primary-950/20 border border-primary-200/50 dark:border-primary-800/50 text-primary-600 dark:text-primary-400 hover:bg-primary-100/80 dark:hover:bg-primary-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shrink-0"
                        title="Enable biometric unlock"
                      >
                        {isUnlocking ? (
                          <span className="w-3.5 h-3.5 border-2 border-primary-400 border-t-transparent rounded-full animate-spin block" />
                        ) : (
                          <Fingerprint className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                  </div>

                  {/* Recovery options */}
                  {hasBiometricCredential && (
                    <div className="mt-2 space-y-1.5">
                      {showHintInput ? (
                        <div className="flex items-stretch gap-1">
                          <input
                            type="text"
                            value={hintDraft}
                            onChange={(e) => setHintDraft(e.target.value)}
                            placeholder="Recovery hint (reminds you of passphrase)"
                            maxLength={100}
                            className="flex-1 min-w-0 px-2 py-1 text-[10px] rounded-lg border border-warm-200/50 dark:border-white/[0.08] bg-warm-50/60 dark:bg-white/[0.04] text-warm-700 dark:text-warm-300 focus:outline-none focus:ring-1 focus:ring-primary-500/30 placeholder:text-warm-400 transition-all duration-200"
                          />
                          <button
                            type="button"
                            onClick={handleSaveHintClick}
                            className="px-1.5 py-1 rounded-lg bg-primary-50/80 dark:bg-primary-950/20 border border-primary-200/50 dark:border-primary-800/50 text-primary-600 dark:text-primary-400 hover:bg-primary-100/80 dark:hover:bg-primary-900/20 transition-all duration-200 shrink-0"
                          >
                            <Save className="w-2.5 h-2.5" />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowHintInput(true)}
                          className="text-[9px] text-warm-400 hover:text-warm-600 dark:hover:text-warm-300 transition-colors"
                        >
                          {passphraseHint
                            ? <>Hint: <span className="italic">{passphraseHint}</span> — edit</>
                            : 'Add a recovery hint'}
                        </button>
                      )}

                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={onShowRecoveryCode}
                          className="text-[9px] text-warm-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors flex items-center gap-0.5"
                        >
                          <Eye className="w-2.5 h-2.5" />
                          View recovery code
                        </button>
                      </div>

                      <div className="flex items-center gap-1 mt-1">
                        <p className="text-[9px] text-warm-400 leading-tight flex-1">
                          {hasBiometricCredential
                            ? 'Unlocked — passphrase in memory'
                            : 'API keys encrypted end-to-end'}
                        </p>
                        {hasBiometricCredential && (
                          <button
                            type="button"
                            onClick={onClearBiometric}
                            className="text-[9px] text-warm-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-0.5 px-1 py-0.5 rounded hover:bg-red-50/50 dark:hover:bg-red-950/30"
                          >
                            <Trash2 className="w-2.5 h-2.5" />
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {!hasBiometricCredential && (
                    <p className="text-[9px] text-warm-400 mt-1 leading-tight">
                      API keys encrypted end-to-end
                    </p>
                  )}
                </>
              )}

              {/* No passphrase, no biometric */}
              {!passphrase && !hasBiometricCredential && !recoveryCode && (
                <>
                  <input
                    type="password"
                    value={passphrase}
                    onChange={(e) => onPassphraseChange(e.target.value)}
                    placeholder="Set a passphrase..."
                    className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-warm-200/50 dark:border-white/[0.08] bg-warm-50/60 dark:bg-white/[0.04] text-warm-700 dark:text-warm-300 focus:outline-none focus:ring-1 focus:ring-primary-500/30 placeholder:text-warm-400 transition-all duration-200"
                  />
                  <p className="text-[9px] text-warm-400 mt-1.5 leading-tight">
                    Unset — API keys sent in plaintext
                  </p>
                </>
              )}
            </div>
          )}

          <div className={collapsed ? 'p-3 flex flex-col items-center gap-2' : 'p-3'}>
            {collapsed ? (
              <button onClick={toggleTheme} className="p-2 rounded-xl hover:bg-warm-50/60 dark:hover:bg-white/[0.04] transition-colors text-warm-400 hover:text-warm-600 dark:hover:text-warm-300">
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            ) : (
              <button onClick={toggleTheme} className="flex items-center gap-2.5 w-full px-3 py-2 rounded-xl hover:bg-warm-50/60 dark:hover:bg-white/[0.03] transition-all duration-200 text-sm text-warm-500 dark:text-warm-400">
                <div className="w-7 h-7 rounded-lg bg-warm-100/60 dark:bg-white/[0.05] flex items-center justify-center">
                  {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
                </div>
                <span>{isDark ? 'Light' : 'Dark'} mode</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
