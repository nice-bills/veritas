"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, ShieldCheck, Terminal, BrainCircuit, ExternalLink,
  CheckCircle2, AlertCircle, Hash, Settings, X, Database,
  Wallet, Zap, MessageSquare, Fingerprint, Coins, Lock, Code2, Rocket,
  Activity, CreditCard, DollarSign, Copy, RefreshCw, Search, ChevronRight,
  Trash2, LayoutGrid
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
  { 
    id: 'arbitrage', 
    name: 'Arbitrage Bot', 
    objective: 'Check ETH price on Pyth and compare with Uniswap pools. If there is a 1% spread, simulate a trade.',
    caps: ['wallet', 'token', 'pyth', 'trading']
  },
  { 
    id: 'rebalance', 
    name: 'Portfolio Guard', 
    objective: 'Check my ETH balance. If it is greater than 0.05, swap the excess to USDC using WETH wrapping if needed.',
    caps: ['wallet', 'token', 'trading']
  },
  { 
    id: 'basename', 
    name: 'Identity Manager', 
    objective: 'Register a new .basetest.eth name for this agent and verify it on-chain.',
    caps: ['wallet', 'basename']
  },
  { 
    id: 'defi', 
    name: 'Yield Optimizer', 
    objective: 'Check my USDC balance and supply it to Aave V3 to earn yield.',
    caps: ['wallet', 'token', 'aave']
  },
];

