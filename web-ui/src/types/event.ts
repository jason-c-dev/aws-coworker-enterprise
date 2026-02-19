/** SSE event types — mirrors ACW Server EventType enum */
export type EventType =
  | 'message'
  | 'tool_use'
  | 'tool_result'
  | 'sub_agent_spawn'
  | 'sub_agent_event'
  | 'sub_agent_complete'
  | 'permission_request'
  | 'permission_grant'
  | 'error'
  | 'todo_update'
  | 'session_info'
  | 'execution_complete'

export interface BaseEvent {
  id: string
  type: EventType
  timestamp: string
}

export interface MessageEvent extends BaseEvent {
  type: 'message'
  content: string
  role: 'assistant' | 'system'
}

export interface ToolUseEvent extends BaseEvent {
  type: 'tool_use'
  tool: string
  input: Record<string, unknown>
}

export interface ToolResultEvent extends BaseEvent {
  type: 'tool_result'
  tool: string
  output: string
  isError: boolean
  durationMs?: number
}

export interface SubAgentSpawnEvent extends BaseEvent {
  type: 'sub_agent_spawn'
  agentId: string
  description: string
  model: string
}

export interface SubAgentEvent extends BaseEvent {
  type: 'sub_agent_event'
  agentId: string
  event: ExecutionEvent
}

export interface SubAgentCompleteEvent extends BaseEvent {
  type: 'sub_agent_complete'
  agentId: string
  result: string
  durationMs: number
}

export interface PermissionRequestEvent extends BaseEvent {
  type: 'permission_request'
  permissionId: string
  tool: string
  description: string
  blastRadius?: string
}

export interface PermissionGrantEvent extends BaseEvent {
  type: 'permission_grant'
  permissionId: string
  granted: boolean
}

export interface ErrorEvent extends BaseEvent {
  type: 'error'
  message: string
  recoverable: boolean
  code?: string
}

export interface TodoUpdateEvent extends BaseEvent {
  type: 'todo_update'
  todos: Array<{ content: string; status: string }>
}

export interface SessionInfoEvent extends BaseEvent {
  type: 'session_info'
  suggestedName?: string
  suggestedDescription?: string
}

export interface ExecutionCompleteEvent extends BaseEvent {
  type: 'execution_complete'
  summary: string
  toolUseCount: number
  subAgentCount: number
  errorCount: number
  durationMs: number
}

export type ExecutionEvent =
  | MessageEvent
  | ToolUseEvent
  | ToolResultEvent
  | SubAgentSpawnEvent
  | SubAgentEvent
  | SubAgentCompleteEvent
  | PermissionRequestEvent
  | PermissionGrantEvent
  | ErrorEvent
  | TodoUpdateEvent
  | SessionInfoEvent
  | ExecutionCompleteEvent

/** Parsed tree node for the execution trace viewer */
export interface TraceNode {
  event: ExecutionEvent
  children: TraceNode[]
  expanded: boolean
}
