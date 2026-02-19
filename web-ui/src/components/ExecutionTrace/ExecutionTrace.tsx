import { useState, useEffect } from 'react'
import {
  Activity, ChevronRight, ChevronDown, CheckCircle, XCircle,
  AlertTriangle, Clock, Wrench, Bot, MessageSquare, ShieldAlert,
  Download, Search, Filter,
} from 'lucide-react'
import type { ExecutionEvent } from '@/types/event'
import type { HistoryEntry } from '@/types/resource'

interface ExecutionTraceProps {
  history: HistoryEntry[]
  sessionId: string | null
}

export default function ExecutionTrace({ history, sessionId }: ExecutionTraceProps) {
  const [filterText, setFilterText] = useState('')
  const [filterLevel, setFilterLevel] = useState<string>('all')

  // Flatten all events from history
  const allEvents = history.flatMap((entry) =>
    (entry.events || []).map((e) => ({ ...e, _messageRole: entry.role })),
  )

  const filteredEvents = allEvents.filter((e) => {
    if (filterLevel !== 'all') {
      if (filterLevel === 'errors' && e.type !== 'error') return false
      if (filterLevel === 'tools' && e.type !== 'tool_use' && e.type !== 'tool_result') return false
      if (filterLevel === 'agents' && e.type !== 'sub_agent_spawn' && e.type !== 'sub_agent_complete') return false
    }
    if (filterText) {
      const str = JSON.stringify(e).toLowerCase()
      if (!str.includes(filterText.toLowerCase())) return false
    }
    return true
  })

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(allEvents, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trace-${sessionId || 'unknown'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Activity size={20} className="text-aws-orange" />
          Execution Trace
        </h2>
        <button onClick={handleExport} className="btn-secondary flex items-center gap-1 text-sm">
          <Download size={14} />
          Export JSON
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input-field pl-9"
            placeholder="Filter events..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
        </div>
        <select
          className="input-field w-auto"
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
        >
          <option value="all">All events</option>
          <option value="tools">Tool calls</option>
          <option value="agents">Sub-agents</option>
          <option value="errors">Errors only</option>
        </select>
      </div>

      {/* Trace tree */}
      {filteredEvents.length === 0 ? (
        <div className="card text-center py-12">
          <Activity size={32} className="text-slate-300 mx-auto" />
          <p className="text-sm text-slate-500 mt-3">
            {allEvents.length === 0
              ? 'No execution events yet. Send a message to see the trace.'
              : 'No events match your filter.'}
          </p>
        </div>
      ) : (
        <div className="card space-y-0.5">
          {filteredEvents.map((event, idx) => (
            <TraceEventNode key={idx} event={event} />
          ))}
        </div>
      )}

      <div className="mt-3 text-xs text-slate-400">
        {filteredEvents.length} of {allEvents.length} events
      </div>
    </div>
  )
}

function TraceEventNode({ event }: { event: ExecutionEvent }) {
  const [expanded, setExpanded] = useState(false)

  const { icon, color, label, detail, expandable } = getEventDisplay(event)

  return (
    <div>
      <button
        onClick={() => expandable && setExpanded(!expanded)}
        className={`w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
          expandable ? 'cursor-pointer' : 'cursor-default'
        }`}
      >
        {expandable ? (
          expanded ? <ChevronDown size={12} className="text-slate-400 shrink-0" /> : <ChevronRight size={12} className="text-slate-400 shrink-0" />
        ) : (
          <span className="w-3 shrink-0" />
        )}
        <span className={`shrink-0 ${color}`}>{icon}</span>
        <span className="font-medium truncate">{label}</span>
        {detail && <span className="text-slate-400 text-xs truncate ml-auto">{detail}</span>}
      </button>

      {expanded && (
        <div className="ml-8 mb-2">
          <pre className="text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded overflow-x-auto font-mono max-h-60 overflow-y-auto">
            {JSON.stringify(event, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function getEventDisplay(event: ExecutionEvent): {
  icon: React.ReactNode
  color: string
  label: string
  detail: string
  expandable: boolean
} {
  switch (event.type) {
    case 'message':
      return {
        icon: <MessageSquare size={14} />,
        color: 'text-blue-500',
        label: `Message: ${(event as import('@/types/event').MessageEvent).content.slice(0, 60)}...`,
        detail: '',
        expandable: true,
      }
    case 'tool_use':
      return {
        icon: <Wrench size={14} />,
        color: 'text-blue-500',
        label: `Tool: ${(event as import('@/types/event').ToolUseEvent).tool}`,
        detail: '',
        expandable: true,
      }
    case 'tool_result': {
      const r = event as import('@/types/event').ToolResultEvent
      return {
        icon: r.isError ? <XCircle size={14} /> : <CheckCircle size={14} />,
        color: r.isError ? 'text-red-500' : 'text-green-500',
        label: `Result: ${r.tool}`,
        detail: r.durationMs ? `${r.durationMs}ms` : '',
        expandable: true,
      }
    }
    case 'sub_agent_spawn':
      return {
        icon: <Bot size={14} />,
        color: 'text-purple-500',
        label: `Agent: ${(event as import('@/types/event').SubAgentSpawnEvent).description}`,
        detail: (event as import('@/types/event').SubAgentSpawnEvent).model,
        expandable: true,
      }
    case 'sub_agent_complete':
      return {
        icon: <Bot size={14} />,
        color: 'text-purple-500',
        label: 'Agent complete',
        detail: `${(event as import('@/types/event').SubAgentCompleteEvent).durationMs}ms`,
        expandable: true,
      }
    case 'error':
      return {
        icon: <XCircle size={14} />,
        color: 'text-red-500',
        label: `Error: ${(event as import('@/types/event').ErrorEvent).message}`,
        detail: (event as import('@/types/event').ErrorEvent).recoverable ? 'recoverable' : 'fatal',
        expandable: true,
      }
    case 'permission_request':
      return {
        icon: <ShieldAlert size={14} />,
        color: 'text-amber-500',
        label: `Permission: ${(event as import('@/types/event').PermissionRequestEvent).description}`,
        detail: '',
        expandable: true,
      }
    case 'execution_complete': {
      const ec = event as import('@/types/event').ExecutionCompleteEvent
      return {
        icon: <CheckCircle size={14} />,
        color: 'text-green-500',
        label: 'Execution complete',
        detail: `${ec.toolUseCount} tools, ${ec.subAgentCount} agents, ${ec.durationMs}ms`,
        expandable: true,
      }
    }
    default:
      return {
        icon: <Activity size={14} />,
        color: 'text-slate-400',
        label: event.type,
        detail: '',
        expandable: true,
      }
  }
}
