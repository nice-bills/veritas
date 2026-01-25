"use client";

import React, { useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  ShieldCheck, LayoutGrid, ArrowLeft, ExternalLink, 
  Trash2, Play, Hash, Calendar, Wallet
} from 'lucide-react';
import { toast } from 'sonner';

interface AgentHistoryItem {
  id: string;
  name: string;
  objective: string;
  root: string;
  tx?: string;
  timestamp: number;
  address?: string;
}

const formatAddress = (address?: string): string => {
  if (!address) return 'Unknown';
  return `${address.slice(0,6)}...${address.slice(-4)}`;
};

export default function Dashboard() {
  const [history, setHistory] = useState<AgentHistoryItem[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const saved = localStorage.getItem('veritas_agent_history');
      if (saved) return JSON.parse(saved);
    } catch {
      return [];
    }
    return [];
  });
  const router = useRouter();

  const handleClearHistory = useCallback(() => {
    if (confirm("Are you sure you want to clear all agent history?")) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('veritas_agent_history');
      }
      setHistory([]);
      toast.success("History cleared");
    }
  }, []);

  const loadAgent = useCallback((item: AgentHistoryItem) => {
    const config = {
      name: item.name,
      brain: 'minimax',
      caps: ['wallet', 'token', 'basename', 'aave'],
      objective: item.objective
    };
    if (typeof window !== 'undefined') {
      localStorage.setItem('veritas_agent_config', JSON.stringify(config));
    }
    toast.success("Agent configuration loaded");
    router.push('/');
  }, [router]);

  return (
    <div className="flex flex-col h-screen bg-[#050505] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

      <header className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/40 backdrop-blur-2xl z-10">
        <div className="flex items-center gap-4">
          <Link href="/" aria-label="Back to playground" className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition-all focus-visible:ring-2 focus-visible:ring-white/20">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-black tracking-tighter text-white leading-none uppercase flex items-center gap-2">
              My Agents <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 text-[10px] rounded-full border border-indigo-500/20">{history.length}</span>
            </h1>
          </div>
        </div>
        <button onClick={handleClearHistory} aria-label="Clear history" className="flex items-center gap-2 px-4 py-2 bg-zinc-900/50 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 rounded-full border border-white/5 text-xs font-bold uppercase tracking-widest transition-all focus-visible:ring-2 focus-visible:ring-red-500/20">
          <Trash2 className="w-4 h-4" /> Clear History
        </button>
      </header>

      <main className="flex-1 overflow-y-auto p-8 z-10 custom-scrollbar">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-800 space-y-6">
            <LayoutGrid className="w-24 h-24 opacity-20" />
            <p className="font-black uppercase tracking-[0.3em] text-xs">No Agents Deployed</p>
            <Link href="/" className="px-6 py-3 bg-white text-black rounded-xl font-bold text-xs uppercase tracking-widest hover:scale-105 transition-all">
              Create New Agent
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
            {history.map((agent, i) => (
              <div key={i} className="bg-zinc-900/20 border border-white/5 rounded-3xl p-6 hover:border-indigo-500/30 hover:bg-zinc-900/40 transition-all group relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-lg font-black text-white mb-1">{agent.name}</h3>
                    <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-mono">
                      <Wallet className="w-3 h-3" />
                      {formatAddress(agent.address)}
                    </div>
                  </div>
                  <div className="bg-emerald-500/10 border border-emerald-500/20 p-2 rounded-xl">
                    <ShieldCheck className="w-5 h-5 text-emerald-500" />
                  </div>
                </div>

                <div className="space-y-4 mb-6">
                  <div className="bg-black/40 rounded-xl p-3 border border-white/5">
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Objective</p>
                    <p className="text-xs text-zinc-300 line-clamp-2">{agent.objective}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-black/40 rounded-xl p-3 border border-white/5">
                      <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1 flex items-center gap-1"><Hash className="w-3 h-3" /> Root</p>
                      <p className="text-[9px] font-mono text-zinc-500 truncate" title={agent.root}>{agent.root}</p>
                    </div>
                    <div className="bg-black/40 rounded-xl p-3 border border-white/5">
                      <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1 flex items-center gap-1"><Calendar className="w-3 h-3" /> Time</p>
                      <p className="text-[9px] font-mono text-zinc-500">{new Date(agent.timestamp).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button onClick={() => loadAgent(agent)} className="flex-1 py-3 bg-white text-black rounded-xl font-bold text-[10px] uppercase tracking-widest hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
                    <Play className="w-3 h-3 fill-current" /> Rerun
                  </button>
                  {agent.tx && (
                    <a href={`https://sepolia.basescan.org/tx/${agent.tx}`} target="_blank" rel="noopener noreferrer" className="px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl border border-white/5 transition-colors">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
