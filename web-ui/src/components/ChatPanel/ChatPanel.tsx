import { useState, useRef, useEffect } from 'react'
import { Send, Square, Wrench, Bot as BotIcon, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import type { HistoryEntry } from '@/types/resource'
import type { ExecutionEvent } from '@/types/event'
import EventBadges from './EventBadges'
import PermissionBanner from './PermissionBanner'

interface ChatPanelProps {
  history: HistoryEntry[]
  streaming: boolean
  currentText: string
  events: ExecutionEvent[]
  onSend: (content: string, command?: string) => void
  onCancel: () => void
  onPermissionGrant: (sessionId: string, permissionId: string, granted: boolean) => void
  sessionId: string | null
}

export default function ChatPanel({
  history,
  streaming,
  currentText,
  events,
  onSend,
  onCancel,
  onPermissionGrant,
  sessionId,
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, currentText])

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || streaming) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Find pending permission requests in current stream
  const pendingPermissions = events.filter(
    (e) => e.type === 'permission_request',
  ) as import('@/types/event').PermissionRequestEvent[]

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {history.map((entry, idx) => (
          <MessageBubble key={idx} entry={entry} />
        ))}

        {/* Streaming response */}
        {streaming && currentText && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-aws-orange/20 flex items-center justify-center shrink-0 mt-1">
              <BotIcon size={14} className="text-aws-orange" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                {currentText}
                <span className="inline-block w-2 h-4 bg-aws-orange animate-pulse ml-0.5" />
              </div>
              {events.length > 0 && <EventBadges events={events} />}
            </div>
          </div>
        )}

        {/* Permission requests */}
        {pendingPermissions.map((perm) => (
          <PermissionBanner
            key={perm.permissionId}
            permission={perm}
            onGrant={(granted) =>
              sessionId && onPermissionGrant(sessionId, perm.permissionId, granted)
            }
          />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-slate-200 dark:border-slate-700 p-4">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={sessionId ? 'Ask AWS Coworker...' : 'Select or create a session first'}
            disabled={!sessionId}
            className="input-field resize-none min-h-[40px] max-h-40"
            rows={1}
          />
          {streaming ? (
            <button onClick={onCancel} className="btn-secondary p-2.5 shrink-0" title="Stop">
              <Square size={16} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || !sessionId}
              className="btn-primary p-2.5 shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Send"
            >
              <Send size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ entry }: { entry: HistoryEntry }) {
  const isUser = entry.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-aws-orange/20 flex items-center justify-center shrink-0 mt-1">
          <BotIcon size={14} className="text-aws-orange" />
        </div>
      )}
      <div className={`max-w-[80%] min-w-0 ${isUser ? 'order-first' : ''}`}>
        <div
          className={`rounded-lg px-3 py-2 text-sm ${
            isUser
              ? 'bg-aws-orange text-white ml-auto'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100'
          }`}
        >
          <div className="whitespace-pre-wrap">{entry.content}</div>
        </div>
        {!isUser && entry.events && entry.events.length > 0 && (
          <EventBadges events={entry.events} />
        )}
      </div>
    </div>
  )
}