export default function VeritasPlayground() {
  // Agent Config
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [selectedCaps, setSelectedCaps] = useState<string[]>(['wallet', 'token', 'basename', 'aave']);
  const [objective, setObjective] = useState('Check balance and secure 0.0001 ETH if available.');
  const [searchQuery, setSearchSearchQuery] = useState('');
  
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
      } catch (e) {
        console.error("Failed to load agent config", e);
      }
    }

    return () => {
      wsRef.current?.close();
    };
  }, []);

  useEffect(() => {
    const config = { name: agentName, brain: brainProvider, caps: selectedCaps, objective: objective };
    localStorage.setItem('veritas_agent_config', JSON.stringify(config));
  }, [agentName, brainProvider, selectedCaps, objective]);

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
    toast.success("Configuration saved");
  };

  const applyTemplate = (t: typeof TEMPLATES[0]) => {
    setObjective(t.objective);
    setSelectedCaps(t.caps);
    toast.success(`Applied template: ${t.name}`);
  };

  const clearLogs = () => {
    setLogs([]);
    setSessionRoot(null);
    setAttestationTx(null);
    toast.info("Audit logs cleared");
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
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
          name: agentName,
          brain_provider: brainProvider,
          network: 'base-sepolia',
          capabilities: selectedCaps,
          cdp_api_key_id: cdpId,
          cdp_api_key_secret: cdpSecret,
          minimax_api_key: minimaxKey
        })
      });
      
      if (!createRes.ok) {
        const errData = await createRes.json();
        throw new Error(errData.detail || "Failed to initialize agent");
      }
      
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
      
      if (!runRes.ok) throw new Error("Mission failed during execution");
      const result = await runRes.json();

      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
      
      // Save to History
      const historyItem = {
        id: agentData.id,
        name: agentName,
        objective: objective,
        root: result.session_root,
        tx: result.attestation_tx,
        timestamp: Date.now(),
        address: agentData.address
      };
      const existingHistory = JSON.parse(localStorage.getItem('veritas_agent_history') || '[]');
      localStorage.setItem('veritas_agent_history', JSON.stringify([historyItem, ...existingHistory]));

      toast.success("Mission Attested to Base");
      ws.close();
    } catch (error: any) {
      toast.error("Mission Error", { description: error.message });
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
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
      
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in duration-300">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-3xl shadow-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
            <button onClick={() => setShowSettings(false)} className="absolute top-6 right-6 text-zinc-500 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
            <h2 className="text-xl font-bold mb-6 flex items-center gap-3 text-white"><Settings className="w-6 h-6 text-indigo-500" /> System Credentials</h2>
            <div className="space-y-5">
              <div>
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 mb-2 block">CDP API Key Name</label>
                <input value={cdpId} onChange={(e) => setCdpId(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all placeholder:text-zinc-800" placeholder="e.g. organizations/..." />
              </div>
              <div>
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 mb-2 block">CDP Private Key</label>
                <textarea rows={3} value={cdpSecret} onChange={(e) => setCdpSecret(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-xs font-mono focus:border-indigo-500 outline-none transition-all placeholder:text-zinc-800" placeholder="-----BEGIN EC PRIVATE KEY-----" />
              </div>
              <div>
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 mb-2 block">MiniMax Brain Key</label>
                <input type="password" value={minimaxKey} onChange={(e) => setMinimaxKey(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all" />
              </div>
              <button onClick={saveKeys} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-black text-xs uppercase tracking-[0.2em] transition-all shadow-xl shadow-indigo-500/20 active:scale-[0.98]">Authorize System</button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/40 backdrop-blur-2xl z-10">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-white/10"><ShieldCheck className="text-white w-6 h-6" /></div>
          <div>
            <h1 className="text-xl font-black tracking-tighter text-white leading-none uppercase">Veritas <span className="text-indigo-500 italic">OS</span></h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[9px] text-zinc-500 font-black tracking-[0.3em] uppercase">Autonomous Audit Engine</span>
              <span className="w-1 h-1 rounded-full bg-zinc-800" />
              <span className="text-[9px] text-indigo-500/80 font-black tracking-[0.3em] uppercase">v0.1.0-A</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition-all" title="My Agents">
            <LayoutGrid className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3 px-4 py-2 bg-zinc-900/50 rounded-full border border-white/5 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
            <span className="text-[10px] text-zinc-400 font-black uppercase tracking-widest">Base Sepolia</span>
          </div>
          <button onClick={() => setShowSettings(true)} className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition-all"><Settings className="w-5 h-5" /></button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left: Identity & Templates */}
        <aside className="w-80 border-r border-white/5 bg-zinc-900/10 p-8 flex flex-col gap-10 overflow-y-auto custom-scrollbar z-10">
          <div className="space-y-5">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Fingerprint className="w-3.5 h-3.5" /> Identity</label>
            <div className="relative group">
              <input value={agentName} onChange={(e) => setAgentName(e.target.value)} className="w-full bg-zinc-900/50 border border-white/5 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none transition-all text-white font-bold placeholder:text-zinc-800 group-hover:bg-zinc-900" placeholder="e.g. AUDIT-01" />
              <div className="absolute inset-0 rounded-xl bg-indigo-500/5 opacity-0 group-focus-within:opacity-100 pointer-events-none transition-opacity" />
            </div>
          </div>

          <div className="space-y-5">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Zap className="w-3.5 h-3.5" /> Neural Templates</label>
            <div className="grid grid-cols-1 gap-3">
              {TEMPLATES.map((t) => (
                <button key={t.id} onClick={() => applyTemplate(t)} className="w-full text-left p-4 rounded-2xl border border-white/5 bg-zinc-900/20 hover:bg-zinc-900/60 hover:border-indigo-500/30 transition-all group relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="flex items-center justify-between mb-1.5 relative z-10">
                    <span className="text-[11px] font-black uppercase tracking-wider text-zinc-400 group-hover:text-indigo-400 transition-colors">{t.name}</span>
                    <ChevronRight className="w-3 h-3 text-zinc-700 group-hover:translate-x-1 transition-transform" />
                  </div>
                  <p className="text-[10px] text-zinc-600 leading-relaxed group-hover:text-zinc-400 transition-colors italic">"{t.objective.slice(0, 60)}..."</p>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-5 flex-1">
            <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Lock className="w-3.5 h-3.5" /> Modules</label>
            <div className="grid grid-cols-1 gap-2">
              {CAPABILITIES.map((cap) => (
                <button key={cap.id} onClick={() => setSelectedCaps(prev => prev.includes(cap.id) ? prev.filter(c => c !== cap.id) : [...prev, cap.id])} className={cn("w-full flex items-center justify-between px-4 py-2.5 rounded-xl border transition-all group", selectedCaps.includes(cap.id) ? "bg-indigo-500/5 border-indigo-500/40 text-indigo-300" : "border-transparent bg-white/5 text-zinc-500 hover:bg-white/10")}>
                  <div className="flex items-center gap-3">
                    <cap.icon className={cn("w-3.5 h-3.5", selectedCaps.includes(cap.id) ? "text-indigo-400" : "text-zinc-700")} />
                    <span className="text-[11px] font-bold uppercase tracking-widest">{cap.name}</span>
                  </div>
                  <div className={cn("w-1.5 h-1.5 rounded-full transition-all", selectedCaps.includes(cap.id) ? "bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]" : "bg-zinc-800")} />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Center: Workspace */}
        <section className="flex-1 flex flex-col bg-black relative z-10">
          <div className="p-8 border-b border-white/5 bg-zinc-900/5">
            <div className="flex justify-between items-center mb-4">
              <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><Code2 className="w-4 h-4" /> Mission Logic</label>
              {agentAddress && (
                <div className="flex items-center gap-2 bg-zinc-900 px-3 py-1.5 rounded-full border border-white/5 hover:border-indigo-500/50 transition-all cursor-pointer group" onClick={() => copyToClipboard(agentAddress, "Agent Address")}>
                  <Wallet className="w-3 h-3 text-indigo-500" />
                  <span className="text-[10px] font-mono text-zinc-500 group-hover:text-indigo-400">{agentAddress.slice(0,12)}...{agentAddress.slice(-10)}</span>
                  <Copy className="w-2.5 h-2.5 text-zinc-700 group-hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition-all" />
                </div>
              )}
            </div>
            <textarea value={objective} onChange={(e) => setObjective(e.target.value)} rows={3} className="w-full bg-black border border-white/5 rounded-2xl px-6 py-5 text-sm focus:border-indigo-500/50 outline-none transition-all font-medium resize-none leading-relaxed text-zinc-200 font-mono shadow-2xl placeholder:text-zinc-800" placeholder="Protocol objectives..." />
            <div className="flex justify-end mt-4 gap-4">
              <button onClick={clearLogs} className="p-3 text-zinc-600 hover:text-red-400 transition-colors" title="Clear Workspace"><Trash2 className="w-4 h-4" /></button>
              <button onClick={runMission} disabled={isRunning} className={cn("px-8 py-3 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] flex items-center gap-3 transition-all", isRunning ? "bg-zinc-900 text-zinc-700 cursor-not-allowed border border-white/5" : "bg-white text-black hover:scale-[1.02] hover:bg-slate-100 shadow-xl shadow-white/5 active:scale-95")}>
                {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current text-black" />}
                {isRunning ? "Running Loop" : "Execute Mission"}
              </button>
            </div>
          </div>

          <div className="px-8 py-4 border-b border-white/5 flex items-center gap-4 bg-black/40">
            <Search className="w-4 h-4 text-zinc-700" />
            <input value={searchQuery} onChange={(e) => setSearchSearchQuery(e.target.value)} placeholder="Filter audit trail..." className="bg-transparent border-none text-xs w-full focus:outline-none text-zinc-500 placeholder:text-zinc-800 font-bold uppercase tracking-widest" />
          </div>

          <div className="flex-1 overflow-y-auto p-8 space-y-5 scroll-smooth custom-scrollbar bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.03)_0%,transparent_100%)]" ref={scrollRef}>
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-900 space-y-6 opacity-40">
                <Terminal className="w-20 h-20 stroke-[1px]" />
                <p className="font-black uppercase tracking-[0.5em] text-[11px]">System Idle</p>
              </div>
            ) : (
              filteredLogs.map((log, i) => (
                <div key={i} className={cn("border rounded-2xl p-6 font-mono text-[11px] animate-in slide-in-from-bottom-4 duration-500 shadow-sm", getLogColor(log.event_type))}>
                  <div className="flex items-center justify-between mb-3 border-b border-current pb-2 opacity-40">
                    <div className="flex items-center gap-3">
                      <span className="font-black uppercase tracking-widest">{log.event_type}</span>
                      <span className="uppercase font-black tracking-widest text-[9px] bg-current/10 px-2 py-0.5 rounded-full">{log.tool_name}</span>
                    </div>
                    <span className="text-[10px] font-bold">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  <pre className="whitespace-pre-wrap break-all leading-loose font-bold text-current drop-shadow-sm">{log.output_result}</pre>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right: Audit Panel */}
        <aside className="w-80 border-l border-white/5 bg-zinc-900/10 p-8 flex flex-col gap-8 z-10 overflow-y-auto custom-scrollbar">
          <label className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-emerald-500" /> Audit Integrity</label>
          
          {sessionRoot ? (
            <div className="space-y-8 animate-in slide-in-from-right-8 duration-700">
              <div className="p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-[2rem] relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10"><CheckCircle2 className="w-16 h-16 text-emerald-500" /></div>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-8 h-8 rounded-2xl bg-emerald-500/20 flex items-center justify-center shadow-lg"><CheckCircle2 className="w-4 h-4 text-emerald-500" /></div>
                  <span className="text-xs font-black uppercase tracking-[0.2em] text-emerald-400">Notarized</span>
                </div>
                <div className="space-y-4 relative z-10">
                  <div>
                    <span className="text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em] mb-2 block">Cryptographic Root</span>
                    <div className="relative group/code">
                      <div className="text-[10px] font-mono text-zinc-400 break-all bg-black/80 p-4 rounded-2xl border border-white/5 cursor-pointer hover:text-emerald-400 transition-all duration-300 shadow-inner" onClick={() => copyToClipboard(sessionRoot, "Session Root")}>
                        {sessionRoot}
                      </div>
                      <Copy className="absolute top-3 right-3 w-3 h-3 text-zinc-700 opacity-0 group-hover/code:opacity-100 transition-opacity" />
                    </div>
                  </div>
                </div>
              </div>

              {attestationTx && (
                <div className="space-y-5">
                  <a href={`https://sepolia.basescan.org/tx/${attestationTx}`} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between w-full p-5 bg-zinc-900/80 hover:bg-zinc-800 border border-white/5 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] text-zinc-300 transition-all group shadow-2xl">
                    <span>View on BaseScan</span>
                    <ExternalLink className="w-4 h-4 text-zinc-600 group-hover:text-white transition-colors" />
                  </a>
                  
                  <div className="p-5 rounded-3xl bg-black border border-white/5">
                    <div className="flex justify-between items-center mb-4">
                      <span className="text-[9px] font-black text-zinc-700 uppercase tracking-[0.3em]">Protocol Proof</span>
                      <span className="text-[8px] text-emerald-500/80 font-black px-2 py-1 bg-emerald-500/10 rounded-full">EAS-ID</span>
                    </div>
                    <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden mb-4">
                      <div className="h-full bg-emerald-500 w-full animate-pulse shadow-[0_0_12px_rgba(16,185,129,0.5)]" />
                    </div>
                    <div className="text-[9px] font-mono text-zinc-800 truncate">0x4ee2145e253098e581a38bdbb7f7c81eae64b6d9d5868063c71b562779056441</div>
                  </div>
                </div>
              )}

              <div className="pt-8 border-t border-white/5">
                <button className="w-full py-5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-3xl text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all shadow-[0_20px_40px_rgba(99,102,241,0.2)] transform hover:-translate-y-1 active:scale-95" onClick={() => toast.info("Beta Gated", { description: "Mainnet deployment is currently restricted." })}>
                  <Rocket className="w-4 h-4" /> Deploy Runtime
                </button>
                <p className="text-center text-[9px] font-black text-zinc-700 mt-6 uppercase tracking-[0.2em]">Promote to Eternal State</p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center py-12 text-center border-2 border-dashed border-white/5 rounded-[3rem] bg-white/[0.02] group hover:border-white/10 transition-all duration-500">
              <div className="w-16 h-16 rounded-full bg-zinc-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-inner"><Hash className="w-8 h-8 text-zinc-800" /></div>
              <p className="text-zinc-600 text-[10px] font-black uppercase tracking-[0.4em]">Audit Vault Empty</p>
              <p className="text-[9px] text-zinc-800 mt-4 max-w-[180px] font-bold leading-loose uppercase tracking-widest opacity-60 italic">Initiate agent loop to generate immutable cryptographic evidence.</p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}