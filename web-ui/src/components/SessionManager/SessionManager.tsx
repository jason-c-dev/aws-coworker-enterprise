import { useState } from 'react'
import { Plus, Trash2, Clock, FolderOpen, Play, Pencil, Check, X, Globe } from 'lucide-react'
import type { SessionSummary } from '@/types/resource'

interface SessionManagerProps {
  sessions: SessionSummary[]
  activeSessionId: string | null
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
  onUpdate?: (id: string, updates: { name?: string; environment?: string }) => void
}

const ENVIRONMENTS = ['', 'sandbox', 'development', 'test', 'staging', 'production'] as const

const envColors: Record<string, string> = {
  sandbox: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
  development: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
  test: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
  staging: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
  production: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
}

export default function SessionManager({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  onDelete,
  onUpdate,
}: SessionManagerProps) {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editEnv, setEditEnv] = useState('')

  const statusColor: Record<string, string> = {
    active: 'bg-green-500',
    idle: 'bg-amber-500',
    closed: 'bg-slate-400',
  }

  const startEditing = (session: SessionSummary, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditName(session.name)
    setEditEnv(session.environment || '')
  }

  const saveEditing = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (editingId && onUpdate) {
      onUpdate(editingId, { name: editName, environment: editEnv })
    }
    setEditingId(null)
  }

  const cancelEditing = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Sessions</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your AWS Coworker conversation sessions
          </p>
        </div>
        <button onClick={onCreate} className="btn-primary flex items-center gap-2">
          <Plus size={16} />
          New Session
        </button>
      </div>

      {sessions.length === 0 ? (
        <div className="card text-center py-12">
          <MessageSquareIcon />
          <p className="text-slate-500 dark:text-slate-400 mt-3">
            No sessions yet. Create one to get started.
          </p>
          <button onClick={onCreate} className="btn-primary mt-4">
            Create Session
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`card flex items-center justify-between group cursor-pointer hover:border-aws-orange/50 transition-colors ${
                activeSessionId === session.id ? 'border-aws-orange ring-1 ring-aws-orange/30' : ''
              }`}
              onClick={() => onSelect(session.id)}
            >
              <div className="min-w-0 flex-1">
                {editingId === session.id ? (
                  /* Inline editing mode */
                  <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${statusColor[session.status] || 'bg-slate-400'}`} />
                      <input
                        className="input-field text-sm font-medium py-1 flex-1"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveEditing(e as unknown as React.MouseEvent)
                          if (e.key === 'Escape') cancelEditing(e as unknown as React.MouseEvent)
                        }}
                      />
                    </div>
                    <div className="flex items-center gap-2 pl-4">
                      <label className="text-xs text-slate-500 dark:text-slate-400">Environment:</label>
                      <select
                        className="input-field text-xs py-1 px-2 w-auto"
                        value={editEnv}
                        onChange={(e) => setEditEnv(e.target.value)}
                      >
                        {ENVIRONMENTS.map((env) => (
                          <option key={env} value={env}>{env || '(none)'}</option>
                        ))}
                      </select>
                      <button onClick={saveEditing} className="btn-primary py-1 px-2 text-xs flex items-center gap-1">
                        <Check size={12} />
                        Save
                      </button>
                      <button onClick={cancelEditing} className="btn-secondary py-1 px-2 text-xs flex items-center gap-1">
                        <X size={12} />
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Normal display mode */
                  <>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${statusColor[session.status] || 'bg-slate-400'}`} />
                      <h3 className="font-medium text-sm truncate">{session.name}</h3>
                    </div>
                    {session.description && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate pl-4">
                        {session.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-2 pl-4 flex-wrap">
                      <span className="badge-gray flex items-center gap-1">
                        <Clock size={10} />
                        {formatRelativeTime(session.lastActivity)}
                      </span>
                      <span className="badge-gray">{session.profile || 'default'}</span>
                      <span className="badge-gray">{session.region || 'us-east-1'}</span>
                      {session.environment && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${envColors[session.environment] || 'badge-gray'}`}>
                          <Globe size={10} />
                          {session.environment}
                        </span>
                      )}
                      {session.artifactCount > 0 && (
                        <span className="badge-purple flex items-center gap-1">
                          <FolderOpen size={10} />
                          {session.artifactCount}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </div>

              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-4">
                {onUpdate && editingId !== session.id && (
                  <button
                    onClick={(e) => startEditing(session, e)}
                    className="btn-ghost p-2"
                    title="Edit session"
                  >
                    <Pencil size={14} />
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); onSelect(session.id) }}
                  className="btn-ghost p-2"
                  title="Open session"
                >
                  <Play size={14} />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setConfirmDelete(session.id)
                  }}
                  className="btn-ghost p-2 text-red-500 hover:text-red-600"
                  title="Delete session"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-96">
            <h3 className="font-semibold mb-2">Delete Session?</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-1">
              This will permanently delete the session and all its artifacts.
            </p>
            {(() => {
              const s = sessions.find((s) => s.id === confirmDelete)
              return s?.artifactCount ? (
                <p className="text-sm text-amber-600 dark:text-amber-400 mb-4">
                  {s.artifactCount} artifact{s.artifactCount > 1 ? 's' : ''} will be deleted.
                </p>
              ) : null
            })()}
            <div className="flex justify-end gap-2 mt-4">
              <button className="btn-secondary" onClick={() => setConfirmDelete(null)}>
                Cancel
              </button>
              <button
                className="btn-danger"
                onClick={() => {
                  onDelete(confirmDelete)
                  setConfirmDelete(null)
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MessageSquareIcon() {
  return (
    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-700">
      <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
      </svg>
    </div>
  )
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}
