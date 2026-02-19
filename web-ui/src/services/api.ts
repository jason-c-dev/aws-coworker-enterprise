/**
 * REST + SSE client for the ACW Server API.
 */

const BASE = ''  // Same origin via Vite proxy in dev, served from FastAPI in prod

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body}`)
  }
  return res.json()
}

// ── Health ──────────────────────────────────────────────────────

export const ping = () => request<{ status: string }>('/ping')

// ── Sessions ────────────────────────────────────────────────────

export interface CreateSessionPayload {
  name?: string
  profile?: string
  region?: string
  environment?: string
}

export const createSession = (payload: CreateSessionPayload = {}) =>
  request<import('@/types/resource').SessionDetail>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const listSessions = () =>
  request<import('@/types/resource').SessionSummary[]>('/api/sessions')

export const getSession = (id: string) =>
  request<import('@/types/resource').SessionDetail>(`/api/sessions/${id}`)

export const updateSession = (id: string, payload: { name?: string; description?: string; environment?: string }) =>
  request<import('@/types/resource').SessionDetail>(`/api/sessions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const deleteSession = (id: string) =>
  request<{ id: string; artifactsDeleted: number }>(`/api/sessions/${id}`, { method: 'DELETE' })

// ── Messages ────────────────────────────────────────────────────

export const sendMessage = (sessionId: string, content: string, command?: string) =>
  request<{ role: string; content: string; events: unknown[] }>(
    `/api/sessions/${sessionId}/messages`,
    { method: 'POST', body: JSON.stringify({ content, command }) },
  )

/**
 * Send a message and get an SSE stream back.
 * Returns an EventSource-like reader — caller is responsible for closing.
 */
export function streamMessage(
  sessionId: string,
  content: string,
  command?: string,
  onEvent?: (eventType: string, data: unknown) => void,
  onDone?: () => void,
  onError?: (err: Error) => void,
): AbortController {
  const controller = new AbortController()

  fetch(`${BASE}/api/sessions/${sessionId}/messages/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, command }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`Stream error: ${res.status}`)
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // Parse SSE lines
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = 'message'
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim())
              onEvent?.(currentEvent, data)
            } catch {
              // Non-JSON data line
              onEvent?.(currentEvent, line.slice(5).trim())
            }
          }
        }
      }
      onDone?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError?.(err)
    })

  return controller
}

export const getHistory = (sessionId: string) =>
  request<import('@/types/resource').HistoryEntry[]>(`/api/sessions/${sessionId}/history`)

// ── Permissions ─────────────────────────────────────────────────

export const grantPermission = (sessionId: string, permissionId: string, granted: boolean) =>
  request<{ status: string }>(`/api/sessions/${sessionId}/permissions/${permissionId}`, {
    method: 'POST',
    body: JSON.stringify({ granted }),
  })

// ── Resources ───────────────────────────────────────────────────

export const listCommands = () =>
  request<import('@/types/resource').CommandSummary[]>('/api/commands')

export const getCommand = (name: string) =>
  request<import('@/types/resource').ResourceDetail>(`/api/commands/${name}`)

export const updateCommand = (name: string, payload: { metadata?: Record<string, unknown>; content?: string }) =>
  request<import('@/types/resource').ResourceDetail>(`/api/commands/${name}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const listSkills = () =>
  request<import('@/types/resource').SkillTreeNode[]>('/api/skills')

export const getSkill = (path: string) =>
  request<import('@/types/resource').ResourceDetail>(`/api/skills/${path}`)

export const updateSkill = (path: string, payload: { metadata?: Record<string, unknown>; content?: string }) =>
  request<import('@/types/resource').ResourceDetail>(`/api/skills/${path}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const listAgents = () =>
  request<import('@/types/resource').AgentSummary[]>('/api/agents')

export const getAgent = (name: string) =>
  request<import('@/types/resource').ResourceDetail>(`/api/agents/${name}`)

export const updateAgent = (name: string, payload: { metadata?: Record<string, unknown>; content?: string }) =>
  request<import('@/types/resource').ResourceDetail>(`/api/agents/${name}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const listConfig = () =>
  request<import('@/types/resource').ConfigSection[]>('/api/config')

export const getConfig = (name: string) =>
  request<import('@/types/resource').ConfigSection>(`/api/config/${name}`)

export const updateConfig = (name: string, body: { content: string }) =>
  request<import('@/types/resource').ConfigSection>(`/api/config/${name}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

// ── Artifacts ───────────────────────────────────────────────────

export const listArtifacts = (sessionId: string) =>
  request<import('@/types/resource').ArtifactSummary[]>(`/api/sessions/${sessionId}/artifacts`)

export const deleteArtifact = (sessionId: string, artifactId: string) =>
  request<{ status: string }>(`/api/sessions/${sessionId}/artifacts/${artifactId}`, {
    method: 'DELETE',
  })

export function getArtifactUrl(sessionId: string, artifactId: string): string {
  return `${BASE}/api/sessions/${sessionId}/artifacts/${artifactId}`
}

// ── Diagrams ────────────────────────────────────────────────────

export const generateDiagram = (payload: import('@/types/resource').DiagramRequest) =>
  request<import('@/types/resource').DiagramResponse>('/api/diagrams/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

// ── Observability ───────────────────────────────────────────────

export const getTrace = (sessionId: string) =>
  request<unknown[]>(`/api/sessions/${sessionId}/trace`)

export const getLogs = (sessionId: string, params?: { level?: string; source?: string; keyword?: string }) => {
  const search = new URLSearchParams()
  if (params?.level) search.set('level', params.level)
  if (params?.source) search.set('source', params.source)
  if (params?.keyword) search.set('keyword', params.keyword)
  const qs = search.toString()
  return request<unknown[]>(`/api/sessions/${sessionId}/logs${qs ? `?${qs}` : ''}`)
}
