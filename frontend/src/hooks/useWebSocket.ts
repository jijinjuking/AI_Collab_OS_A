import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '@/store/auth'
import { useMessageStore } from '@/store/message'

export interface WSMessage {
  type: string
  data: Record<string, unknown>
  timestamp: string
}

type MessageHandler = (msg: WSMessage) => void

const MAX_RECONNECT_DELAY = 30000
const INITIAL_RECONNECT_DELAY = 1000
const MAX_RETRIES = 10

/**
 * WebSocket hook for real-time project communication.
 * Features: JWT auth, exponential backoff reconnect, connection status.
 */
export function useWebSocket(projectId: string | undefined, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const retriesRef = useRef(0)
  const delayRef = useRef(INITIAL_RECONNECT_DELAY)
  const token = useAuthStore((s) => s.token)
  const setConnected = useMessageStore((s) => s.setConnected)

  const connect = useCallback(() => {
    if (!projectId || !token) return

    // Don't connect if already open or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/${projectId}?token=${token}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`[WS] Connected to project ${projectId}`)
      setConnected(true)
      // Reset backoff on successful connection
      retriesRef.current = 0
      delayRef.current = INITIAL_RECONNECT_DELAY
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        onMessage(msg)
      } catch (e) {
        console.warn('[WS] Failed to parse message:', event.data)
      }
    }

    ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code=${event.code})`)
      wsRef.current = null
      setConnected(false)

      // Don't reconnect on intentional close or auth failure
      if (event.code === 1000 || event.code === 4001) return

      // Exponential backoff reconnect
      if (retriesRef.current < MAX_RETRIES) {
        retriesRef.current++
        const jitter = Math.random() * 500
        const delay = Math.min(delayRef.current + jitter, MAX_RECONNECT_DELAY)
        console.log(`[WS] Reconnecting in ${Math.round(delay)}ms (attempt ${retriesRef.current}/${MAX_RETRIES})`)
        reconnectTimer.current = setTimeout(connect, delay)
        delayRef.current = Math.min(delayRef.current * 2, MAX_RECONNECT_DELAY)
      } else {
        console.error('[WS] Max reconnection attempts reached')
      }
    }

    ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }, [projectId, token, onMessage, setConnected])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.close(1000)
        wsRef.current = null
      }
      setConnected(false)
    }
  }, [connect, setConnected])

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const reconnect = useCallback(() => {
    retriesRef.current = 0
    delayRef.current = INITIAL_RECONNECT_DELAY
    if (wsRef.current) {
      wsRef.current.close(1000)
      wsRef.current = null
    }
    connect()
  }, [connect])

  return { send, reconnect }
}
