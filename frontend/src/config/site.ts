/**
 * Curato AI — Site Configuration
 */

export const siteConfig = {
  name: "Curato AI",
  description: "Social Media Intelligence System — Enterprise-grade multi-agent AI platform",
  version: "0.1.0",
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
  },
} as const;

export const AGENT_DISPLAY_NAMES: Record<string, string> = {
  research: "Research Intelligence",
  topic_prioritization: "Topic Prioritization",
  content_strategist: "Content Strategist",
  content_writer: "Content Writer",
  chief_editor: "Chief Editor",
  cmo: "Curato CMO",
} as const;

export const AGENT_PIPELINE_ORDER = [
  "research",
  "topic_prioritization",
  "content_strategist",
  "content_writer",
  "chief_editor",
  "cmo",
] as const;

export const STATUS_COLORS: Record<string, string> = {
  pending: "text-zinc-400",
  running: "text-blue-400",
  agent_executing: "text-blue-400",
  completed: "text-emerald-400",
  failed: "text-red-400",
  approved: "text-emerald-400",
  revision_loop: "text-amber-400",
  cancelled: "text-zinc-500",
} as const;
