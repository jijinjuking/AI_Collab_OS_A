import { create } from 'zustand'
import type { WSMessage } from '@/hooks/useWebSocket'

export interface ChatMessage {
  id: string
  type: 'agent_message' | 'agent_status' | 'workflow_event' | 'system'
  fromAgent: string | null
  fromAgentName: string | null
  toAgent: string | null
  content: string
  timestamp: string
  metadata: Record<string, unknown>
}

export interface AgentStatus {
  agentId: string
  status: 'idle' | 'working' | 'error'
}

interface MessageState {
  messages: ChatMessage[]
  agentStatuses: Map<string, AgentStatus>
  connected: boolean

  addMessage: (msg: ChatMessage) => void
  handleWSMessage: (wsMsg: WSMessage) => void
  setConnected: (val: boolean) => void
  clearMessages: () => void
}

let msgCounter = 0

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  agentStatuses: new Map(),
  connected: false,

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  handleWSMessage: (wsMsg: WSMessage) => {
    const { type, data } = wsMsg
    msgCounter++

    if (type === 'agent_message') {
      const msg: ChatMessage = {
        id: `msg_${msgCounter}_${Date.now()}`,
        type: 'agent_message',
        fromAgent: (data.from_agent as string) || null,
        fromAgentName: (data.agent_name as string) || null,
        toAgent: (data.to_agent as string) || null,
        content: (data.content as string) || '',
        timestamp: wsMsg.timestamp || new Date().toISOString(),
        metadata: {
          messageType: data.message_type,
          nodeId: data.node_id,
          verdict: data.verdict,
          reviewRound: data.review_round,
        },
      }
      set((state) => ({ messages: [...state.messages, msg] }))
    } else if (type === 'agent_status') {
      const agentId = data.agent_id as string
      const status = data.status as 'idle' | 'working' | 'error'
      set((state) => {
        const newStatuses = new Map(state.agentStatuses)
        newStatuses.set(agentId, { agentId, status })
        return { agentStatuses: newStatuses }
      })
    } else if (type === 'workflow_event') {
      const msg: ChatMessage = {
        id: `msg_${msgCounter}_${Date.now()}`,
        type: 'workflow_event',
        fromAgent: null,
        fromAgentName: null,
        toAgent: null,
        content: `工作流 ${data.event}: ${data.workflow_id || ''}`,
        timestamp: wsMsg.timestamp || new Date().toISOString(),
        metadata: data,
      }
      set((state) => ({ messages: [...state.messages, msg] }))
    }
  },

  setConnected: (val) => set({ connected: val }),
  clearMessages: () => set({ messages: [] }),
}))
