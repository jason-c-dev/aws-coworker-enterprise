import { useState, useCallback, useEffect } from 'react'
import type { SessionSummary, SessionDetail, HistoryEntry } from '@/types/resource'
import type { ExecutionEvent } from '@/types/event'
import * as api from '@/services/api'

export interface SessionState {
  sessions: SessionSummary[]
  activeSession: SessionDetail | null
  history: HistoryEntry[]
  loading: boolean
  error: string | null
}

export function useSession() {
  const [state, setState] = useState<SessionState>({
    sessions: [],
    activeSession: null,
    history: [],
    loading: false,
    error: null,
  })

  const setError = (error: string | null) => setState((s) => ({ ...s, error }))
  const setLoading = (loading: boolean) => setState((s) => ({ ...s, loading }))

  const refreshSessions = useCallback(async () => {
    try {
      const sessions = await api.listSessions()
      setState((s) => ({ ...s, sessions }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
    }
  }, [])

  const createSession = useCallback(async (payload: api.CreateSessionPayload = {}) => {
    setLoading(true)
    try {
      const session = await api.createSession(payload)
      setState((s) => ({
        ...s,
        sessions: [{ ...session, artifactCount: 0 }, ...s.sessions],
        activeSession: session,
        history: [],
        loading: false,
        error: null,
      }))
      return session
    } catch (err: unknown) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'Failed to create session')
      return null
    }
  }, [])

  const selectSession = useCallback(async (id: string) => {
    setLoading(true)
    try {
      const [session, history] = await Promise.all([
        api.getSession(id),
        api.getHistory(id),
      ])
      setState((s) => ({ ...s, activeSession: session, history, loading: false, error: null }))
    } catch (err: unknown) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'Failed to load session')
    }
  }, [])

  const renameSession = useCallback(async (id: string, name: string, description?: string) => {
    try {
      const updated = await api.updateSession(id, { name, description })
      setState((s) => ({
        ...s,
        activeSession: s.activeSession?.id === id ? updated : s.activeSession,
        sessions: s.sessions.map((sess) =>
          sess.id === id ? { ...sess, name: updated.name, description: updated.description } : sess,
        ),
      }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to rename session')
    }
  }, [])

  const updateSessionMeta = useCallback(async (id: string, updates: { name?: string; environment?: string }) => {
    try {
      const updated = await api.updateSession(id, updates)
      setState((s) => ({
        ...s,
        activeSession: s.activeSession?.id === id ? updated : s.activeSession,
        sessions: s.sessions.map((sess) =>
          sess.id === id ? { ...sess, ...updates } : sess,
        ),
      }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update session')
    }
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    try {
      await api.deleteSession(id)
      setState((s) => ({
        ...s,
        sessions: s.sessions.filter((sess) => sess.id !== id),
        activeSession: s.activeSession?.id === id ? null : s.activeSession,
        history: s.activeSession?.id === id ? [] : s.history,
      }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete session')
    }
  }, [])

  /** Append a history entry locally (used after streaming completes) */
  const appendHistory = useCallback((entry: HistoryEntry) => {
    setState((s) => ({ ...s, history: [...s.history, entry] }))
  }, [])

  /** Update session name from a session_info event */
  const handleSessionInfo = useCallback((suggestedName?: string, suggestedDescription?: string) => {
    setState((s) => {
      if (!s.activeSession) return s
      const updated = { ...s.activeSession }
      if (suggestedName) updated.name = suggestedName
      if (suggestedDescription) updated.description = suggestedDescription
      return {
        ...s,
        activeSession: updated,
        sessions: s.sessions.map((sess) =>
          sess.id === updated.id ? { ...sess, name: updated.name, description: updated.description } : sess,
        ),
      }
    })
  }, [])

  // Load sessions on mount
  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  return {
    ...state,
    refreshSessions,
    createSession,
    selectSession,
    renameSession,
    updateSessionMeta,
    deleteSession,
    appendHistory,
    handleSessionInfo,
  }
}
