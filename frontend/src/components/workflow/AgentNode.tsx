import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type AgentStatus = 'pending' | 'running' | 'completed' | 'error';

interface AgentNodeProps {
  name: string;
  status: AgentStatus;
  isActive?: boolean;
}

export function AgentNode({ name, status, isActive }: AgentNodeProps) {
  const getIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-6 h-6 text-curato-teal" />;
      case 'error':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'running':
        return <Loader2 className="w-6 h-6 text-curato-teal animate-spin" />;
      default:
        return <Circle className="w-6 h-6 text-muted" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative flex flex-col items-center p-4 rounded-xl border min-w-[120px] transition-all duration-300",
        isActive ? "border-curato-teal bg-curato-navy-light shadow-[0_0_15px_rgba(100,255,218,0.2)]" : "border-border bg-curato-navy",
        status === 'completed' && "border-curato-teal/50"
      )}
    >
      {isActive && status === 'running' && (
        <div className="absolute inset-0 rounded-xl border border-curato-teal animate-pulse-ring pointer-events-none" />
      )}
      <div className="mb-3">
        {getIcon()}
      </div>
      <span className={cn(
        "text-sm font-medium text-center",
        isActive ? "text-curato-teal" : "text-muted"
      )}>
        {name}
      </span>
    </motion.div>
  );
}
