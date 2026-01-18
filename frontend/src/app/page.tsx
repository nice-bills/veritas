"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, ShieldCheck, Terminal, BrainCircuit, ExternalLink,
  CheckCircle2, AlertCircle, Hash, Settings, X, Database,
  Wallet, Zap, MessageSquare, Fingerprint, Coins, Lock, Code2, Rocket
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Capability Config
const CAPABILITIES = [
  { id: 'erc20', name: 'Tokens', icon: Coins },
  { id: 'trading', name: 'Trading', icon: Zap },
  { id: 'social', name: 'Social', icon: MessageSquare },
  { id: 'identity', name: 'Identity', icon: Fingerprint },
  { id: 'privacy', name: 'Privacy', icon: Lock },
];

export default function VeritasPlayground() {
  // Agent Config
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [selectedCaps, setSelectedCaps] = useState<string[]>(['erc20', 'trading']);
  const [objective, setObjective] = useState('Check balance and secure 0.0001 ETH if available.');
  
  // API Keys
  const [cdpId, setCdpId] = useState('');
  const [cdpSecret, setCdpSecret] = useState('');
  const [minimaxKey, setMinimaxKey] = useState('');
  
  // UI State
  const [isRunning, setIsRunning] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const [sessionRoot, setSessionRoot] = useState<string | null>(null);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [agentAddress, setAgentAddress] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCdpId(localStorage.getItem('veritas_cdp_id') || '');
    setCdpSecret(localStorage.getItem('veritas_cdp_secret') || '');
    setMinimaxKey(localStorage.getItem('veritas_minimax_key') || '');
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const saveKeys = () => {
    localStorage.setItem('veritas_cdp_id', cdpId);
    localStorage.setItem('veritas_cdp_secret', cdpSecret);
    localStorage.setItem('veritas_minimax_key', minimaxKey);
    setShowSettings(false);
  };

  const toggleCap = (id: string) => {
    setSelectedCaps(prev => 
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const runMission = async () => {
    if (!objective.trim()) return;
    if (!cdpId || !cdpSecret || !minimaxKey) {
      setShowSettings(true);
      return;
    }

    setIsRunning(true);
    setLogs([]);
    setSessionRoot(null);
    setAttestationTx(null);

    try {
      // 1. Create Agent
      const createRes = await fetch('http://localhost:8000/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentName,
          brain_provider: brainProvider,
          network: 'base-sepolia',
          capabilities: selectedCaps,
          cdp_api_key_id: cdpId,
          cdp_api_key_secret: cdpSecret,
          minimax_api_key: minimaxKey
        })
      });
      
      if (!createRes.ok) throw new Error("Failed to initialize agent");
      const agentData = await createRes.json();
      setAgentAddress(agentData.address);

      // 2. Run Mission
      const runRes = await fetch(`http://localhost:8000/agents/${agentData.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });
      
      if (!runRes.ok) throw new Error("Mission execution failed");
      const result = await runRes.json();

      setLogs(result.logs);
      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
    } catch (error: any) {
      setLogs(prev => [...prev, { event_type: 'ERROR', tool_name: 'System', output_result: error.message }]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-slate-200 font-sans selection:bg-indigo-500/30 overflow-hidden">
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-6">
            <h2 className="text-lg font-bold mb-4">API Configuration</h2>
            <div className="space-y-4">
              <input placeholder="CDP API Key ID" value={cdpId} onChange={(e) => setCdpId(e.target.value)} className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2 text-sm" />
              <textarea placeholder="CDP API Key Secret" value={cdpSecret} onChange={(e) => setCdpSecret(e.target.value)} className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2 text-sm" />
              <input type="password" placeholder="MiniMax API Key" value={minimaxKey} onChange={(e) => setMinimaxKey(e.target.value)} className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2 text-sm" />
              <button onClick={saveKeys} className="w-full py-2 bg-indigo-600 rounded-lg font-bold text-sm">Save Configuration</button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <ShieldCheck className="text-white w-5 h-5" />
          </div>
          <h1 className="text-lg font-black tracking-tight text-white">VERITAS <span className="text-indigo-500">OS</span></h1>
        </div>
        <button onClick={() => setShowSettings(true)} className="p-2 hover:bg-zinc-900 rounded-full text-zinc-400">
          <Settings className="w-5 h-5" />
        </button>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left: Configuration */}
        <aside className="w-80 border-r border-zinc-800 bg-zinc-900/10 p-6 flex flex-col gap-6 overflow-y-auto">
          <div className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Identity</label>
            <input 
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:border-indigo-500 outline-none"
            />
          </div>

          <div className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Brain</label>
            <div className="grid grid-cols-3 gap-2">
              {['minimax', 'anthropic', 'openai'].map((p) => (
                <button
                  key={p}
                  onClick={() => setBrainProvider(p)}
                  className={cn(
                    "flex flex-col items-center justify-center p-2 rounded-lg border text-[10px] capitalize transition-all gap-1",
                    brainProvider === p ? "bg-indigo-600/10 border-indigo-500 text-white" : "bg-zinc-900 border-zinc-800 text-zinc-500"
                  )}
                >
                  <BrainCircuit className={cn("w-4 h-4", brainProvider === p ? "text-indigo-400" : "text-zinc-600")} />
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Capabilities</label>
            <div className="space-y-1">
              {CAPABILITIES.map((cap) => (
                <button
                  key={cap.id}
                  onClick={() => toggleCap(cap.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg border text-xs font-medium transition-all",
                    selectedCaps.includes(cap.id) ? "bg-indigo-600/5 border-indigo-500/30 text-indigo-200" : "border-transparent text-zinc-500 hover:bg-zinc-900"
                  )}
                >
                  <div className={cn("w-4 h-4 rounded flex items-center justify-center", selectedCaps.includes(cap.id) ? "bg-indigo-500 text-white" : "bg-zinc-800 text-zinc-600")}>
                    {selectedCaps.includes(cap.id) ? <CheckCircle2 className="w-3 h-3" /> : <cap.icon className="w-3 h-3" />}
                  </div>
                  {cap.name}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Center: Mission Editor & Logs */}
        <section className="flex-1 flex flex-col bg-black relative">
          <div className="p-6 border-b border-zinc-800 bg-zinc-900/20">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-3 block flex items-center gap-2">
              <Code2 className="w-3 h-3" /> Mission Logic
            </label>
            <textarea 
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={3}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all font-medium resize-none leading-relaxed placeholder:text-zinc-700 font-mono"
              placeholder="Define the agent's objective..."
            />
            <div className="flex justify-end mt-3">
              <button 
                onClick={runMission}
                disabled={isRunning}
                className={cn(
                  "px-6 py-2 rounded-lg font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition-all",
                  isRunning ? "bg-zinc-800 text-zinc-600 cursor-not-allowed" : "bg-white text-black hover:scale-105"
                )}
              >
                {isRunning ? <div className="w-3 h-3 border-2 border-zinc-600 border-t-black rounded-full animate-spin" /> : <Play className="w-3 h-3" />}
                Run on Testnet
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4" ref={scrollRef}>
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-800 space-y-4">
                <Terminal className="w-12 h-12 opacity-20" />
                <p className="font-bold uppercase tracking-widest text-[10px]">Awaiting Execution</p>
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-4 font-mono text-xs text-zinc-300">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      log.event_type === 'OBSERVATION' ? 'bg-blue-500/10 text-blue-400' : 'bg-green-500/10 text-green-400'
                    )}>{log.event_type}</span>
                    <span className="text-zinc-500">{log.tool_name}</span>
                  </div>
                  <pre className="whitespace-pre-wrap break-all opacity-80">{log.output_result}</pre>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right: Audit */}
        <aside className="w-72 border-l border-zinc-800 bg-zinc-900/10 p-6">
          <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-4 block">Audit Trail</label>
          {sessionRoot ? (
            <div className="space-y-6 animate-in slide-in-from-right-4">
              <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-xs font-bold text-green-500">Verified</span>
                </div>
                <div className="text-[10px] font-mono text-zinc-500 break-all bg-black/50 p-2 rounded">
                  {sessionRoot}
                </div>
              </div>
              {attestationTx && (
                <a 
                  href={`https://sepolia.basescan.org/tx/${attestationTx}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 rounded-lg text-center text-xs font-bold text-zinc-300 transition-all"
                >
                  View on BaseScan ↗
                </a>
              )}
              <div className="pt-8 border-t border-zinc-800">
                <button className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-500/20">
                  <Rocket className="w-3 h-3" /> Deploy to Mainnet
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center text-zinc-700 text-xs py-10">
              Run a mission to generate proof.
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
