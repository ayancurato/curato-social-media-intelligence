/**
 * Curato AI — Log Viewer Component
 *
 * Real-time scrolling log output with color-coded levels.
 */

"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { formatTimestamp } from "@/lib/utils";
import type { WorkflowLogEntry } from "@/types/workflow";

interface LogViewerProps {
  logs: WorkflowLogEntry[];
}

const LEVEL_STYLES: Record<string, string> = {
  info: "text-blue-400",
  warning: "text-amber-400",
  error: "text-red-400",
  debug: "text-zinc-500",
};

const LEVEL_BADGES: Record<string, string> = {
  info: "bg-blue-500/15 text-blue-400",
  warning: "bg-amber-500/15 text-amber-400",
  error: "bg-red-500/15 text-red-400",
  debug: "bg-zinc-500/15 text-zinc-400",
};

export function LogViewer({ logs }: LogViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
        Execution Logs
      </h3>

      <div
        ref={scrollRef}
        className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 h-64 overflow-y-auto font-mono text-xs space-y-1.5 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent"
      >
        {logs.length === 0 ? (
          <p className="text-zinc-600 text-center py-8">
            No logs yet. Trigger a workflow to see execution logs.
          </p>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-2 py-0.5 hover:bg-zinc-800/50 rounded px-1 -mx-1 transition-colors"
            >
              <span className="text-zinc-600 shrink-0 tabular-nums">
                {formatTimestamp(log.timestamp).split(", ").pop()}
              </span>
              <span
                className={cn(
                  "shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium uppercase",
                  LEVEL_BADGES[log.level] || LEVEL_BADGES.info
                )}
              >
                {log.level}
              </span>
              {log.agent_name && (
                <span className="text-violet-400 shrink-0">
                  [{log.agent_name}]
                </span>
              )}
              <span className={cn("break-all", LEVEL_STYLES[log.level] || "text-zinc-300")}>
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
