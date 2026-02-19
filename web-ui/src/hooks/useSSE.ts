import { useState, useCallback, useRef } from 'react'
import type { ExecutionEvent } from '@/types/event'
import { streamMessage } from '@/services/api'

export interface SSEState {
  streaming: boolean
  events: ExecutionEvent[]
  currentText: string
}

export interface SSEResult {
  events: ExecutionEvent[]
  text: string
}

export function useSSE(
  sessionId: string | null,
  onSessionInfo?: (name?: string, description?: string) => void,
) {
  const [state, setState] = useState<SSEState>({
    streaming: false,
    events: [],
    currentText: '',
  })

  const controllerRef = useRef<AbortController | null>(null)

  const send = useCallback(
    (content: string, command?: string): Promise<SSEResult> => {
      if (!sessionId) return Promise.resolve({ events: [], text: '' })

      return new Promise((resolve) => {
        const events: ExecutionEvent[] = []
        let text = ''

        setState({ streaming: true, events: [], currentText: '' })

        controllerRef.current = streamMessage(
          sessionId,
          content,
          command,
          (eventType: string, data: unknown) => {
            const event = data as ExecutionEvent
            events.push(event)

            if (eventType === 'message' || event.type === 'message') {
              const msg = event as import('@/types/event').MessageEvent
              text += msg.content
              setState((s) => ({
                ...s,
                events: [...events],
                currentText: text,
              }))
            } else if (event.type === 'session_info') {
              const info = event as import('@/types/event').SessionInfoEvent
              onSessionInfo?.(info.suggestedName, info.suggestedDescription)
              setState((s) => ({ ...s, events: [...events] }))
            } else {
              setState((s) => ({ ...s, events: [...events] }))
            }
          },
          () => {
            // Keep the final text visible — don't clear it
            setState((s) => ({ ...s, streaming: false }))
            resolve({ events, text })
          },
          (err) => {
            setState((s) => ({ ...s, streaming: false }))
            events.push({
              id: crypto.randomUUID(),
              type: 'error',
              timestamp: new Date().toISOString(),
              message: err.message,
              recoverable: false,
            } as import('@/types/event').ErrorEvent)
            resolve({ events, text })
          },
        )
      })
    },
    [sessionId, onSessionInfo],
  )

  const cancel = useCallback(() => {
    controllerRef.current?.abort()
    setState((s) => ({ ...s, streaming: false }))
  }, [])

  /** Clear the streaming state (call after appending to history) */
  const clear = useCallback(() => {
    setState({ streaming: false, events: [], currentText: '' })
  }, [])

  return {
    ...state,
    send,
    cancel,
    clear,
  }
}
