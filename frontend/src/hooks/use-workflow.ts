/**
 * Curato AI — useWorkflow Hook
 *
 * Manages workflow state, WebSocket events, and API polling.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  getWorkflowHistory,
  getWorkflowLogs,
  getWorkflowStatus,
  triggerWorkflow,
} from "@/lib/api";
import { CuratoWebSocket } from "@/lib/websocket";
import type {
  GenerationSummary,
  WebSocketEvent,
  WorkflowLogEntry,
  WorkflowStatusResponse,
} from "@/types/workflow";

interface UseWorkflowReturn {
  // State
  sessionId: string | null;
  status: WorkflowStatusResponse | null;
  logs: WorkflowLogEntry[];
  history: GenerationSummary[];
  isTriggering: boolean;
  isRunning: boolean;
  error: string | null;

  // Actions
  trigger: () => Promise<void>;
  refreshStatus: () => Promise<void>;
  refreshHistory: () => Promise<void>;
  clearError: () => void;
}

export function useWorkflow(): UseWorkflowReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<WorkflowStatusResponse | null>(null);
  const [logs, setLogs] = useState<WorkflowLogEntry[]>([]);
  const [history, setHistory] = useState<GenerationSummary[]>([]);
  const [isTriggering, setIsTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<CuratoWebSocket | null>(null);

  const isRunning =
    status !== null &&
    !["completed", "failed", "cancelled"].includes(status.status);

  // ── WebSocket Event Handler ─────────────────────────────────────────
  const handleWSEvent = useCallback(
    (event: WebSocketEvent) => {
      // Update status based on events
      if (
        event.event_type === "agent_started" ||
        event.event_type === "agent_completed" ||
        event.event_type === "agent_failed"
      ) {
        // Refresh full status from API
        if (sessionId) {
          getWorkflowStatus(sessionId).then((res) => {
            if (res.success && res.data) {
              setStatus(res.data);
            }
          });
          getWorkflowLogs(sessionId).then((res) => {
            if (res.success && res.data) {
              setLogs(res.data);
            }
          });
        }
      }

      if (
        event.event_type === "workflow_completed" ||
        event.event_type === "workflow_failed"
      ) {
        if (sessionId) {
          getWorkflowStatus(sessionId).then((res) => {
            if (res.success && res.data) {
              setStatus(res.data);
            }
          });
          getWorkflowLogs(sessionId).then((res) => {
            if (res.success && res.data) {
              setLogs(res.data);
            }
          });
        }
        // Refresh history
        refreshHistory();
      }
    },
    [sessionId]
  );

  // ── WebSocket Connection ────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;

    // Connect WebSocket
    const ws = new CuratoWebSocket(sessionId);
    ws.onEvent(handleWSEvent);
    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [sessionId, handleWSEvent]);

  // ── Trigger Workflow ────────────────────────────────────────────────
  const trigger = useCallback(async () => {
    setIsTriggering(true);
    setError(null);

    try {
      const res = await triggerWorkflow();
      if (res.success && res.data) {
        setSessionId(res.data.session_id);
        setStatus({
          session_id: res.data.session_id,
          status: "pending",
          current_agent: null,
          agents: [],
          started_at: new Date().toISOString(),
          completed_at: null,
          total_duration_ms: null,
          error_message: null,
          retry_count: 0,
        });
        setLogs([]);
      } else {
        setError(res.error || "Failed to trigger workflow");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to trigger workflow");
    } finally {
      setIsTriggering(false);
    }
  }, []);

  // ── Refresh Status ──────────────────────────────────────────────────
  const refreshStatus = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await getWorkflowStatus(sessionId);
      if (res.success && res.data) {
        setStatus(res.data);
      }
    } catch (e) {
      console.error("Failed to refresh status:", e);
    }
  }, [sessionId]);

  // ── Refresh History ─────────────────────────────────────────────────
  const refreshHistory = useCallback(async () => {
    try {
      const res = await getWorkflowHistory();
      if (res.success && res.data) {
        setHistory(res.data.items);
      }
    } catch (e) {
      console.error("Failed to refresh history:", e);
    }
  }, []);

  // Load history on mount
  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  const clearError = useCallback(() => setError(null), []);

  return {
    sessionId,
    status,
    logs,
    history,
    isTriggering,
    isRunning,
    error,
    trigger,
    refreshStatus,
    refreshHistory,
    clearError,
  };
}
