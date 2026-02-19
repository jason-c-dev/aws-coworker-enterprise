/** Resource types for commands, skills, agents, config */

export interface CommandSummary {
  name: string
  description: string
  agent: string
  skills: string[]
  tools: string[]
}

export interface ResourceDetail {
  id: string
  name: string
  category: string
  metadata: Record<string, unknown>
  content: string
}

export interface SkillTreeNode {
  name: string
  type: 'directory' | 'file'
  path: string
  children?: SkillTreeNode[]
}

export interface AgentSummary {
  id: string
  name: string
  content: string
}

export interface ConfigSection {
  section: string
  metadata: Record<string, unknown>
  content: string
  fileType: 'markdown' | 'yaml'
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/** Session types */
export type SessionStatus = 'active' | 'idle' | 'closed'
export type ArtifactSource = 'model-generated' | 'user-uploaded' | 'system-exported'

export interface SessionSummary {
  id: string
  name: string
  description: string
  status: SessionStatus
  profile: string
  region: string
  environment: string
  created: string
  lastActivity: string
  artifactCount: number
}

export interface SessionDetail extends SessionSummary {
  messageCount: number
}

export interface ArtifactSummary {
  id: string
  name: string
  mimeType: string
  size: number
  source: ArtifactSource
  created: string
}

export interface HistoryEntry {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  events: import('./event').ExecutionEvent[]
}

export interface DiagramRequest {
  type: 'architecture' | 'flowchart' | 'sequence'
  format?: 'mermaid' | 'reactflow'
  resources: Record<string, unknown>
}

export interface DiagramResponse {
  type: string
  format: string
  content: string
  artifactId?: string
}

/** View identifiers for sidebar navigation */
export type ViewId =
  | 'sessions'
  | 'chat'
  | 'commands'
  | 'skills'
  | 'agents'
  | 'config'
  | 'trace'
  | 'infrastructure'
  | 'artifacts'
