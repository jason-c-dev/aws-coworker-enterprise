import { useState } from 'react'
import { Save, X, ChevronDown, ChevronRight } from 'lucide-react'
import type { ResourceDetail } from '@/types/resource'

interface ResourceEditorProps {
  resource: ResourceDetail
  onSave: (metadata: Record<string, unknown>, content: string) => Promise<void>
  onCancel: () => void
}

export default function ResourceEditor({ resource, onSave, onCancel }: ResourceEditorProps) {
  const hasFrontmatter = Object.keys(resource.metadata).length > 0
  const [frontmatterText, setFrontmatterText] = useState(
    Object.entries(resource.metadata)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join('\n'),
  )
  const [content, setContent] = useState(resource.content)
  const [saving, setSaving] = useState(false)
  const [fmExpanded, setFmExpanded] = useState(true)

  const handleSave = async () => {
    setSaving(true)
    try {
      // Simple key: value parsing for frontmatter
      const fm: Record<string, unknown> = {}
      for (const line of frontmatterText.split('\n')) {
        const colonIdx = line.indexOf(':')
        if (colonIdx > 0) {
          const key = line.slice(0, colonIdx).trim()
          const val = line.slice(colonIdx + 1).trim()
          // Auto-detect arrays (comma-separated)
          if (val.includes(',')) {
            fm[key] = val.split(',').map((s) => s.trim())
          } else {
            fm[key] = val
          }
        }
      }
      await onSave(fm, content)
    } finally {
      setSaving(false)
    }
  }

  // Count frontmatter lines for textarea height
  const fmLineCount = frontmatterText.split('\n').length

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 180px)' }}>
      <div className="flex items-center justify-between mb-3 shrink-0">
        <h3 className="font-semibold">Editing: {resource.name}</h3>
        <div className="flex gap-2">
          <button onClick={onCancel} className="btn-secondary flex items-center gap-1 text-sm">
            <X size={14} />
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-1 text-sm">
            <Save size={14} />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {hasFrontmatter && (
        /* Collapsible frontmatter section — compact, above the main editor */
        <div className="shrink-0 mb-3 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
          <button
            onClick={() => setFmExpanded(!fmExpanded)}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {fmExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            Frontmatter (YAML)
          </button>
          {fmExpanded && (
            <textarea
              className="w-full font-mono text-xs px-3 py-2 bg-white dark:bg-slate-900 border-0 border-t border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-0 resize-none"
              style={{ height: `${Math.min(Math.max(fmLineCount + 1, 3), 10) * 1.5}rem` }}
              value={frontmatterText}
              onChange={(e) => setFrontmatterText(e.target.value)}
            />
          )}
        </div>
      )}

      {/* Main body editor — fills remaining space */}
      <div className="flex flex-col flex-1 min-h-0">
        <label className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 block shrink-0">
          {hasFrontmatter ? 'Body (Markdown)' : 'Content (Markdown)'}
        </label>
        <textarea
          className="input-field font-mono text-code flex-1 min-h-0 resize-none"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </div>
    </div>
  )
}
