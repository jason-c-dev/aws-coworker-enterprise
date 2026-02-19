import { useState } from 'react'
import { Bot, Search, ArrowLeft, Pencil } from 'lucide-react'
import { useAgents, useAgent } from '@/hooks/useResources'
import * as api from '@/services/api'
import ResourceEditor from '../Common/ResourceEditor'
import MarkdownRenderer from '../Common/MarkdownRenderer'

export default function AgentBrowser() {
  const { agents, loading } = useAgents()
  const [selected, setSelected] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [editing, setEditing] = useState(false)
  const { detail, loading: detailLoading } = useAgent(selected)

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(filter.toLowerCase()) ||
      a.content.toLowerCase().includes(filter.toLowerCase()),
  )

  if (selected && detail) {
    return (
      <div className="p-6">
        <button onClick={() => { setSelected(null); setEditing(false) }} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
          <ArrowLeft size={14} />
          Back to agents
        </button>

        {editing ? (
          <ResourceEditor
            resource={detail}
            onSave={async (metadata, content) => {
              await api.updateAgent(detail.name, { metadata, content })
              setEditing(false)
              setSelected(detail.name)
            }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Bot size={20} className="text-aws-orange" />
                {detail.name}
              </h2>
              <button onClick={() => setEditing(true)} className="btn-secondary flex items-center gap-1 text-sm">
                <Pencil size={14} />
                Edit
              </button>
            </div>

            {Object.keys(detail.metadata).length > 0 && (
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
            )}

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
      <h2 className="text-xl font-semibold mb-4">Agents</h2>

      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input-field pl-9"
          placeholder="Search agents..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((agent) => (
            <div
              key={agent.name}
              onClick={() => setSelected(agent.name)}
              className="card cursor-pointer hover:border-aws-orange/50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Bot size={14} className="text-aws-orange shrink-0" />
                <span className="font-medium text-sm font-mono">{agent.name}</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate pl-6">
                {agent.content}
              </p>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-8">No agents match your search</p>
          )}
        </div>
      )}
    </div>
  )
}
