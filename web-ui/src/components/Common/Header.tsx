import { useState } from 'react'
import { ChevronDown, Plus } from 'lucide-react'
import ThemeToggle from './ThemeToggle'
import type { SessionSummary, SessionDetail } from '@/types/resource'

interface HeaderProps {
  activeSession: SessionDetail | null
  sessions: SessionSummary[]
  onSelectSession: (id: string) => void
  onCreateSession: () => void
  onRenameSession: (id: string, name: string) => void
}

export default function Header({
  activeSession,
  sessions,
  onSelectSession,
  onCreateSession,
  onRenameSession,
}: HeaderProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState('')

  const startRename = () => {
    if (!activeSession) return
    setEditName(activeSession.name)
    setEditing(true)
  }

  const commitRename = () => {
    if (activeSession && editName.trim()) {
      onRenameSession(activeSession.id, editName.trim())
    }
    setEditing(false)
  }

  return (
    <header className="h-12 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-4 shrink-0">
      {/* Left: session name + profile */}
      <div className="flex items-center gap-3 min-w-0">
        {activeSession ? (
          <>
            {editing ? (
              <input
                className="input-field text-sm py-1 w-64"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={commitRename}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') commitRename()
                  if (e.key === 'Escape') setEditing(false)
                }}
                autoFocus
              />
            ) : (
              <button
                onClick={startRename}
                className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate max-w-xs hover:text-aws-orange transition-colors"
                title="Click to rename"
              >
                {activeSession.name}
              </button>
            )}
            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span className="badge-gray">{activeSession.profile || 'default'}</span>
              <span className="badge-gray">{activeSession.region || 'us-east-1'}</span>
              <span className="badge-gray">{activeSession.environment || 'development'}</span>
            </div>
          </>
        ) : (
          <span className="text-sm text-slate-500 dark:text-slate-400">No session selected</span>
        )}
      </div>

      {/* Right: session switcher + theme */}
      <div className="flex items-center gap-2">
        {/* Session switcher dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="btn-ghost flex items-center gap-1 text-sm"
          >
            Sessions
            <ChevronDown size={14} />
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-20 py-1 max-h-80 overflow-y-auto">
                <button
                  onClick={() => { onCreateSession(); setDropdownOpen(false) }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-aws-orange hover:bg-slate-50 dark:hover:bg-slate-700"
                >
                  <Plus size={14} />
                  New Session
                </button>
                <div className="border-t border-slate-200 dark:border-slate-700 my-1" />
                {sessions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => { onSelectSession(s.id); setDropdownOpen(false) }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 ${
                      activeSession?.id === s.id ? 'bg-aws-orange/10 text-aws-orange' : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="font-medium truncate">{s.name}</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {s.status} &middot; {s.artifactCount} artifacts
                    </div>
                  </button>
                ))}
                {sessions.length === 0 && (
                  <p className="px-3 py-2 text-xs text-slate-400">No sessions yet</p>
                )}
              </div>
            </>
          )}
        </div>

        <ThemeToggle />
      </div>
    </header>
  )
}
