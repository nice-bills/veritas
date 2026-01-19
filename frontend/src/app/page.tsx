"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, ShieldCheck, Terminal, BrainCircuit, ExternalLink,
  CheckCircle2, AlertCircle, Hash, Settings, X, Database,
  Wallet, Zap, MessageSquare, Fingerprint, Coins, Lock, Code2, Rocket,
  Activity, CreditCard, DollarSign, Copy, RefreshCw, Search, ChevronRight,
  Trash2, Download, QrCode, LayoutGrid
} from 'lucide-react';
import Link from 'next/link';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { toast } from 'sonner';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace("http", "ws");

// Capability Config
const CAPABILITIES = [
  { id: 'wallet', name: 'Wallet', icon: Wallet },
  { id: 'token', name: 'Tokens', icon: Coins },
  { id: 'nft', name: 'NFTs', icon: Database },
  { id: 'basename', name: 'Basenames', icon: Fingerprint },
  { id: 'aave', name: 'Aave', icon: Zap },
  { id: 'compound', name: 'Compound', icon: Zap },
  { id: 'pyth', name: 'Pyth', icon: Activity },
  { id: 'onramp', name: 'Onramp', icon: CreditCard },
  { id: 'payments', name: 'Payments', icon: DollarSign },
  { id: 'trading', name: 'Trading', icon: Zap },
  { id: 'social', name: 'Social', icon: MessageSquare },
  { id: 'privacy', name: 'Privacy', icon: Lock },
];

// Templates Config
const TEMPLATES = [
  { id: 'arbitrage', name: 'Arbitrage Bot', objective: 'Check ETH price on Pyth and compare with Uniswap pools.', caps: ['wallet', 'token', 'pyth', 'trading'] },
  { id: 'rebalance', name: 'Portfolio Guard', objective: 'Check my ETH balance. If it is greater than 0.05, swap to USDC.', caps: ['wallet', 'token', 'trading'] },
  { id: 'basename', name: 'Identity Manager', objective: 'Register a new .basetest.eth name for this agent.', caps: ['wallet', 'basename'] },
  { id: 'defi', name: 'Yield Optimizer', objective: 'Check my USDC balance and supply it to Aave V3.', caps: ['wallet', 'token', 'aave'] },
];

