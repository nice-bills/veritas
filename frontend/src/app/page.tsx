"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Square, 
  ShieldCheck, 
  Terminal, 
  BrainCircuit, 
  Wallet, 
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Hash
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function VeritasPlayground() {
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [objective, setObjective] = useState('Check balance and secure 0.0001 ETH if available.');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const [sessionRoot, setSessionRoot] = useState<string | null>(null);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [agentAddress, setAgentAddress] = useState<string | null>(null);
  const [agentId, setAgentId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const runMission = async () => {
    setIsRunning(true);
    setLogs([]);
    setSessionRoot(null);
    setAttestationTx(null);

    try {
      // 1. Create/Get Agent
      const createRes = await fetch('http://localhost:8000/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentName,
          brain_provider: brainProvider,
          network: 'base-sepolia'
        })
      });
      const agentData = await createRes.json();
      setAgentId(agentData.id);
      setAgentAddress(agentData.address);

      // 2. Run Mission
      const runRes = await fetch(`http://localhost:8000/agents/${agentData.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });
      const result = await runRes.json();

      setLogs(result.logs);
      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
    } catch (error) {
      console.error("Mission failed:", error);
      setLogs(prev => [...prev, { event_type: 'ERROR', tool_name: 'System', output_result: 'Connection to Veritas API failed.' }]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-slate-200 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <ShieldCheck className="text-white w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
            Veritas <span className="text-zinc-500 font-medium">OS</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-zinc-800 rounded-full border border-zinc-700">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-zinc-400">Base Sepolia</span>
          </div>
          <button className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
            Documentation
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: Configuration */}
        <aside className="w-80 border-r border-zinc-800 bg-zinc-900/30 p-6 flex flex-col gap-6 overflow-y-auto">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 block mb-2">Agent Name</label>
            <input 
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 block mb-2">Select Brain</label>
            <div className="grid grid-cols-1 gap-2">
              {['minimax', 'anthropic', 'openai'].map((p) => (
                <button
                  key={p}
                  onClick={() => setBrainProvider(p)}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-md border text-sm capitalize transition-all",
                    brainProvider === p 
                      ? "bg-indigo-600/10 border-indigo-500 text-white shadow-sm" 
                      : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-600"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <BrainCircuit className="w-4 h-4" />
                    {p}
                  </div>
                  {brainProvider === p && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 block mb-2">Mission Objective</label>
            <textarea 
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={4}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none"
              placeholder="What should the agent do?"
            />
          </div>

          <div className="mt-auto">
            <button 
              onClick={runMission}
              disabled={isRunning}
              className={cn(
                "w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all shadow-lg",
                isRunning 
                  ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" 
                  : "bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-[1.02] active:scale-[0.98]"
              )}
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-zinc-500 border-t-zinc-200 rounded-full animate-spin" />
                  Running Mission...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Deploy to Testnet
                </>
              )}
            </button>
          </div>
        </aside>

        {/* Center: Terminal */}
        <section className="flex-1 bg-black p-4 flex flex-col">
          <div className="flex items-center justify-between mb-4 px-2">
            <div className="flex items-center gap-2 text-zinc-500 text-xs font-mono uppercase tracking-widest">
              <Terminal className="w-4 h-4" />
              Agent Live Execution Log
            </div>
            {agentAddress && (
              <div className="text-xs font-mono text-indigo-400 bg-indigo-400/10 px-2 py-1 rounded">
                {agentAddress.slice(0, 6)}...{agentAddress.slice(-4)}
              </div>
            )}
          </div>
          
          <div 
            ref={scrollRef}
            className="flex-1 bg-zinc-950 rounded-xl border border-zinc-800 overflow-y-auto font-mono text-sm p-6 space-y-4 terminal-glow"
          >
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-zinc-700 italic">
                Ready for deployment...
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="animate-in fade-in slide-in-from-left-2 duration-300">
                  <div className={cn(
                    "text-[10px] uppercase font-bold tracking-widest mb-1",
                    log.event_type === 'OBSERVATION' ? 'text-blue-400' : 'text-green-400'
                  )}>
                    {log.event_type} — {log.tool_name}
                  </div>
                  <div className="bg-zinc-900/50 border-l-2 border-zinc-700 p-3 rounded-r-md">
                    <pre className="text-zinc-300 whitespace-pre-wrap break-all">
                      {log.output_result}
                    </pre>
                    {log.basis_id && (
                      <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center gap-2 text-xs text-zinc-500">
                        <ShieldCheck className="w-3 h-3" />
                        Basis ID: {log.basis_id.slice(0, 8)}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right Panel: Verification */}
        <aside className="w-80 border-l border-zinc-800 bg-zinc-900/30 p-6 flex flex-col gap-6 overflow-y-auto">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Verification Hub</h2>
          
          <div className={cn(
            "p-4 rounded-xl border flex flex-col gap-3 transition-all",
            sessionRoot ? "bg-green-500/5 border-green-500/20" : "bg-zinc-800/50 border-zinc-700"
          )}>
            <div className="flex items-center gap-2">
              {sessionRoot ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-zinc-600" />
              )}
              <span className={cn(
                "text-sm font-bold",
                sessionRoot ? "text-green-500" : "text-zinc-500"
              )}>
                {sessionRoot ? "Session Audited" : "No Session Proof"}
              </span>
            </div>
            
            {sessionRoot && (
              <div className="space-y-3">
                <div>
                  <div className="flex items-center gap-1 text-[10px] text-zinc-500 uppercase font-bold mb-1">
                    <Hash className="w-3 h-3" /> Merkle Root
                  </div>
                  <div className="text-[10px] font-mono bg-black p-2 rounded break-all text-zinc-400 leading-relaxed">
                    {sessionRoot}
                  </div>
                </div>

                {attestationTx && (
                  <div className="pt-2">
                    <a 
                      href={`https://sepolia.basescan.org/tx/${attestationTx}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between w-full px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-md text-xs font-medium transition-colors border border-zinc-700"
                    >
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-3 h-3" />
                        View Attestation
                      </div>
                      <span className="text-[10px] text-zinc-500 underline">BaseScan</span>
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/50 flex flex-col gap-2">
            <h3 className="text-xs font-bold text-zinc-400">Why Veritas?</h3>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Every action in the center panel is cryptographically linked to the observations that preceded it. The Merkle Root above proves the entire chain of reasoning.
            </p>
          </div>

          <div className="mt-auto pt-6 border-t border-zinc-800">
            <button className="w-full py-2 px-4 bg-zinc-100 hover:bg-white text-black rounded-md text-xs font-bold transition-all">
              Promote to Mainnet
            </button>
            <p className="text-[10px] text-center text-zinc-600 mt-2">
              Moves agent to production infrastructure.
            </p>
          </div>
        </aside>
      </main>
    </div>
  );
}