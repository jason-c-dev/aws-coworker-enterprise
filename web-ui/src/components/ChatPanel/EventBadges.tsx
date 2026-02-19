import { useState } from 'react'
import { Wrench, Bot as BotIcon, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react'
import type { ExecutionEvent } from '@/types/event'

interface EventBadgesProps {
  events: ExecutionEvent[]
}

export default function EventBadges({ events }: EventBadgesProps) {
  const [expanded, setExpanded] = useState(false)

  const toolUses = events.filter((e) => e.type === 'tool_use').length
  const subAgents = events.filter((e) => e.type === 'sub_agent_spawn').length
  const errors = events.filter((e) => e.type === 'error').length

  if (toolUses === 0 && subAgents === 0 && errors === 0) return null

  return (
    <div className="mt-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        {toolUses > 0 && (
          <span className="badge-blue">
            <Wrench size={10} className="mr-1" />
            {toolUses} tool{toolUses > 1 ? 's' : ''}
          </span>
        )}
        {subAgents > 0 && (
          <span className="badge-purple">
            <BotIcon size={10} className="mr-1" />
            {subAgents} agent{subAgents > 1 ? 's' : ''}
          </span>
        )}
        {errors > 0 && (
          <span className="badge-red">
            <AlertTriangle size={10} className="mr-1" />
            {errors} error{errors > 1 ? 's' : ''}
          </span>
        )}
      </button>

      {expanded && (
        <div className="mt-2 pl-3 border-l-2 border-slate-200 dark:border-slate-600 space-y-1.5">
          {events
            .filter((e) => ['tool_use', 'tool_result', 'sub_agent_spawn', 'sub_agent_complete', 'error'].includes(e.type))
            .map((event, idx) => (
              <EventLine key={idx} event={event} />
            ))}
        </div>
      )}
    </div>
  )
}

function EventLine({ event }: { event: ExecutionEvent }) {
  const [open, setOpen] = useState(false)

  if (event.type === 'tool_use') {
    const e = event as import('@/types/event').ToolUseEvent
    return (
      <div>
        <button onClick={() => setOpen(!open)} className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline">
          <Wrench size={11} />
          {e.tool}
        </button>
        {open && (
          <pre className="mt-1 text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded overflow-x-auto font-mono">
            {JSON.stringify(e.input, null, 2)}
          </pre>
        )}
      </div>
    )
  }

  if (event.type === 'tool_result') {
    const e = event as import('@/types/event').ToolResultEvent
    return (
      <div>
        <button onClick={() => setOpen(!open)} className={`flex items-center gap-1.5 text-xs ${e.isError ? 'text-red-500' : 'text-green-600 dark:text-green-400'}`}>
          {e.isError ? <AlertTriangle size={11} /> : <Wrench size={11} />}
          {e.tool} result {e.durationMs ? `(${e.durationMs}ms)` : ''}
        </button>
        {open && (
          <pre className="mt-1 text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded overflow-x-auto font-mono max-h-40 overflow-y-auto">
            {e.output}
          </pre>
        )}
      </div>
    )
  }

  if (event.type === 'sub_agent_spawn') {
    const e = event as import('@/types/event').SubAgentSpawnEvent
    return (
      <div className="flex items-center gap-1.5 text-xs text-purple-600 dark:text-purple-400">
        <BotIcon size={11} />
        Sub-agent: {e.description} ({e.model})
      </div>
    )
  }

  if (event.type === 'sub_agent_complete') {
    const e = event as import('@/types/event').SubAgentCompleteEvent
    return (
      <div className="flex items-center gap-1.5 text-xs text-purple-600 dark:text-purple-400">
        <BotIcon size={11} />
        Agent done ({e.durationMs}ms)
      </div>
    )
  }

  if (event.type === 'error') {
    const e = event as import('@/types/event').ErrorEvent
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-500">
        <AlertTriangle size={11} />
        {e.message}
      </div>
    )
  }

  return null
}
