/**
 * Curato AI — REST API Client
 */

import { siteConfig } from "@/config/site";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type {
  GenerationSummary,
  WorkflowLogEntry,
  WorkflowStatusResponse,
  WorkflowTriggerResponse,
} from "@/types/workflow";

const API_BASE = `${siteConfig.api.baseUrl}/api/v1`;

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(error.message || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Workflow API ──────────────────────────────────────────────────────────

export async function triggerWorkflow(): Promise<
  ApiResponse<WorkflowTriggerResponse>
> {
  return fetchApi("/workflow/trigger", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getWorkflowStatus(
  sessionId: string
): Promise<ApiResponse<WorkflowStatusResponse>> {
  return fetchApi(`/workflow/${sessionId}/status`);
}

export async function getWorkflowLogs(
  sessionId: string,
  limit = 100
): Promise<ApiResponse<WorkflowLogEntry[]>> {
  return fetchApi(`/workflow/${sessionId}/logs?limit=${limit}`);
}

export async function getWorkflowHistory(
  page = 1,
  pageSize = 20
): Promise<ApiResponse<PaginatedResponse<GenerationSummary>>> {
  return fetchApi(`/workflow/history?page=${page}&page_size=${pageSize}`);
}

// ── Generations API ──────────────────────────────────────────────────────

export async function getGenerationDetail(sessionId: string): Promise<ApiResponse<unknown>> {
  return fetchApi(`/generations/${sessionId}`);
}
