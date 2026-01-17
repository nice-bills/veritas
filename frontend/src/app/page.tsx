"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  ShieldCheck, 
  Terminal, 
  BrainCircuit, 
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Hash,
  Settings,
  X,
  Key,
  Database,
  Wallet
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function VeritasPlayground() {
  // Agent Config
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [objective, setObjective] = useState('Check balance and secure 0.0001 ETH if available.');
  
  // API Keys (Persisted)
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

  // Load keys from localStorage on mount
  useEffect(() => {
    setCdpId(localStorage.getItem('veritas_cdp_id') || '');
    setCdpSecret(localStorage.getItem('veritas_cdp_secret') || '');
    setMinimaxKey(localStorage.getItem('veritas_minimax_key') || '');
  }, []);

  // Auto-scroll terminal
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

  const runMission = async () => {
    if (!cdpId || !cdpSecret || !minimaxKey) {
      setShowSettings(true);
      return;
    }

    setIsRunning(true);
    setLogs([]);
    setSessionRoot(null);
    setAttestationTx(null);

    try {
      // 1. Create Agent with Keys
      const createRes = await fetch('http://localhost:8000/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentName,
          brain_provider: brainProvider,
          network: 'base-sepolia',
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
      console.error("Mission failed:", error);
      setLogs(prev => [...prev, { 
        event_type: 'ERROR', 
        tool_name: 'System', 
        output_result: error.message || 'Connection failed.' 
      }]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-6 border-b border-zinc-800 bg-zinc-900/50">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-indigo-400" />
                <h2 className="text-lg font-bold">API Configuration</h2>
              </div>
              <button onClick={() => setShowSettings(false)} className="text-zinc-500 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-widest">
                  <Database className="w-3 h-3" /> Coinbase CDP
                </div>
                <div className="space-y-3">
                  <input 
                    placeholder="API Key ID"
                    value={cdpId}
                    onChange={(e) => setCdpId(e.target.value)}
                    className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2.5 text-sm focus:border-indigo-500 outline-none transition-all font-mono"
                  />
                  <textarea 
                    placeholder="API Key Secret (PEM format)"
                    value={cdpSecret}
                    onChange={(e) => setCdpSecret(e.target.value)}
                    rows={3}
                    className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2.5 text-xs focus:border-indigo-500 outline-none transition-all font-mono resize-none"
                  />
                </div>
                <a href="https://portal.cdp.coinbase.com/access/api" target="_blank" rel="noreferrer" className="text-[10px] text-indigo-400 hover:underline flex items-center gap-1">
                  Get CDP Keys <ExternalLink className="w-2 h-2" />
                </a>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-widest">
                  <BrainCircuit className="w-3 h-3" /> MiniMax Brain
                </div>
                <input 
                  type="password"
                  placeholder="MiniMax API Key"
                  value={minimaxKey}
                  onChange={(e) => setMinimaxKey(e.target.value)}
                  className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-2.5 text-sm focus:border-indigo-500 outline-none transition-all font-mono"
                />
                <a href="https://platform.minimaxi.com/user-center/basic-information/interface-key" target="_blank" rel="noreferrer" className="text-[10px] text-indigo-400 hover:underline flex items-center gap-1">
                  Get MiniMax Key <ExternalLink className="w-2 h-2" />
                </a>
              </div>
            </div>

            <div className="p-6 bg-zinc-900/50 border-t border-zinc-800">
              <button 
                onClick={saveKeys}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-indigo-500/20"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-zinc-800/50 bg-zinc-950/50 backdrop-blur-xl sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight text-white leading-none">
              VERITAS <span className="text-indigo-500">OS</span>
            </h1>
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em] mt-1">Agent Platform</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2.5 px-4 py-1.5 bg-zinc-900 rounded-full border border-zinc-800 shadow-inner">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-wider text-zinc-400">Base Sepolia</span>
          </div>
          
          <button 
            onClick={() => setShowSettings(true)}
            className="p-2 hover:bg-zinc-900 rounded-full transition-colors text-zinc-400 hover:text-white relative group"
          >
            <Settings className="w-5 h-5" />
            <span className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-zinc-800 text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-zinc-700">API Settings</span>
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: Configuration */}
        <aside className="w-80 border-r border-zinc-800/50 bg-zinc-900/10 p-8 flex flex-col gap-8 overflow-y-auto">
          <section className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 block">Agent Identity</label>
            <div className="space-y-3">
              <div className="relative group">
                <input 
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  placeholder="Agent Name"
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all font-medium group-hover:border-zinc-700"
                />
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 block">Model Selection</label>
            <div className="grid grid-cols-3 gap-2">
              {['minimax', 'anthropic', 'openai'].map((p) => (
                <button
                  key={p}
                  onClick={() => setBrainProvider(p)}
                  className={cn(
                    "flex flex-col items-center justify-center p-2 rounded-lg border text-[10px] capitalize transition-all gap-1",
                    brainProvider === p 
                      ? "bg-indigo-600/10 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500/50" 
                      : "bg-zinc-900/30 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300"
                  )}
                >
                  <BrainCircuit className={cn("w-4 h-4", brainProvider === p ? "text-indigo-400" : "text-zinc-600")} />
                  <span className="font-bold truncate w-full text-center">{p}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 block">Mission Objective</label>
            <textarea 
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={5}
              className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all font-medium resize-none leading-relaxed placeholder:text-zinc-700 group-hover:border-zinc-700"
              placeholder="Enter high-level goal..."
            />
          </section>

          <div className="mt-auto pt-4 space-y-3">
            {(!cdpId || !minimaxKey) && (
              <button 
                onClick={() => setShowSettings(true)}
                className="w-full py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-[10px] font-bold uppercase tracking-wider hover:bg-yellow-500/20 transition-colors flex items-center justify-center gap-2"
              >
                <Key className="w-3 h-3" /> Configure API Keys Required
              </button>
            )}
            
            <button 
              onClick={runMission}
              disabled={isRunning}
              className={cn(
                "w-full py-4 rounded-xl font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-xl",
                isRunning 
                  ? "bg-zinc-800 text-zinc-600 cursor-not-allowed" 
                  : "bg-white text-black hover:bg-zinc-200 hover:scale-[1.02] active:scale-[0.98] shadow-white/5"
              )}
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-zinc-600 border-t-zinc-400 rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 fill-current" />
                  Start Mission
                </>
              )}
            </button>
          </div>
        </aside>

        {/* Center: Terminal */}
        <section className="flex-1 bg-black p-8 flex flex-col relative">
          <div className="flex items-center justify-between mb-6 px-2">
            <div className="flex items-center gap-3 text-zinc-600 text-[10px] font-black uppercase tracking-[0.3em]">
              <Terminal className="w-4 h-4" />
              Live Output
            </div>
            {agentAddress && (
              <div className="flex items-center gap-2 px-3 py-1 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
                <Wallet className="w-3 h-3 text-indigo-400" />
                <span className="text-[10px] font-mono text-indigo-400 font-bold">{agentAddress}</span>
              </div>
            )}
          </div>
          
          <div 
            ref={scrollRef}
            className="flex-1 bg-zinc-950/50 rounded-2xl border border-zinc-800/50 overflow-y-auto font-mono text-xs p-8 space-y-6 terminal-glow relative shadow-inner"
          >
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-800 animate-pulse">
                <Terminal className="w-12 h-12 mb-4 opacity-20" />
                <p className="font-bold uppercase tracking-widest text-[10px]">Awaiting Instructions</p>
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="animate-in fade-in slide-in-from-left-4 duration-500 group">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={cn(
                      "text-[9px] uppercase font-black tracking-widest px-2 py-0.5 rounded-sm",
                      log.event_type === 'OBSERVATION' ? 'bg-blue-500/10 text-blue-400' : 
                      log.event_type === 'ERROR' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                    )}>
                      {log.event_type}
                    </span>
                    <span className="text-[10px] font-bold text-zinc-600">{log.tool_name}</span>
                    <span className="h-px flex-1 bg-zinc-900 group-hover:bg-zinc-800 transition-colors" />
                  </div>
                  <div className="pl-4 border-l border-zinc-800 group-hover:border-zinc-700 transition-colors ml-1">
                    <pre className="text-zinc-400 whitespace-pre-wrap break-all leading-relaxed">
                      {log.output_result}
                    </pre>
                    {log.basis_id && (
                      <div className="mt-3 flex items-center gap-2 text-[9px] font-bold text-zinc-600 uppercase tracking-wider bg-zinc-900/50 w-fit px-2 py-1 rounded">
                        <ShieldCheck className="w-3 h-3 text-zinc-700" />
                        Basis: {log.basis_id.slice(0, 8)}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right Panel: Verification */}
        <aside className="w-80 border-l border-zinc-800/50 bg-zinc-900/10 p-8 flex flex-col gap-8 overflow-y-auto">
          <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 block">Trust Engine</label>
          
          <div className={cn(
            "p-6 rounded-2xl border transition-all duration-500 relative overflow-hidden group",
            sessionRoot ? "bg-green-500/5 border-green-500/30 shadow-lg shadow-green-500/5" : "bg-zinc-900/30 border-zinc-800"
          )}>
            <div className="flex items-center gap-3 mb-4">
              <div className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
                sessionRoot ? "bg-green-500/20" : "bg-zinc-800"
              )}>
                {sessionRoot ? (
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-zinc-600" />
                )}
              </div>
              <div>
                <h3 className={cn(
                  "text-sm font-black uppercase tracking-tight",
                  sessionRoot ? "text-green-500" : "text-zinc-500"
                )}>
                  {sessionRoot ? "Session Audited" : "Idle"}
                </h3>
                <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest mt-0.5">Cryptographic Integrity</p>
              </div>
            </div>
            
            {sessionRoot && (
              <div className="space-y-5 animate-in slide-in-from-bottom-2 duration-500">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[9px] text-zinc-500 uppercase font-black tracking-[0.1em]">
                    <div className="flex items-center gap-1.5"><Hash className="w-3 h-3 text-zinc-700" /> Session Fingerprint</div>
                    <span className="text-green-500/50">Verified</span>
                  </div>
                  <div className="text-[10px] font-mono bg-black/50 p-3 rounded-xl break-all text-zinc-400 leading-relaxed border border-zinc-800 shadow-inner group-hover:text-zinc-300 transition-colors">
                    {sessionRoot}
                  </div>
                </div>

                {attestationTx && (
                  <div className="pt-2">
                    <a 
                      href={`https://sepolia.basescan.org/tx/${attestationTx}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between w-full p-4 bg-zinc-900 hover:bg-zinc-800 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border border-zinc-800 hover:border-indigo-500/50 shadow-xl group/link"
                    >
                      <div className="flex items-center gap-3">
                        <ExternalLink className="w-4 h-4 text-indigo-400 group-hover/link:scale-110 transition-transform" />
                        On-Chain Proof
                      </div>
                      <span className="text-zinc-600 group-hover/link:text-indigo-400 transition-colors underline decoration-2 underline-offset-4">BaseScan</span>
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-6 rounded-2xl border border-zinc-800/50 bg-zinc-900/20 space-y-3">
            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-2">
              <Key className="w-3 h-3 text-indigo-500" /> Security Note
            </h3>
            <p className="text-[11px] text-zinc-600 leading-relaxed font-medium">
              Every thought and action is Merkle-hashed locally and attested to the Base blockchain. The proof above is mathematically immutable.
            </p>
          </div>

          <div className="mt-auto border-t border-zinc-800 pt-8">
            <button className="w-full py-4 px-4 bg-zinc-100 hover:bg-white text-black rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-xl active:scale-95 disabled:opacity-50">
              Promote to Mainnet
            </button>
            <p className="text-[10px] font-bold text-center text-zinc-700 mt-4 uppercase tracking-widest">
              Production Lockdown Required
            </p>
          </div>
        </aside>
      </main>
    </div>
  );
}
