import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Target, RefreshCw, BookOpen, GraduationCap, FileText, Zap } from 'lucide-react';

interface PIData {
  clarity_score?: number;
  logic_score?: number;
  critique_focus?: string;
}

interface PIInterfaceProps {
  metadata: PIData | null;
  children?: React.ReactNode;
  onReset?: () => void;
}

export const PIInterface: React.FC<PIInterfaceProps> = ({ metadata, children, onReset }) => {
  // Default values or parse from metadata (normalize keys just in case)
  const clarity = metadata?.clarity_score || (metadata as any)?.clarity || 0;
  const logic = metadata?.logic_score || (metadata as any)?.logic || 0;
  const focus = metadata?.critique_focus || (metadata as any)?.focus || "General Assessment";

  // Calculate overall "Defense Status"
  const overallScore = (clarity + logic) / 2;
  
  // Status indicator color (Light Theme)
  const getStatusColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600 border-emerald-200 bg-emerald-50';
    if (score >= 60) return 'text-amber-600 border-amber-200 bg-amber-50';
    return 'text-red-600 border-red-200 bg-red-50';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="h-full w-full bg-white text-slate-800 relative overflow-hidden rounded-2xl border border-slate-200 flex flex-col font-sans shadow-sm">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 p-4 z-10 shrink-0 flex items-center justify-between">
        <div className="flex items-center gap-2 text-blue-700">
          <div className="p-1.5 bg-blue-50 rounded-lg">
             <Zap className="w-5 h-5" />
          </div>
          <h2 className="font-bold tracking-tight text-sm uppercase">Academic Defense Console</h2>
        </div>
        <button 
          onClick={onReset}
          className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="New Conversation"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 relative z-10 flex overflow-hidden bg-slate-50/50">
        {/* Dashboard Panel (Left) */}
        <div className="w-1/3 border-r border-slate-200 bg-white p-5 flex flex-col gap-6 overflow-y-auto shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)] z-20 hide-scrollbar">
            
            {/* Overall Status */}
            <div className="flex flex-col gap-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Defense Status</span>
                <div className={`px-4 py-3 rounded-xl text-sm font-bold border flex items-center justify-between ${getStatusColor(overallScore)}`}>
                    <span>{overallScore >= 80 ? 'STRONG' : overallScore >= 60 ? 'STABLE' : 'CRITICAL'}</span>
                    <Shield className="w-4 h-4" />
                </div>
            </div>

            {/* Meters Grid */}
            <div className="space-y-4">
              {/* Clarity Meter */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div className="flex justify-between text-xs mb-2 text-slate-500 font-medium">
                  <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> Clarity</span>
                  <span>{clarity}%</span>
                </div>
                <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${clarity}%` }}
                    className={`h-full rounded-full ${getProgressBarColor(clarity)}`}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
              </div>

              {/* Logic Meter */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div className="flex justify-between text-xs mb-2 text-slate-500 font-medium">
                  <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" /> Logic</span>
                  <span>{logic}%</span>
                </div>
                <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${logic}%` }}
                    className={`h-full rounded-full ${getProgressBarColor(logic)}`}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
              </div>
            </div>
            
            {/* Focus Indicator */}
            {focus && (
              <div className="mt-auto">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Current Focus</span>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-lg text-blue-700 text-xs font-medium w-full">
                  <Target className="w-4 h-4 text-blue-500" />
                  <span>{focus.toUpperCase()}</span>
                </div>
              </div>
            )}
            
            <div className="text-[10px] text-slate-400 text-center pt-4 border-t border-slate-100 mt-2">
                <div className="flex items-center justify-center gap-1 mb-1">
                    <FileText className="w-3 h-3" />
                    <span>Live Critique Active</span>
                </div>
                Reviewing argument coherence...
            </div>
        </div>

        {/* Chat Area (Right) */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-white relative">
           {children}
        </div>
      </div>
    </div>
  );
};
