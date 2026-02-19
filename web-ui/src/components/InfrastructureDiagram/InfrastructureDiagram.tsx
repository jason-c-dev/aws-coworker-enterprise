import { useState, useCallback } from 'react'
import { Network, Play, Download, ZoomIn, ZoomOut } from 'lucide-react'

/**
 * Infrastructure Diagram view.
 *
 * Uses React Flow for interactive diagrams. Since React Flow is a heavy
 * dependency, we lazy-load it. When no diagram data exists, we show
 * a placeholder with a button to generate one.
 */

interface InfrastructureDiagramProps {
  sessionId: string | null
  onGenerate?: () => void
}

// Placeholder for when React Flow isn't needed yet
export default function InfrastructureDiagram({ sessionId, onGenerate }: InfrastructureDiagramProps) {
  const [diagramData, setDiagramData] = useState<{ nodes: unknown[]; edges: unknown[] } | null>(null)
  const [mermaidSrc, setMermaidSrc] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const generateSample = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/diagrams/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'architecture',
          format: 'mermaid',
          resources: {
            vpcs: [{ name: 'Production VPC' }],
            instances: [{ name: 'Web Server', vpc_index: 0 }, { name: 'API Server', vpc_index: 0 }],
            buckets: [{ name: 'app-assets' }, { name: 'logs' }],
            databases: [{ name: 'Primary DB', vpc_index: 0 }],
            connections: [
              { from: 'ec2_0', to: 'rds_0', label: 'SQL' },
              { from: 'ec2_1', to: 's3_0', label: 'assets' },
            ],
          },
        }),
      })
      const data = await res.json()
      setMermaidSrc(data.content)
    } catch (err) {
      console.error('Failed to generate diagram:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="p-6 text-center py-12">
        <Network size={32} className="text-slate-300 mx-auto" />
        <p className="text-sm text-slate-500 mt-3">Select a session to view infrastructure diagrams</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Network size={20} className="text-aws-orange" />
          Infrastructure
        </h2>
        <button
          onClick={generateSample}
          disabled={loading}
          className="btn-primary flex items-center gap-1 text-sm"
        >
          <Play size={14} />
          {loading ? 'Generating...' : 'Generate Diagram'}
        </button>
      </div>

      {mermaidSrc ? (
        <div className="card">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-mono">Mermaid Diagram</span>
            <button
              onClick={() => {
                const blob = new Blob([mermaidSrc], { type: 'text/plain' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = 'diagram.mmd'
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="btn-ghost text-xs flex items-center gap-1"
            >
              <Download size={12} />
              Export
            </button>
          </div>
          <MermaidRenderer source={mermaidSrc} />
        </div>
      ) : (
        <div className="card text-center py-16">
          <Network size={48} className="text-slate-200 dark:text-slate-600 mx-auto" />
          <p className="text-sm text-slate-500 mt-4">
            No infrastructure diagrams yet.
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Run a discovery command to generate architecture diagrams, or click "Generate Diagram" for a sample.
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * Simple Mermaid renderer. Loads mermaid.js from CDN and renders inline.
 */
function MermaidRenderer({ source }: { source: string }) {
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const containerRef = useCallback(
    async (node: HTMLDivElement | null) => {
      if (!node || !source) return
      try {
        // Dynamic import of mermaid
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({
          startOnLoad: false,
          theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default',
          securityLevel: 'loose',
        })
        const id = `mermaid-${Date.now()}`
        const { svg: rendered } = await mermaid.render(id, source)
        setSvg(rendered)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to render diagram')
        // Fallback: show raw source
        setSvg(null)
      }
    },
    [source],
  )

  if (error) {
    return (
      <div>
        <p className="text-xs text-red-500 mb-2">Render error: {error}</p>
        <pre className="text-xs font-mono bg-slate-50 dark:bg-slate-900 p-3 rounded overflow-x-auto">
          {source}
        </pre>
      </div>
    )
  }

  return (
    <div ref={containerRef}>
      {svg ? (
        <div
          className="overflow-auto"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      ) : (
        <pre className="text-xs font-mono bg-slate-50 dark:bg-slate-900 p-3 rounded overflow-x-auto">
          {source}
        </pre>
      )}
    </div>
  )
}
