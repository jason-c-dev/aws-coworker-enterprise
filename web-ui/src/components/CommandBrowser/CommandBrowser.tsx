import { useState } from 'react'
import { Terminal, Search, ArrowLeft, Pencil, Play, Save, X } from 'lucide-react'
import { useCommands, useCommand } from '@/hooks/useResources'
import * as api from '@/services/api'
import ResourceEditor from '../Common/ResourceEditor'
import MarkdownRenderer from '../Common/MarkdownRenderer'

interface CommandBrowserProps {
  onExecute?: (command: string) => void
}

export default function CommandBrowser({ onExecute }: CommandBrowserProps) {
  const { commands, loading } = useCommands()
  const [selected, setSelected] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [editing, setEditing] = useState(false)
  const { detail, loading: detailLoading } = useCommand(selected)

  const filtered = commands.filter(
    (c) =>
      c.name.toLowerCase().includes(filter.toLowerCase()) ||
      c.description.toLowerCase().includes(filter.toLowerCase()),
  )

  if (selected && detail) {
    return (
      <div className="p-6">
        <button onClick={() => { setSelected(null); setEditing(false) }} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
          <ArrowLeft size={14} />
          Back to commands
        </button>

        {editing ? (
          <ResourceEditor
            resource={detail}
            onSave={async (metadata, content) => {
              await api.updateCommand(detail.name, { metadata, content })
              setEditing(false)
              setSelected(detail.name) // refresh
            }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Terminal size={20} className="text-aws-orange" />
                {detail.name}
              </h2>
              <div className="flex gap-2">
                <button onClick={() => setEditing(true)} className="btn-secondary flex items-center gap-1 text-sm">
                  <Pencil size={14} />
                  Edit
                </button>
                {onExecute && (
                  <button onClick={() => onExecute(detail.name)} className="btn-primary flex items-center gap-1 text-sm">
                    <Play size={14} />
                    Execute
                  </button>
                )}
              </div>
            </div>

            {/* Frontmatter card */}
            <div className="card mb-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                {Object.entries(detail.metadata).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">{key}</dt>
                    <dd className="mt-0.5 font-mono text-code">
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </dd>
                  </div>
                ))}
              </div>
            </div>

            {/* Body — rendered as markdown */}
            <div className="card overflow-y-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
              <MarkdownRenderer content={detail.content} />
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Commands</h2>
      </div>

      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input-field pl-9"
          placeholder="Search commands..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="space-y-2">
          {filtered.map((cmd) => (
            <div
              key={cmd.name}
              onClick={() => setSelected(cmd.name)}
              className="card flex items-center justify-between cursor-pointer hover:border-aws-orange/50 transition-colors"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Terminal size={14} className="text-aws-orange shrink-0" />
                  <span className="font-medium text-sm font-mono">{cmd.name}</span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate pl-6">
                  {cmd.description}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4 shrink-0">
                <span className="badge-blue text-xs">{cmd.agent}</span>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-8">No commands match your search</p>
          )}
        </div>
      )}
    </div>
  )
}

function LoadingSpinner() {
  return (
    <div className="flex justify-center py-12">
      <div className="w-6 h-6 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
