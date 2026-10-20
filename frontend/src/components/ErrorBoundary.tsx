import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false, error: null }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center gap-5 px-6 py-14 text-center max-w-sm mx-auto">
          <div className="p-4 rounded-2xl bg-red-50/80 dark:bg-red-950/20 backdrop-blur-sm border border-red-200/50 dark:border-red-900/50 shadow-sm">
            <AlertTriangle className="w-7 h-7 text-red-500" />
          </div>
          <div className="space-y-2">
            <h3 className="text-base font-semibold text-warm-800 dark:text-warm-200">Something went wrong</h3>
            <p className="text-sm text-warm-500 dark:text-warm-400 max-w-xs mx-auto leading-relaxed">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="flex items-center gap-1.5 px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 rounded-xl shadow-sm shadow-red-500/20 hover:shadow-md hover:shadow-red-500/30 transition-all duration-200 active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
