"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentNode, AgentStatus } from "@/components/workflow/AgentNode";
import { LiveLogs, LogEntry } from "@/components/workflow/LiveLogs";
import { CuratoWebSocket } from "@/lib/websocket";
import { Play, FileText, LayoutDashboard, CheckCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const AGENTS = [
  { id: "research_intelligence", name: "1. Research Intelligence" },
  { id: "topic_prioritization", name: "2. Topic Prioritization" },
  { id: "content_strategy", name: "3. Content Strategy" },
  { id: "content_writer", name: "4. Content Writer" },
  { id: "chief_editor", name: "5. Chief Editor" },
  { id: "cmo", name: "6. Exec. Approval" },
];

export default function Dashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const [completedAgents, setCompletedAgents] = useState<Set<string>>(new Set());
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [finalData, setFinalData] = useState<any>(null);

  const startWorkflow = async () => {
    setIsRunning(true);
    setIsComplete(false);
    setLogs([]);
    setCompletedAgents(new Set());
    setActiveAgentId("research_intelligence");

    try {
      setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'info', message: 'Initializing workflow with AI Backend...' }]);
      
      const response = await fetch("http://localhost:8000/api/v1/workflow/trigger", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          topic: "AI Marketing Strategies",
          platform: "linkedin"
        })
      });

      if (!response.ok) {
        throw new Error("Failed to trigger workflow");
      }

      const data = await response.json();
      const sessionId = data.data.session_id;

      setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'info', message: `Connected to execution engine. Session ID: ${sessionId}` }]);

      const ws = new CuratoWebSocket(sessionId);
      
      ws.onEvent((event) => {
        if (event.event_type === "agent_started") {
          setActiveAgentId(event.agent_name);
          setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'info', message: `[${event.agent_name.toUpperCase()}] started working...` }]);
        } else if (event.event_type === "agent_completed") {
          setCompletedAgents((prev) => {
            const next = new Set(prev);
            next.add(event.agent_name);
            return next;
          });
          setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'info', message: `[${event.agent_name.toUpperCase()}] completed successfully.` }]);
        } else if (event.event_type === "workflow_completed") {
          setIsRunning(false);
          setIsComplete(true);
          setActiveAgentId(null);
          
          setFinalData({
            docUrl: event.metadata?.doc_url || "https://docs.google.com/document/",
            sheetUrl: event.metadata?.sheet_url || "https://docs.google.com/spreadsheets/d/1hrLDz9RAsvPZjyDonzzK32ob_2AkaFhQJNec745zbus/edit"
          });
          
          setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'info', message: `Workflow fully completed! Content pushed to Google Workspace.` }]);
          ws.disconnect();
        } else if (event.event_type === "agent_error") {
          setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'error', message: `ERROR in [${event.agent_name}]: ${event.metadata?.error || 'Unknown error'}` }]);
          setIsRunning(false);
          ws.disconnect();
        }
      });

      ws.connect();

    } catch (error: any) {
      console.error(error);
      setLogs((prev) => [...prev, { id: Date.now().toString(), timestamp: new Date().toISOString(), level: 'error', message: `Failed to connect to backend engine: ${error.message}` }]);
      setIsRunning(false);
    }
  };

  const getStatus = (agentId: string): AgentStatus => {
    if (completedAgents.has(agentId)) return "completed";
    if (activeAgentId === agentId) return "running";
    return "pending";
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Header */}
      <header className="h-16 border-b border-border bg-curato-navy/50 glass flex items-center px-6 justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-gradient-to-tr from-curato-teal to-blue-500 flex items-center justify-center shadow-lg">
            <LayoutDashboard className="w-4 h-4 text-curato-navy" />
          </div>
          <h1 className="font-semibold text-lg tracking-wide text-white">Curato AI</h1>
        </div>
        <div>
          <Button 
            onClick={startWorkflow} 
            disabled={isRunning}
            className="gap-2 bg-curato-teal text-curato-navy hover:bg-curato-teal-light shadow-[0_0_15px_rgba(100,255,218,0.3)] transition-all"
          >
            <Play className="w-4 h-4" />
            {isRunning ? "Workflow Running..." : "Generate Today's Post"}
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-6xl mx-auto w-full flex flex-col gap-8">
        
        {/* Agent Pipeline Visualizer */}
        <section>
          <h2 className="text-xl font-semibold mb-6 text-white flex items-center gap-2">
            AI Orchestration Pipeline
          </h2>
          <div className="flex flex-wrap gap-4 items-center justify-between">
            {AGENTS.map((agent, index) => (
              <React.Fragment key={agent.id}>
                <AgentNode 
                  name={agent.name} 
                  status={getStatus(agent.id)} 
                  isActive={activeAgentId === agent.id} 
                />
                {index < AGENTS.length - 1 && (
                  <div className={`flex-1 h-0.5 rounded-full transition-colors duration-500 ${completedAgents.has(agent.id) ? 'bg-curato-teal' : 'bg-curato-navy-lighter'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Live Logs */}
          <div className="lg:col-span-2">
             <h2 className="text-xl font-semibold mb-6 text-white">System Telemetry</h2>
             <LiveLogs logs={logs} />
          </div>

          {/* Output Panel */}
          <div className="lg:col-span-1">
             <h2 className="text-xl font-semibold mb-6 text-white">Delivery Status</h2>
             
             <AnimatePresence mode="wait">
               {isComplete && finalData ? (
                 <motion.div
                   initial={{ opacity: 0, scale: 0.95 }}
                   animate={{ opacity: 1, scale: 1 }}
                   className="p-1"
                 >
                   <Card className="border-curato-teal/30 shadow-[0_0_20px_rgba(100,255,218,0.1)] bg-curato-navy-light relative overflow-hidden">
                     <div className="absolute top-0 left-0 w-full h-1 bg-curato-teal" />
                     <CardHeader>
                       <CardTitle className="flex items-center gap-2 text-curato-teal">
                         <CheckCircle className="w-5 h-5" /> Delivery Complete
                       </CardTitle>
                     </CardHeader>
                     <CardContent className="flex flex-col gap-4">
                        <p className="text-sm text-muted">
                          Curato AI has successfully generated the post, received executive approval, and synced the results to your Google Workspace.
                        </p>
                        
                        <Button variant="outline" className="w-full justify-start gap-3 h-12 border-curato-teal/30" asChild>
                          <a href={finalData.docUrl} target="_blank" rel="noreferrer">
                            <FileText className="w-4 h-4 text-blue-400" />
                            Open Google Doc
                          </a>
                        </Button>

                        <Button variant="outline" className="w-full justify-start gap-3 h-12 border-curato-teal/30" asChild>
                          <a href={finalData.sheetUrl} target="_blank" rel="noreferrer">
                            <svg className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="currentColor"><path d="M2 13h6v6H2v-6zm0-8h6v6H2V5zm8 0h6v6h-6V5zm0 8h6v6h-6v-6zm8-8h4v6h-4V5zm0 8h4v6h-4v-6z"/></svg>
                            Open Tracker Sheet
                          </a>
                        </Button>
                     </CardContent>
                   </Card>
                 </motion.div>
               ) : (
                 <motion.div
                   initial={{ opacity: 0 }}
                   animate={{ opacity: 1 }}
                   className="h-full"
                 >
                   <Card className="h-full min-h-[300px] flex items-center justify-center border-dashed border-border bg-transparent">
                     <div className="text-center text-muted flex flex-col items-center gap-3 p-6">
                        {isRunning ? (
                          <>
                            <div className="w-12 h-12 rounded-full border-4 border-curato-navy-lighter border-t-curato-teal animate-spin" />
                            <p>Awaiting final CMO approval...</p>
                          </>
                        ) : (
                          <>
                            <FileText className="w-10 h-10 opacity-20" />
                            <p>Click "Generate Today's Post" to begin.</p>
                          </>
                        )}
                     </div>
                   </Card>
                 </motion.div>
               )}
             </AnimatePresence>
          </div>
        </div>

      </main>
    </div>
  );
}
