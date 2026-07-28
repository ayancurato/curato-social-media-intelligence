/**
 * Curato AI — Generation History Table
 *
 * Displays past generation sessions with status and timestamps.
 */

"use client";

import { cn, formatDuration, formatTimestamp, getStatusLabel } from "@/lib/utils";
import type { GenerationSummary } from "@/types/workflow";
import { STATUS_COLORS } from "@/config/site";

interface GenerationHistoryProps {
  generations: GenerationSummary[];
}

export function GenerationHistory({ generations }: GenerationHistoryProps) {
  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
        Previous Generations
      </h3>

      {generations.length === 0 ? (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 text-center">
          <p className="text-zinc-500">No previous generations found.</p>
          <p className="text-zinc-600 text-sm mt-1">
            Click &quot;Generate Today&apos;s Content&quot; to create your first generation.
          </p>
        </div>
      ) : (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                  Revisions
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                  ID
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {generations.map((gen) => (
                <tr
                  key={gen.id}
                  className="hover:bg-zinc-800/30 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                        gen.status === "completed" &&
                          "bg-emerald-500/10 text-emerald-400",
                        gen.status === "failed" &&
                          "bg-red-500/10 text-red-400",
                        gen.status === "running" &&
                          "bg-blue-500/10 text-blue-400",
                        gen.status === "pending" &&
                          "bg-zinc-500/10 text-zinc-400"
                      )}
                    >
                      <span
                        className={cn(
                          "w-1.5 h-1.5 rounded-full",
                          gen.status === "completed" && "bg-emerald-400",
                          gen.status === "failed" && "bg-red-400",
                          gen.status === "running" &&
                            "bg-blue-400 animate-pulse",
                          gen.status === "pending" && "bg-zinc-400"
                        )}
                      />
                      {getStatusLabel(gen.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {formatTimestamp(gen.started_at || gen.created_at)}
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {formatDuration(gen.total_duration_ms)}
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {gen.retry_count}
                  </td>
                  <td className="px-4 py-3 text-zinc-600 font-mono text-xs">
                    {gen.id.slice(0, 8)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
