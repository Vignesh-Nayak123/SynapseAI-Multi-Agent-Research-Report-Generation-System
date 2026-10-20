import { useMemo, useRef, useState, useEffect, useCallback } from 'react'
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d'
import { ZoomIn, ZoomOut, Crosshair } from 'lucide-react'

interface Props {
  topic: string
  sources: string[]
  graphData?: {
    nodes: Array<{ id: string; type?: string; label?: string; url?: string }>
    links: Array<{ source: string; target: string; weight?: number }>
  }
}

interface Node {
  id: string
  name: string
  shortName: string
  val: number
  color: string
  group: 'topic' | 'source'
  url?: string
  x?: number
  y?: number
}

interface Link {
  source: string | Node
  target: string | Node
}

export function KnowledgeGraph({ topic, sources, graphData }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<ForceGraphMethods<any, any> | undefined>(undefined)
  const [dimensions, setDimensions] = useState({ width: 340, height: 340 })
  const [hoverNode, setHoverNode] = useState<string | null>(null)
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  )

  // Listen for theme changes (toggled via Sidebar)
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'))
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])

  // Theme-aware colors — memoized to avoid recreating on every render
  const colors = useMemo(() => ({
    bg: isDark ? '#121110' : '#f5f4f0',
    containerBg: isDark ? '#121110' : '#f5f4f0',
    link: isDark ? '#554e46' : '#b0a898',
    nodeTopic: '#6366f1',
    nodeSource: isDark ? '#a69b8d' : '#787162',
    nodeSourceHover: isDark ? '#f5f3f0' : '#292521',
    nodeRing: isDark ? 'rgba(99, 102, 241, 0.25)' : 'rgba(99, 102, 241, 0.35)',
    nodeRingOuter: isDark ? 'rgba(99, 102, 241, 0.08)' : 'rgba(99, 102, 241, 0.12)',
    label: isDark ? '#f5f3f0' : '#292521',
    shadow: isDark ? 'rgba(0,0,0,0.8)' : 'rgba(0,0,0,0.4)',
    glow: isDark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.3)',
    legendBg: isDark ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.85)',
    legendBorder: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    legendText: isDark ? '#a3a3a3' : '#787162',
    legendTextMuted: isDark ? '#737373' : '#a8a294',
    controllerBg: isDark ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.85)',
    controllerBorder: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)',
    controllerIcon: isDark ? '#818cf8' : '#6366f1',
  }), [isDark])

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        })
      }
    }

    const resizeObserver = new ResizeObserver(() => updateDimensions())
    if (containerRef.current) resizeObserver.observe(containerRef.current)
    window.addEventListener('resize', updateDimensions)
    updateDimensions()

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', updateDimensions)
    }
  }, [])

  const extractLabel = (url: string) => {
    if (!url || typeof url !== 'string') return 'Unknown Source'
    try {
      const urlObj = new URL(url)
      const domain = urlObj.hostname.replace('www.', '')
      const path = urlObj.pathname
      const file = path.split('/').pop() || ''
      if (domain.includes('arxiv')) return `arXiv:${file.replace('.pdf', '')}`
      if (file.length > 15) return `${domain}/...${file.slice(-10)}`
      return `${domain}/${file}`
    } catch {
      return url.slice(0, 30) + '...'
    }
  }

  const data = useMemo(() => {
    const safeTopic = (topic && typeof topic === 'string') ? topic : 'Research Topic'

    if (graphData && graphData.nodes && graphData.nodes.length > 0) {
      const nodes: Node[] = [
        {
          id: 'root',
          name: safeTopic,
          shortName: safeTopic.length > 40 ? safeTopic.slice(0, 40) + '...' : safeTopic,
          val: 30,
          color: '#6366f1',
          group: 'topic'
        },
        ...graphData.nodes.map(n => ({
          id: n.id,
          name: n.url || n.label || n.id,
          shortName: n.label || n.id,
          val: 10,
          color: '#a69b8d',
          group: 'source' as const,
          url: n.url
        }))
      ]
      const links: Link[] = [
        ...(graphData.links || []).map(l => ({ source: l.source, target: l.target })),
        ...graphData.nodes.map(n => ({ source: 'root', target: n.id }))
      ]
      return { nodes, links }
    }

    const validSources = Array.isArray(sources)
      ? Array.from(new Set(sources.filter(s => typeof s === 'string').map(s => s.trim()).filter(s => s.length > 0 && !['http://', 'https://'].includes(s))))
      : []

    return {
      nodes: [
        {
          id: 'root',
          name: safeTopic,
          shortName: safeTopic.length > 40 ? safeTopic.slice(0, 40) + '...' : safeTopic,
          val: 30,
          color: '#6366f1',
          group: 'topic'
        },
        ...validSources.map(s => ({
          id: s,
          name: s,
          shortName: extractLabel(s),
          val: 10,
          color: '#a69b8d',
          group: 'source' as const,
          url: s
        }))
      ],
      links: validSources.map(s => ({ source: 'root', target: s }))
    }
  }, [topic, sources, graphData])

  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force('charge')?.strength(-200)
      graphRef.current.d3Force('link')?.distance(80)
      graphRef.current.d3ReheatSimulation()
    }
  }, [data])

  // Auto fit on mount — wait for layout to stabilize
  useEffect(() => {
    if (graphRef.current && data.nodes.length > 1) {
      const timer = setTimeout(() => {
        try {
          graphRef.current?.zoomToFit(400, 60)
        } catch { /* not ready yet */ }
      }, 600)
      const timer2 = setTimeout(() => {
        try {
          graphRef.current?.zoomToFit(400, 60)
        } catch { /* not ready yet */ }
      }, 1200)
      return () => {
        clearTimeout(timer)
        clearTimeout(timer2)
      }
    }
  }, [data])

  const paintNode = useCallback((node: Node, ctx: CanvasRenderingContext2D, globalScale: number) => {
    if (typeof node.x !== 'number' || typeof node.y !== 'number') return
    const isRoot = node.group === 'topic'
    const isHovered = node.id === hoverNode
    const r = isRoot ? 5.5 : 3.5

    // Glow on hover
    if (isHovered) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r * 3, 0, 2 * Math.PI)
      const gradient = ctx.createRadialGradient(node.x, node.y, r, node.x, node.y, r * 4)
      gradient.addColorStop(0, colors.glow)
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = gradient
      ctx.fill()
    }

    // Outer ring for topic
    if (isRoot) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI)
      ctx.strokeStyle = colors.nodeRing
      ctx.lineWidth = 1
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(node.x, node.y, r + 6, 0, 2 * Math.PI)
      ctx.strokeStyle = colors.nodeRingOuter
      ctx.lineWidth = 0.8
      ctx.stroke()
    }

    // Node
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fillStyle = isRoot ? colors.nodeTopic : (isHovered ? colors.nodeSourceHover : colors.nodeSource)
    ctx.fill()

    if (isRoot) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
      ctx.strokeStyle = '#818cf8'
      ctx.lineWidth = 1.2
      ctx.stroke()
    }

    // Label — only show on hover for such a small graph
    if (isHovered) {
      const label = node.shortName
      const fontSize = 10 / globalScale
      ctx.font = `${isRoot ? '600' : ''} ${fontSize}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = colors.label
      ctx.shadowColor = colors.shadow
      ctx.shadowBlur = 5
      ctx.fillText(label, node.x, node.y + r + 6 + fontSize / 2)
      ctx.shadowBlur = 0
    }
  }, [hoverNode, colors])

  const nodePointerAreaPaint = useCallback((node: Node, color: string, ctx: CanvasRenderingContext2D) => {
    if (typeof node.x !== 'number' || typeof node.y !== 'number') return
    const isRoot = node.group === 'topic'
    const r = isRoot ? 5.5 : 3.5
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(node.x, node.y, r + 7, 0, 2 * Math.PI)
    ctx.fill()
  }, [])

  const handleZoom = (factor: number) => {
    if (graphRef.current) graphRef.current.zoom(graphRef.current.zoom() * factor, 400)
  }

  const handleFit = () => {
    if (graphRef.current) graphRef.current.zoomToFit(400, 50)
  }

  return (
    <div ref={containerRef} className="relative w-full aspect-square" style={{ backgroundColor: colors.containerBg }}>
      {/* Controls */}
      <div
        className="absolute top-3 right-3 z-10 flex gap-0.5 rounded-lg p-1 backdrop-blur-sm"
        style={{
          backgroundColor: colors.controllerBg,
          borderColor: colors.controllerBorder,
          borderWidth: 1,
        }}
      >
        <button
          onClick={() => handleZoom(1.2)}
          className="p-1.5 rounded transition-colors hover:bg-black/10 dark:hover:bg-white/10"
          style={{ color: colors.controllerIcon }}
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => handleZoom(0.8)}
          className="p-1.5 rounded transition-colors hover:bg-black/10 dark:hover:bg-white/10"
          style={{ color: colors.controllerIcon }}
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleFit}
          className="p-1.5 rounded transition-colors hover:bg-black/10 dark:hover:bg-white/10"
          style={{ color: colors.controllerIcon }}
        >
          <Crosshair className="w-3.5 h-3.5" />
        </button>
      </div>

      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={data}
        nodeCanvasObject={(node, ctx, globalScale) => paintNode(node as Node, ctx, globalScale)}
        nodePointerAreaPaint={(node, color, ctx) => nodePointerAreaPaint(node as Node, color, ctx)}
        linkColor={() => colors.link}
        linkWidth={1.2}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={1.5}
        linkDirectionalParticleSpeed={0.004}
        linkDirectionalParticleColor={() => '#6366f1'}
        backgroundColor={colors.bg}
        onNodeClick={(node) => {
          if (node.group === 'source') {
            const url = (node as Node).url || node.id
            if (url.startsWith('http')) window.open(url, '_blank')
            else window.open(`https://scholar.google.com/scholar?q=${encodeURIComponent(url)}`, '_blank')
          }
        }}
        onNodeHover={(node) => setHoverNode(node ? node.id : null)}
        cooldownTicks={300}
        d3VelocityDecay={0.3}
        d3AlphaDecay={0.02}
      />

      {/* Legend */}
      <div className="absolute bottom-3 left-3 right-3">
        <div
          className="flex items-center gap-4 px-3.5 py-2 rounded-xl backdrop-blur-sm shadow-lg"
          style={{
            backgroundColor: colors.legendBg,
            borderColor: colors.legendBorder,
            borderWidth: 1,
          }}
        >
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-primary-500 ring-1 ring-primary-400/40" />
            <span className="text-[10px] font-medium" style={{ color: colors.legendText }}>Topic</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colors.nodeSource, boxShadow: `0 0 0 1px ${isDark ? 'rgba(166,155,141,0.3)' : 'rgba(120,113,98,0.3)'}` }} />
            <span className="text-[10px] font-medium" style={{ color: colors.legendText }}>Source</span>
          </div>
          <div className="w-px h-4" style={{ backgroundColor: colors.legendBorder }} />
          <span className="text-[10px]" style={{ color: colors.legendTextMuted }}>Click a source to open</span>
        </div>
      </div>
    </div>
  )
}
