/**
 * Curato AI — TypeScript Types: Workflow
 */

export type WorkflowStatus =
  | "pending"
  | "running"
  | "agent_executing"
  | "awaiting_approval"
  | "revision_loop"
  | "approved"
  | "generating_output"
  | "completed"
  | "failed"
  | "cancelled";

export interface WorkflowTriggerResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface AgentStatusDetail {
  agent_name: string;
  status: string;
  duration_ms: number | null;
  attempt_number: number;
  error: string | null;
}

export interface WorkflowStatusResponse {
  session_id: string;
  status: WorkflowStatus;
  current_agent: string | null;
  agents: AgentStatusDetail[];
  started_at: string | null;
  completed_at: string | null;
  total_duration_ms: number | null;
  error_message: string | null;
  retry_count: number;
}

export interface WorkflowLogEntry {
  id: string;
  level: string;
  agent_name: string | null;
  message: string;
  details: Record<string, unknown> | null;
  timestamp: string;
}

export interface GenerationSummary {
  id: string;
  status: WorkflowStatus;
  current_agent: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_duration_ms: number | null;
  retry_count: number;
  created_at: string;
}

export interface WebSocketEvent {
  event_type: string;
  session_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}
