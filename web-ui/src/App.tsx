import { useState, useCallback, Component, type ReactNode, type ErrorInfo } from 'react'
import type { ViewId } from '@/types/resource'
import { useSession } from '@/hooks/useSession'
import { useSSE } from '@/hooks/useSSE'
import * as api from '@/services/api'

import Sidebar from '@/components/Common/Sidebar'
import Header from '@/components/Common/Header'
import SessionManager from '@/components/SessionManager/SessionManager'
import ChatPanel from '@/components/ChatPanel/ChatPanel'
import CommandBrowser from '@/components/CommandBrowser/CommandBrowser'
import SkillBrowser from '@/components/SkillBrowser/SkillBrowser'
import AgentBrowser from '@/components/AgentBrowser/AgentBrowser'
import ConfigBrowser from '@/components/ConfigBrowser/ConfigBrowser'
import ExecutionTrace from '@/components/ExecutionTrace/ExecutionTrace'
import InfrastructureDiagram from '@/components/InfrastructureDiagram/InfrastructureDiagram'
import ArtifactBrowser from '@/components/ArtifactBrowser/ArtifactBrowser'

// ── Error Boundary ────────────────────────────────────────────

interface ErrorBoundaryProps {
  children: ReactNode
  fallbackView: ViewId
  onReset: (view: ViewId) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ViewErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('View error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center py-12">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <h3 className="font-semibold text-lg mb-2">Something went wrong</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mb-4 font-mono">
            Check the browser console for details
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null })
              this.props.onReset(this.props.fallbackView)
            }}
            className="btn-primary"
          >
            Go to Sessions
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// ── Main App ──────────────────────────────────────────────────

export default function App() {
  const [activeView, setActiveView] = useState<ViewId>('sessions')

  const session = useSession()
  const sse = useSSE(
    session.activeSession?.id ?? null,
    session.handleSessionInfo,
  )

  const handleViewChange = (view: ViewId) => {
    setActiveView(view)
  }

  const handleCreateSession = async () => {
    const created = await session.createSession()
    if (created) setActiveView('chat')
  }

  const handleSelectSession = async (id: string) => {
    await session.selectSession(id)
    setActiveView('chat')
  }

  const handleSendMessage = useCallback(
    async (content: string, command?: string) => {
      if (!session.activeSession) return

      // Append user message to history immediately
      session.appendHistory({
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
        events: [],
      })

      // Stream the response — send() returns { events, text } directly
      // so we don't depend on stale state
      const result = await sse.send(content, command)

      // Append assistant response to history using the returned text
      if (result.text) {
        session.appendHistory({
          role: 'assistant',
          content: result.text,
          timestamp: new Date().toISOString(),
          events: result.events,
        })
      }

      // Clear streaming state now that it's in history
      sse.clear()
    },
    [session, sse],
  )

  const handlePermissionGrant = async (sessionId: string, permissionId: string, granted: boolean) => {
    await api.grantPermission(sessionId, permissionId, granted)
  }

  const handleExecuteCommand = (commandName: string) => {
    setActiveView('chat')
    handleSendMessage(`/aws-coworker ${commandName}`, commandName)
  }

  const renderView = () => {
    switch (activeView) {
      case 'sessions':
        return (
          <SessionManager
            sessions={session.sessions}
            activeSessionId={session.activeSession?.id ?? null}
            onSelect={handleSelectSession}
            onCreate={handleCreateSession}
            onDelete={session.deleteSession}
            onUpdate={session.updateSessionMeta}
          />
        )
      case 'chat':
        return (
          <ChatPanel
            history={session.history}
            streaming={sse.streaming}
            currentText={sse.currentText}
            events={sse.events}
            onSend={handleSendMessage}
            onCancel={sse.cancel}
            onPermissionGrant={handlePermissionGrant}
            sessionId={session.activeSession?.id ?? null}
          />
        )
      case 'commands':
        return <CommandBrowser onExecute={handleExecuteCommand} />
      case 'skills':
        return <SkillBrowser />
      case 'agents':
        return <AgentBrowser />
      case 'config':
        return <ConfigBrowser />
      case 'trace':
        return (
          <ExecutionTrace
            history={session.history}
            sessionId={session.activeSession?.id ?? null}
          />
        )
      case 'infrastructure':
        return (
          <InfrastructureDiagram
            sessionId={session.activeSession?.id ?? null}
          />
        )
      case 'artifacts':
        return (
          <ArtifactBrowser
            sessionId={session.activeSession?.id ?? null}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar
        activeView={activeView}
        onViewChange={handleViewChange}
        sessionActive={!!session.activeSession}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          activeSession={session.activeSession}
          sessions={session.sessions}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onRenameSession={session.renameSession}
        />
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
          <ViewErrorBoundary key={activeView} fallbackView="sessions" onReset={setActiveView}>
            {renderView()}
          </ViewErrorBoundary>
        </main>
      </div>
    </div>
  )
}