export default function VeritasPlayground() {
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [selectedCaps, setSelectedCaps] = useState<string[]>(['wallet', 'token', 'basename', 'aave']);
  const [objective, setObjective] = useState('Check balance and secure 0.0001 ETH if available.');
  const [searchQuery, setSearchSearchQuery] = useState('');
  
  const [cdpId, setCdpId] = useState('');
  const [cdpSecret, setCdpSecret] = useState('');
  const [minimaxKey, setMinimaxKey] = useState('');
  
  const [isRunning, setIsRunning] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const [sessionRoot, setSessionRoot] = useState<string | null>(null);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [agentAddress, setAgentAddress] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setCdpId(localStorage.getItem('veritas_cdp_id') || '');
    setCdpSecret(localStorage.getItem('veritas_cdp_secret') || '');
    setMinimaxKey(localStorage.getItem('veritas_minimax_key') || '');
    
    const savedConfig = localStorage.getItem('veritas_agent_config');
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        setAgentName(parsed.name || 'Sentinel-1');
        setBrainProvider(parsed.brain || 'minimax');
        setSelectedCaps(parsed.caps || ['wallet', 'token', 'basename', 'aave']);
        setObjective(parsed.objective || 'Check balance and secure 0.0001 ETH if available.');
      } catch (e) {}
    }
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => {
    const config = { name: agentName, brain: brainProvider, caps: selectedCaps, objective: objective };
    localStorage.setItem('veritas_agent_config', JSON.stringify(config));
  }, [agentName, brainProvider, selectedCaps, objective]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [logs]);

  const saveKeys = () => {
    localStorage.setItem('veritas_cdp_id', cdpId);
    localStorage.setItem('veritas_cdp_secret', cdpSecret);
    localStorage.setItem('veritas_minimax_key', minimaxKey);
    setShowSettings(false);
    toast.success("Configuration saved");
  };

  const downloadProof = () => {
    const data = { session_root: sessionRoot, logs, timestamp: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `veritas-proof-${Date.now()}.json`;
    a.click();
    toast.success("Proof package downloaded");
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  };

  const applyTemplate = (t: typeof TEMPLATES[0]) => {
    setObjective(t.objective);
    setSelectedCaps(t.caps);
    toast.success(`Applied: ${t.name}`);
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
      const createRes = await fetch(`${API_BASE_URL}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentName, brain_provider: brainProvider, network: 'base-sepolia',
          capabilities: selectedCaps, cdp_api_key_id: cdpId, cdp_api_key_secret: cdpSecret, minimax_api_key: minimaxKey
        })
      });
      
      if (!createRes.ok) throw new Error("Initialization failed");
      const agentData = await createRes.json();
      setAgentAddress(agentData.address);

      const ws = new WebSocket(`${WS_BASE_URL}/agents/${agentData.id}/ws`);
      wsRef.current = ws;
      ws.onmessage = (event) => setLogs(prev => [...prev, JSON.parse(event.data)]);

      const runRes = await fetch(`${API_BASE_URL}/agents/${agentData.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });
      
      if (!runRes.ok) throw new Error("Execution failed");
      const result = await runRes.json();

      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
      
      const historyItem = { id: agentData.id, name: agentName, objective, root: result.session_root, tx: result.attestation_tx, timestamp: Date.now(), address: agentData.address };
      const hist = JSON.parse(localStorage.getItem('veritas_agent_history') || '[]');
      localStorage.setItem('veritas_agent_history', JSON.stringify([historyItem, ...hist]));

      toast.success("Audit Verified");
      ws.close();
    } catch (error: any) {
      toast.error(error.message);
      setLogs(prev => [...prev, { event_type: 'ERROR', tool_name: 'System', output_result: error.message, timestamp: Date.now()/1000 }]);
    } finally {
      setIsRunning(false);
    }
  };

  const filteredLogs = logs.filter(log => 
    log.tool_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.output_result.toString().toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getLogColor = (type: string) => {
    switch (type) {
      case 'ACTION': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'OBSERVATION': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'THOUGHT': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'ERROR': return 'bg-red-500/10 text-red-400 border-red-500/20';
      default: return 'bg-zinc-800 text-zinc-400';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#050505] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
      
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in duration-300">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-3xl shadow-2xl p-8 relative">
            <button onClick={() => setShowSettings(false)} className="absolute top-6 right-6 text-zinc-500"><X className="w-5 h-5" /></button>
            <h2 className="text-xl font-bold mb-6 flex items-center gap-3 text-white"><Settings className="w-6 h-6 text-indigo-500" /> Credentials</h2>
            <div className="space-y-5">
              <input value={cdpId} onChange={(e) => setCdpId(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none" placeholder="CDP API Key Name" />
              <textarea rows={3} value={cdpSecret} onChange={(e) => setCdpSecret(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-xs font-mono focus:border-indigo-500 outline-none" placeholder="CDP Private Key" />
              <input type="password" value={minimaxKey} onChange={(e) => setMinimaxKey(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none" placeholder="MiniMax API Key" />
              <button onClick={saveKeys} className="w-full py-4 bg-indigo-600 rounded-xl font-black text-xs uppercase tracking-[0.2em]">Authorize</button>
            </div>
          </div>
        </div>
      )}

      <header className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/40 backdrop-blur-2xl z-10">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg"><ShieldCheck className="text-white w-6 h-6" /></div>
          <div>
            <h1 className="text-xl font-black tracking-tighter text-white uppercase leading-none tracking-tight">Veritas <span className="text-indigo-500 italic">OS</span></h1>
            <p className="text-[9px] text-zinc-500 font-black tracking-[0.3em] uppercase mt-1">Autonomous Runtime</p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition-all" title="History">
            <LayoutGrid className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3 px-4 py-2 bg-zinc-900 rounded-full border border-white/5 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
            <span className="text-[10px] text-zinc-400 font-black uppercase tracking-widest">Base Sepolia</span>
          </div>
          <button onClick={() => setShowSettings(true)} className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition-all"><Settings className="w-5 h-5" /></button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <aside className="w-80 border-r border-white/5 bg-zinc-900/10 p-8 flex flex-col gap-10 overflow-y-auto custom-scrollbar z-10">
          <div className="space-y-5">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Fingerprint className="w-3.5 h-3.5" /> Identity</label>
            <input value={agentName} onChange={(e) => setAgentName(e.target.value)} className="w-full bg-zinc-900 border border-white/5 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all text-white font-bold" placeholder="Agent ID" />
          </div>

          <div className="space-y-5">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Zap className="w-3.5 h-3.5" /> Neural Templates</label>
            <div className="grid grid-cols-1 gap-3">
              {TEMPLATES.map((t) => (
                <button key={t.id} onClick={() => applyTemplate(t)} className="w-full text-left p-4 rounded-2xl border border-white/5 bg-zinc-900/20 hover:bg-zinc-900/60 hover:border-indigo-500/30 transition-all group overflow-hidden relative">
                  <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-black uppercase tracking-wider text-zinc-400 group-hover:text-indigo-400 block mb-1">{t.name}</span>
                  <p className="text-[10px] text-zinc-600 leading-relaxed italic truncate">"{t.objective}"</p>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-5 flex-1">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Lock className="w-3.5 h-3.5" /> Modules</label>
            <div className="grid grid-cols-1 gap-2">
              {CAPABILITIES.map((cap) => (
                <button key={cap.id} onClick={() => setSelectedCaps(prev => prev.includes(cap.id) ? prev.filter(c => c !== cap.id) : [...prev, cap.id])} className={cn("w-full flex items-center justify-between px-4 py-2.5 rounded-xl border transition-all", selectedCaps.includes(cap.id) ? "bg-indigo-500/5 border-indigo-500/40 text-indigo-300" : "border-transparent bg-white/5 text-zinc-500 hover:bg-white/10")}>
                  <div className="flex items-center gap-3"><cap.icon className="w-3.5 h-3.5" /><span className="text-[11px] font-bold uppercase tracking-widest">{cap.name}</span></div>
                  <div className={cn("w-1.5 h-1.5 rounded-full", selectedCaps.includes(cap.id) ? "bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]" : "bg-zinc-800")} />
                </button>
              ))}
            </div>
          </div>
        </aside>

        <section className="flex-1 flex flex-col bg-black relative z-10 shadow-2xl">
          <div className="p-8 border-b border-white/5 bg-zinc-900/5">
            <div className="flex justify-between items-center mb-4 text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">
              <span className="flex items-center gap-2"><Code2 className="w-4 h-4" /> Mission Objective</span>
              {agentAddress && <span onClick={() => copyToClipboard(agentAddress, "Address")} className="font-mono hover:text-indigo-400 cursor-pointer transition-colors px-2 py-1 bg-zinc-900 rounded border border-white/5">{agentAddress.slice(0,12)}...{agentAddress.slice(-10)}</span>}
            </div>
            <textarea value={objective} onChange={(e) => setObjective(e.target.value)} rows={3} className="w-full bg-black border border-white/5 rounded-2xl px-6 py-5 text-sm focus:border-indigo-500/50 outline-none transition-all font-medium resize-none leading-relaxed text-zinc-200 font-mono" placeholder="Define runtime protocol..." />
            <div className="flex justify-end mt-4 gap-4">
              <button onClick={() => setLogs([])} className="p-3 text-zinc-600 hover:text-red-400 transition-colors" title="Clear"><Trash2 className="w-4 h-4" /></button>
              <button onClick={runMission} disabled={isRunning} className={cn("px-8 py-3 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] flex items-center gap-3 transition-all", isRunning ? "bg-zinc-900 text-zinc-700 cursor-not-allowed border border-white/5" : "bg-white text-black hover:bg-slate-100 shadow-xl active:scale-95")}>
                {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                {isRunning ? "Executing Loop" : "Initiate Testnet"}
              </button>
            </div>
          </div>

          <div className="px-8 py-4 border-b border-white/5 flex items-center gap-4 bg-black/40 backdrop-blur-md">
            <Search className="w-4 h-4 text-zinc-700" />
            <input value={searchQuery} onChange={(e) => setSearchSearchQuery(e.target.value)} placeholder="Filter audit trail..." className="bg-transparent border-none text-xs w-full focus:outline-none text-zinc-500 placeholder:text-zinc-800 font-bold uppercase tracking-widest" />
          </div>

          <div className="flex-1 overflow-y-auto p-8 space-y-5 scroll-smooth custom-scrollbar" ref={scrollRef}>
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-900 space-y-6 opacity-40">
                <Terminal className="w-20 h-20" />
                <p className="font-black uppercase tracking-[0.5em] text-[11px]">System Idle</p>
              </div>
            ) : (
              filteredLogs.map((log, i) => (
                <div key={i} className={cn("border rounded-2xl p-6 font-mono text-[11px] animate-in slide-in-from-bottom-4 duration-500", getLogColor(log.event_type))}>
                  <div className="flex items-center justify-between mb-3 border-b border-current pb-2 opacity-40">
                    <div className="flex items-center gap-3"><span className="font-black uppercase tracking-widest">{log.event_type}</span><span className="uppercase font-black text-[9px] bg-current/10 px-2 py-0.5 rounded-full">{log.tool_name}</span></div>
                    <span className="text-[10px] font-bold">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  <pre className="whitespace-pre-wrap break-all leading-loose font-bold text-current drop-shadow-sm">{log.output_result}</pre>
                </div>
              ))
            )}
          </div>
        </section>

        <aside className="w-80 border-l border-white/5 bg-zinc-900/10 p-8 flex flex-col gap-8 z-10 overflow-y-auto custom-scrollbar">
          <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-emerald-500" /> Integrity Audit</label>
          
          {sessionRoot ? (
            <div className="space-y-8 animate-in slide-in-from-right-8 duration-700">
              <div className="p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-[2rem] relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><CheckCircle2 className="w-16 h-16 text-emerald-500" /></div>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-8 h-8 rounded-2xl bg-emerald-500/20 flex items-center justify-center shadow-lg"><CheckCircle2 className="w-4 h-4 text-emerald-500" /></div>
                  <span className="text-xs font-black uppercase tracking-[0.2em] text-emerald-400 tracking-tighter">Verified</span>
                </div>
                <div>
                  <span className="text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em] mb-2 block">Merkle Root</span>
                  <div className="text-[10px] font-mono text-zinc-400 break-all bg-black/80 p-4 rounded-2xl border border-white/5 cursor-pointer hover:text-emerald-400 transition-all duration-300" onClick={() => copyToClipboard(sessionRoot, "Root")}>{sessionRoot}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button onClick={downloadProof} className="flex flex-col items-center justify-center p-4 bg-zinc-900 border border-white/5 rounded-2xl hover:bg-zinc-800 transition-all gap-2 group">
                  <Download className="w-5 h-5 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
                  <span className="text-[9px] font-black uppercase tracking-wider text-zinc-600 group-hover:text-zinc-400">Proof</span>
                </button>
                <div className="flex flex-col items-center justify-center p-4 bg-zinc-900 border border-white/5 rounded-2xl opacity-50 cursor-not-allowed gap-2" title="Mobile Verification Coming Soon">
                  <QrCode className="w-5 h-5 text-zinc-700" />
                  <span className="text-[9px] font-black uppercase tracking-wider text-zinc-700">Verify Mobile</span>
                </div>
              </div>

              {attestationTx && (
                <div className="space-y-5">
                  <a href={`https://sepolia.basescan.org/tx/${attestationTx}`} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between w-full p-5 bg-zinc-900/80 hover:bg-zinc-800 border border-white/5 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] text-zinc-300 transition-all group shadow-2xl">
                    <span>View BaseScan</span><ExternalLink className="w-4 h-4 text-zinc-600 group-hover:text-white transition-colors" />
                  </a>
                </div>
              )}

              <div className="pt-8 border-t border-white/5">
                <button className="w-full py-5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-3xl text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all shadow-2xl hover:-translate-y-1" onClick={() => toast.info("Beta Gated")}>
                  <Rocket className="w-4 h-4" /> Deploy Persistence
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center py-12 text-center border-2 border-dashed border-white/5 rounded-[3rem] bg-white/[0.02] opacity-40">
              <Hash className="w-8 h-8 text-zinc-800 mb-4" />
              <p className="text-zinc-600 text-[10px] font-black uppercase tracking-[0.4em]">Vault Empty</p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
