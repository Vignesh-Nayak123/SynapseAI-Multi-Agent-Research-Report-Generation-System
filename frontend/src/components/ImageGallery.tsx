import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ImageIcon, ExternalLink, ChevronLeft, ChevronRight,
  X, BarChart3, Loader2, AlertCircle,
} from 'lucide-react'
import type { ImageResult } from '../types'

interface Props {
  images: ImageResult[]
  graphs: ImageResult[]
  topic: string
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '')
  } catch {
    return url
  }
}

/* ─── Image Card ─── */

function ImageCard({
  img,
  index,
  onClick,
}: {
  img: ImageResult
  index: number
  onClick: () => void
}) {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  // Use thumbnail URL if available for the grid (lighter), fallback to full image
  const gridSrc = img.thumbnail_url || img.image_url

  return (
    <motion.button
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      onClick={onClick}
      className="group relative aspect-[4/3] rounded-xl overflow-hidden bg-warm-100 dark:bg-white/[0.04] border border-warm-200/40 dark:border-white/[0.06] hover:border-primary-400/50 dark:hover:border-primary-500/40 hover:shadow-lg hover:shadow-primary-500/5 transition-all duration-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-500/40"
    >
      {!loaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-5 h-5 text-warm-300 dark:text-warm-600 animate-spin" />
        </div>
      )}

      {error ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 text-warm-400">
          <AlertCircle className="w-5 h-5" />
          <span className="text-[10px]">Failed to load</span>
        </div>
      ) : (
        <img
          src={gridSrc}
          alt={img.title || `Image related to research topic`}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}

      {/* Hover overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute bottom-0 left-0 right-0 p-3">
          <p className="text-[11px] text-white/90 font-medium line-clamp-2 text-left leading-tight">
            {img.title || 'Related image'}
          </p>
          <p className="text-[9px] text-white/60 mt-1 text-left flex items-center gap-1">
            <ExternalLink className="w-2.5 h-2.5" />
            {extractDomain(img.source_url)}
          </p>
        </div>
      </div>
    </motion.button>
  )
}

/* ─── Lightbox ─── */

function Lightbox({
  img,
  onClose,
  onPrev,
  onNext,
  hasPrev,
  hasNext,
}: {
  img: ImageResult
  onClose: () => void
  onPrev: () => void
  onNext: () => void
  hasPrev: boolean
  hasNext: boolean
}) {
  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && hasPrev) onPrev()
      if (e.key === 'ArrowRight' && hasNext) onNext()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, onPrev, onNext, hasPrev, hasNext])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-[100] bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 sm:p-8"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image lightbox"
    >
      {/* Keyboard hint */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 hidden sm:flex items-center gap-3 text-[11px] text-white/40">
        {hasPrev && <span>← Prev</span>}
        {hasNext && <span>→ Next</span>}
        <span>⎋ Close</span>
      </div>
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-all duration-200"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Prev */}
      {hasPrev && (
        <button
          onClick={(e) => { e.stopPropagation(); onPrev() }}
          className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-all duration-200"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      )}

      {/* Next */}
      {hasNext && (
        <button
          onClick={(e) => { e.stopPropagation(); onNext() }}
          className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-all duration-200"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      )}

      {/* Image */}
      <motion.div
        key={img.image_url}
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="relative max-w-5xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={img.image_url}
          alt={img.title || 'Related image'}
          className="max-w-full max-h-[80vh] object-contain rounded-2xl shadow-2xl"
        />

        <div className="mt-3 flex items-center justify-between px-1">
          <div className="min-w-0 flex-1">
            <p className="text-sm text-white/90 font-medium truncate">
              {img.title || 'Related image'}
            </p>
            <a
              href={img.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-white/50 hover:text-white/80 transition-colors inline-flex items-center gap-1 mt-0.5"
            >
              <ExternalLink className="w-3 h-3" />
              {extractDomain(img.source_url)}
            </a>
          </div>
          {img.width && img.height && (
            <span className="text-[11px] text-white/40 font-mono shrink-0 ml-4">
              {img.width} × {img.height}
            </span>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

/* ─── Section Wrapper ─── */

function MediaSection({
  title,
  icon,
  items,
  topic,
  accentColor,
}: {
  title: string
  icon: React.ReactNode
  items: ImageResult[]
  topic: string
  accentColor: string
}) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)

  const openLightbox = (index: number) => setLightboxIndex(index)
  const closeLightbox = () => setLightboxIndex(null)

  const goPrev = () => {
    if (lightboxIndex !== null && lightboxIndex > 0) {
      setLightboxIndex(lightboxIndex - 1)
    }
  }

  const goNext = () => {
    if (lightboxIndex !== null && lightboxIndex < items.length - 1) {
      setLightboxIndex(lightboxIndex + 1)
    }
  }

  if (items.length === 0) return null

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5 mb-3 px-1">
        <div
          className={`w-8 h-8 rounded-xl flex items-center justify-center ring-1`}
          style={{
            backgroundColor: `${accentColor}15`,
            color: accentColor,
            borderColor: `${accentColor}30`,
          }}
        >
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-semibold text-warm-800 dark:text-warm-200">{title}</h3>
          <p className="text-[10px] text-warm-400">{items.length} result{items.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {items.map((img, i) => (
          <ImageCard
            key={`${img.image_url}-${i}`}
            img={img}
            index={i}
            onClick={() => openLightbox(i)}
          />
        ))}
      </div>

      {/* Lightbox */}
      <AnimatePresence>
        {lightboxIndex !== null && items[lightboxIndex] && (
          <Lightbox
            img={items[lightboxIndex]}
            onClose={closeLightbox}
            onPrev={goPrev}
            onNext={goNext}
            hasPrev={lightboxIndex > 0}
            hasNext={lightboxIndex < items.length - 1}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

/* ─── Empty State ─── */

function EmptyMedia() {
  return (
    <div className="text-center py-12 px-4">
      <ImageIcon className="w-8 h-8 text-warm-200 dark:text-warm-700 mx-auto mb-3" />
      <p className="text-sm text-warm-400">No related media found</p>
      <p className="text-[11px] text-warm-500 mt-1">Images and charts will appear here once the research is complete</p>
    </div>
  )
}

/* ─── Main Component ─── */

export function ImageGallery({ images, graphs, topic }: Props) {
  const hasContent = useMemo(
    () => images.length > 0 || graphs.length > 0,
    [images, graphs]
  )

  if (!hasContent) return <EmptyMedia />

  return (
    <div className="space-y-6">
      {/* Related Images */}
      <MediaSection
        title="Related Images"
        icon={<ImageIcon className="w-4 h-4" />}
        items={images}
        topic={topic}
        accentColor="#6366f1"
      />

      {/* Charts & Graphs */}
      <MediaSection
        title="Charts & Visualizations"
        icon={<BarChart3 className="w-4 h-4" />}
        items={graphs}
        topic={topic}
        accentColor="#f59e0b"
      />
    </div>
  )
}
