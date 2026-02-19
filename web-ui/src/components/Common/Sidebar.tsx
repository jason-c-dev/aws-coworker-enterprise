import {
  MessageSquare,
  Terminal,
  BookOpen,
  Bot,
  Settings,
  Activity,
  Network,
  FolderOpen,
  LayoutDashboard,
} from 'lucide-react'
import type { ViewId } from '@/types/resource'

const NAV_ITEMS: { id: ViewId; label: string; icon: React.ElementType }[] = [
  { id: 'sessions', label: 'Sessions', icon: LayoutDashboard },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'commands', label: 'Commands', icon: Terminal },
  { id: 'skills', label: 'Skills', icon: BookOpen },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'config', label: 'Config', icon: Settings },
  { id: 'trace', label: 'Trace', icon: Activity },
  { id: 'infrastructure', label: 'Infrastructure', icon: Network },
  { id: 'artifacts', label: 'Artifacts', icon: FolderOpen },
]

interface SidebarProps {
  activeView: ViewId
  onViewChange: (view: ViewId) => void
  sessionActive: boolean
}

export default function Sidebar({ activeView, onViewChange, sessionActive }: SidebarProps) {
  return (
    <aside className="w-56 bg-white dark:bg-aws-navy-deep border-r border-slate-200 dark:border-transparent flex flex-col h-full shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-slate-200 dark:border-white/10">
        <h1 className="text-slate-900 dark:text-white font-semibold text-base tracking-tight">
          AWS Coworker
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs mt-0.5">Developer Workbench</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const disabled = id !== 'sessions' && !sessionActive
          return (
            <button
              key={id}
              onClick={() => !disabled && onViewChange(id)}
              className={`sidebar-item w-full ${
                activeView === id ? 'active' : ''
              } ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
              disabled={disabled}
              title={disabled ? 'Select a session first' : label}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-200 dark:border-white/10">
        <p className="text-slate-400 dark:text-slate-500 text-xs">v0.1.0</p>
      </div>
    </aside>
  )
}
