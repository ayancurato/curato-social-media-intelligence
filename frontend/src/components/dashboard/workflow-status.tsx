/**
 * Curato AI — Workflow Status Pipeline Visualization
 *
 * Shows all 6 agents as connected nodes with live status indicators.
 */

"use client";

import { AGENT_DISPLAY_NAMES, AGENT_PIPELINE_ORDER } from "@/config/site";
import { cn } from "@/lib/utils";
import type { AgentStatusDetail } from "@/types/workflow";

interface WorkflowStatusProps {
  agents: AgentStatusDetail[];
  currentAgent: string | null;
}

function getAgentStatus(
  agents: AgentStatusDetail[],
  agentName: string,
  currentAgent: string | null
): string {
  const run = agents.find((a) => a.agent_name === agentName);
  if (run) return run.status;
  if (currentAgent === agentName) return "running";
  return "pending";
}

function StatusDot({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-zinc-900",
        status === "completed" && "bg-emerald-400",
        status === "running" && "bg-blue-400 animate-pulse",
        status === "failed" && "bg-red-400",
        status === "pending" && "bg-zinc-600"
      )}
    />
  );
}

function AgentIcon({ agentName }: { agentName: string }) {
  const icons: Record<string, string> = {
    research: "🔍",
    topic_prioritization: "📊",
    content_strategist: "🎯",
    content_writer: "✍️",
    chief_editor: "📝",
    cmo: "👔",
  };
  return <span className="text-2xl">{icons[agentName] || "🤖"}</span>;
}

export function WorkflowStatus({ agents, currentAgent }: WorkflowStatusProps) {
  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-zinc-400 mb-4 uppercase tracking-wider">
        Agent Pipeline
      </h3>

      <div className="flex flex-col gap-1">
        {AGENT_PIPELINE_ORDER.map((agentName, index) => {
          const status = getAgentStatus(agents, agentName, currentAgent);
          const agentRun = agents.find((a) => a.agent_name === agentName);

          return (
            <div key={agentName}>
              {/* Agent Node */}
              <div
                className={cn(
                  "relative flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300",
                  status === "running" &&
                    "bg-blue-500/10 border border-blue-500/30 shadow-lg shadow-blue-500/5",
                  status === "completed" &&
                    "bg-emerald-500/5 border border-emerald-500/20",
                  status === "failed" &&
                    "bg-red-500/5 border border-red-500/20",
                  status === "pending" &&
                    "bg-zinc-800/50 border border-zinc-700/50"
                )}
              >
                {/* Icon */}
                <div className="relative">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      status === "running" && "bg-blue-500/20",
                      status === "completed" && "bg-emerald-500/20",
                      status === "failed" && "bg-red-500/20",
                      status === "pending" && "bg-zinc-700/50"
                    )}
                  >
                    <AgentIcon agentName={agentName} />
                  </div>
                  <StatusDot status={status} />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      "text-sm font-medium truncate",
                      status === "running" && "text-blue-300",
                      status === "completed" && "text-emerald-300",
                      status === "failed" && "text-red-300",
                      status === "pending" && "text-zinc-500"
                    )}
                  >
                    {AGENT_DISPLAY_NAMES[agentName] || agentName}
                  </p>
                  {agentRun?.duration_ms && (
                    <p className="text-xs text-zinc-500 mt-0.5">
                      {(agentRun.duration_ms / 1000).toFixed(1)}s
                    </p>
                  )}
                  {agentRun?.error && (
                    <p className="text-xs text-red-400 mt-0.5 truncate">
                      {agentRun.error}
                    </p>
                  )}
                </div>

                {/* Status badge */}
                <span
                  className={cn(
                    "text-xs font-medium px-2 py-1 rounded-full",
                    status === "running" && "bg-blue-500/20 text-blue-300",
                    status === "completed" &&
                      "bg-emerald-500/20 text-emerald-300",
                    status === "failed" && "bg-red-500/20 text-red-300",
                    status === "pending" && "bg-zinc-700/50 text-zinc-500"
                  )}
                >
                  {status === "running"
                    ? "Running"
                    : status === "completed"
                      ? "Done"
                      : status === "failed"
                        ? "Failed"
                        : "Waiting"}
                </span>
              </div>

              {/* Connector line */}
              {index < AGENT_PIPELINE_ORDER.length - 1 && (
                <div className="flex justify-start ml-9 py-0.5">
                  <div
                    className={cn(
                      "w-0.5 h-3 rounded-full",
                      status === "completed"
                        ? "bg-emerald-500/40"
                        : "bg-zinc-700/50"
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
