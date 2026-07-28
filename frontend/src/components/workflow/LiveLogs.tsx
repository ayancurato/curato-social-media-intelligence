import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  message: string;
}

interface LiveLogsProps {
  logs: LogEntry[];
}

export function LiveLogs({ logs }: LiveLogsProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col h-[300px] w-full rounded-xl border border-border bg-[#050B14] overflow-hidden shadow-inner">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-curato-navy-light/50">
        <Terminal className="w-4 h-4 text-muted" />
        <span className="text-xs font-mono text-muted uppercase tracking-wider">Live System Logs</span>
      </div>
      <div 
        ref={containerRef}
        className="flex-1 p-4 overflow-y-auto font-mono text-sm scrollbar-thin"
      >
        <AnimatePresence initial={false}>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="mb-2 leading-relaxed"
            >
              <span className="text-muted mr-3">
                {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
              <span className={`
                ${log.level === 'error' ? 'text-red-400' : ''}
                ${log.level === 'warn' ? 'text-yellow-400' : ''}
                ${log.level === 'info' ? 'text-[#CCD6F6]' : ''}
              `}>
                {log.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        {logs.length === 0 && (
          <div className="text-muted italic opacity-50">Waiting for system activity...</div>
        )}
      </div>
    </div>
  );
}
