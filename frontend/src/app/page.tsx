"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, ShieldCheck, Terminal, Settings, X, Database,
  Wallet, Zap, MessageSquare, Fingerprint, Coins, Lock, Code2, Rocket,
  Activity, CreditCard, DollarSign, Copy, RefreshCw, Search, ChevronRight,
  Trash2, Download, QrCode, LayoutGrid, ChevronDown, ChevronUp, Layers, CheckCircle2,
  ExternalLink, Hash
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

// Grouped Capabilities
const CAPABILITY_GROUPS = [
  {
    name: "Core",
    items: [
      { id: 'wallet', name: 'Wallet', icon: Wallet },
      { id: 'token', name: 'Tokens', icon: Coins },
      { id: 'nft', name: 'NFTs', icon: Database },
    ]
  },
  {
    name: "DeFi",
    items: [
      { id: 'aave', name: 'Aave', icon: Zap },
      { id: 'compound', name: 'Compound', icon: Zap },
      { id: 'trading', name: 'Trading', icon: Activity },
    ]
  },
  {
    name: "Identity & Social",
    items: [
      { id: 'basename', name: 'Basenames', icon: Fingerprint },
      { id: 'social', name: 'Social', icon: MessageSquare },
      { id: 'privacy', name: 'Privacy', icon: Lock },
    ]
  },
  {
    name: "Infrastructure",
    items: [
      { id: 'pyth', name: 'Pyth Oracle', icon: Activity },
      { id: 'onramp', name: 'Onramp', icon: CreditCard },
      { id: 'payments', name: 'Payments', icon: DollarSign },
    ]
  }
];

// Templates Config
const TEMPLATES = [
  {
    id: 'arbitrage',
    name: 'Arbitrage Hunter',
    objective: 'Check ETH price on Pyth and compare with Uniswap pools. If there is a >1% spread, simulate a trade to capture profit.',
    caps: ['wallet', 'token', 'pyth', 'trading']
  },
  {
    id: 'rebalance',
    name: 'Portfolio Guard',
    objective: 'Check my ETH balance. If it is greater than 0.005 ETH, transfer 0.0001 ETH to the secure vault: 0x000000000000000000000000000000000000dEaD',
    caps: ['wallet', 'token', 'trading']
  },
  {
    id: 'yield',
    name: 'Yield Optimizer',
    objective: 'Check my USDC balance and supply it to Aave V3 to earn yield.',
    caps: ['wallet', 'token', 'aave']
  },
  {
    id: 'basename',
    name: 'Identity Manager',
    objective: 'Register a new .basetest.eth name for this agent and verify it on-chain.',
    caps: ['wallet', 'basename']
  },
  {
    id: 'monitor',
    name: 'Whale Monitor',
    objective: 'Monitor the vitalik.eth address. If it moves funds, log an alert.',
    caps: ['data', 'basename']
  }
];

export default function VeritasPlayground() {
  const [agentName, setAgentName] = useState('Sentinel-1');
  const [brainProvider, setBrainProvider] = useState('minimax');
  const [selectedCaps, setSelectedCaps] = useState<string[]>(['wallet', 'token', 'basename', 'aave']);
  const [objective, setObjective] = useState('Check my balance. If I have ETH, transfer 0.0001 ETH to 0x000000000000000000000000000000000000dEaD to secure it.');
  const [searchQuery, setSearchSearchQuery] = useState('');
  
  // UI Toggles
  const [showTemplates, setShowTemplates] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['Core', 'DeFi']);
  
  // API Keys
  const [cdpId, setCdpId] = useState('');
  const [cdpSecret, setCdpSecret] = useState('');
  const [minimaxKey, setMinimaxKey] = useState('');
  
  // Runtime State
  const [isRunning, setIsRunning] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const [sessionRoot, setSessionRoot] = useState<string | null>(null);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [agentAddress, setAgentAddress] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Load config
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
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [logs]);

  const toggleGroup = (name: string) => {
    setExpandedGroups(prev => prev.includes(name) ? prev.filter(g => g !== name) : [...prev, name]);
  };

  const toggleCap = (id: string) => {
    setSelectedCaps(prev => prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]);
  };

  const saveKeys = () => {
    localStorage.setItem('veritas_cdp_id', cdpId);
    localStorage.setItem('veritas_cdp_secret', cdpSecret);
    localStorage.setItem('veritas_minimax_key', minimaxKey);
    setShowSettings(false);
    toast.success("Credentials secured");
  };

  const downloadProof = () => {
    const data = { session_root: sessionRoot, logs, timestamp: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `veritas-proof-${Date.now()}.json`;
    a.click();
    toast.success("Proof downloaded");
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
      
      if (!createRes.ok) throw new Error((await createRes.json()).detail || "Initialization failed");
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
      
      if (!runRes.ok) throw new Error((await runRes.json()).detail || "Execution failed");
      const result = await runRes.json();

      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
      
      const historyItem = { id: agentData.id, name: agentName, objective, root: result.session_root, tx: result.attestation_tx, timestamp: Date.now(), address: agentData.address };
      const hist = JSON.parse(localStorage.getItem('veritas_agent_history') || '[]');
      localStorage.setItem('veritas_agent_history', JSON.stringify([historyItem, ...hist]));

      toast.success("Audit Verified");
      ws.close();
    } catch (error: any) {
      toast.error("Error", { description: error.message });
      setLogs(prev => [...prev, { event_type: 'ERROR', tool_name: 'System', output_result: error.message, timestamp: Date.now()/1000 }]);
    } finally {
      setIsRunning(false);
    }
  };

  const filteredLogs = logs.filter(log => 
    log.tool_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.output_result.toString().toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatLogOutput = (log: any) => {
    try {
      if (typeof log.output_result === 'string' && (log.output_result.trim().startsWith('{') || log.output_result.trim().startsWith('['))) {
        const parsed = JSON.parse(log.output_result);
        if (parsed.thought) return parsed.thought;
        if (parsed.balance_eth) return `Balance: ${parsed.balance_eth} ETH`;
        if (parsed.price) return `Price: $${parsed.price}`;
        if (parsed.tx_hash) return `Transaction: ${parsed.tx_hash}`;
        return JSON.stringify(parsed, null, 2);
      }
      return log.output_result;
    } catch {
      return log.output_result;
    }
  };

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
    <div className="flex flex-col h-screen bg-[#09090b] text-zinc-300 font-sans overflow-hidden">
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2"><Settings className="w-4 h-4" /> System Configuration</h2>
              <button onClick={() => setShowSettings(false)}><X className="w-4 h-4 hover:text-white transition-colors" /></button>
            </div>
            <div className="space-y-4">
              <input value={cdpId} onChange={(e) => setCdpId(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-lg px-3 py-2 text-xs focus:border-zinc-600 outline-none transition-all font-mono" placeholder="CDP Key Name" />
              <textarea rows={3} value={cdpSecret} onChange={(e) => setCdpSecret(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-lg px-3 py-2 text-xs font-mono focus:border-zinc-600 outline-none transition-all" placeholder="CDP Private Key" />
              <input type="password" value={minimaxKey} onChange={(e) => setMinimaxKey(e.target.value)} className="w-full bg-black/50 border border-zinc-800 rounded-lg px-3 py-2 text-xs focus:border-zinc-600 outline-none transition-all font-mono" placeholder="MiniMax API Key" />
              <button onClick={saveKeys} className="w-full py-2 bg-white text-black hover:bg-zinc-200 rounded-lg font-semibold text-xs transition-colors">Save Credentials</button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="h-14 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 bg-white rounded flex items-center justify-center"><ShieldCheck className="text-black w-4 h-4" /></div>
          <span className="text-sm font-bold text-white tracking-tight">Veritas <span className="text-zinc-500 font-normal">Runtime</span></span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-medium text-zinc-400">Base Sepolia</span>
          </div>
          <Link href="/dashboard" className="hover:text-white transition-colors" title="Agent History"><LayoutGrid className="w-4 h-4" /></Link>
          <button onClick={() => setShowSettings(true)} className="hover:text-white transition-colors"><Settings className="w-4 h-4" /></button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: Configuration */}
        <aside className="w-72 border-r border-zinc-800 bg-zinc-900/30 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-zinc-800">
            <label className="text-[10px] uppercase font-bold text-zinc-500 mb-2 block">Agent Identity</label>
            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500" />
              <input value={agentName} onChange={(e) => setAgentName(e.target.value)} className="bg-transparent border-none text-xs font-medium text-white w-full focus:outline-none" placeholder="Name..." />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
            {/* Templates Dropdown */}
            <div>
              <button onClick={() => setShowTemplates(!showTemplates)} className="flex items-center justify-between w-full text-xs font-bold text-zinc-400 hover:text-white mb-2 group">
                <span className="flex items-center gap-2"><Zap className="w-3.5 h-3.5" /> Strategy Templates</span>
                {showTemplates ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              {showTemplates && (
                <div className="space-y-1 pl-2 border-l border-zinc-800 ml-1.5 animate-in slide-in-from-top-2 duration-200">
                  {TEMPLATES.map(t => (
                    <button key={t.id} onClick={() => { setObjective(t.objective); setSelectedCaps(t.caps); toast.success("Template Loaded"); }} className="w-full text-left px-3 py-2 text-[11px] text-zinc-500 hover:text-white hover:bg-zinc-800/50 rounded transition-colors truncate">
                      {t.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Capability Groups (Accordion) */}
            <div className="space-y-4">
              {CAPABILITY_GROUPS.map(group => (
                <div key={group.name}>
                  <button onClick={() => toggleGroup(group.name)} className="flex items-center justify-between w-full text-xs font-bold text-zinc-400 hover:text-white mb-2">
                    <span className="flex items-center gap-2"><Layers className="w-3.5 h-3.5" /> {group.name}</span>
                    {expandedGroups.includes(group.name) ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                  
                  {expandedGroups.includes(group.name) && (
                    <div className="grid grid-cols-1 gap-1 pl-2 border-l border-zinc-800 ml-1.5 animate-in slide-in-from-top-2 duration-200">
                      {group.items.map(cap => (
                        <button key={cap.id} onClick={() => toggleCap(cap.id)} className={cn("flex items-center gap-3 px-3 py-2 rounded text-[11px] font-medium transition-all text-left", selectedCaps.includes(cap.id) ? "bg-white/10 text-white" : "text-zinc-500 hover:bg-zinc-800/50")}>
                          <div className={cn("w-1.5 h-1.5 rounded-full", selectedCaps.includes(cap.id) ? "bg-emerald-500" : "bg-zinc-700")} />
                          {cap.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main: Execution */}
        <section className="flex-1 flex flex-col min-w-0 bg-[#0c0c0e] relative">
          <div className="p-6 border-b border-zinc-800 bg-zinc-900/10">
            <div className="flex justify-between items-center mb-3">
              <label className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-2"><Code2 className="w-3.5 h-3.5" /> Execution Logic</label>
              {agentAddress && <span className="text-[10px] font-mono text-zinc-500 cursor-pointer hover:text-white" onClick={() => {navigator.clipboard.writeText(agentAddress); toast.success("Address Copied")}}>{agentAddress}</span>}
            </div>
            <textarea value={objective} onChange={(e) => setObjective(e.target.value)} className="w-full bg-[#050505] border border-zinc-800 rounded-xl p-4 text-sm font-mono text-zinc-300 focus:border-zinc-600 outline-none resize-none min-h-[100px]" placeholder="Describe the autonomous mission..." />
            <div className="flex justify-between items-center mt-4">
              <div className="flex gap-2">
                <button onClick={() => setLogs([])} className="p-2 hover:bg-zinc-800 rounded text-zinc-500 transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
              <button onClick={runMission} disabled={isRunning} className={cn("px-6 py-2 bg-white text-black rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-zinc-200 transition-all", isRunning && "opacity-50 cursor-not-allowed")}>
                {isRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                {isRunning ? "Running..." : "Run Mission"}
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar" ref={scrollRef}>
            {filteredLogs.map((log, i) => (
              <div key={i} className="font-mono text-xs border-l-2 border-zinc-800 pl-4 py-1 hover:border-zinc-600 transition-colors group">
                <div className="flex items-center gap-3 mb-1">
                  <span className={cn("text-[10px] font-bold uppercase", log.event_type === 'THOUGHT' ? 'text-purple-400' : log.event_type === 'ACTION' ? 'text-emerald-400' : log.event_type === 'ERROR' ? 'text-red-400' : 'text-blue-400')}>{log.event_type}</span>
                  <span className="text-[10px] text-zinc-600">{log.tool_name}</span>
                  <span className="text-[10px] text-zinc-700 ml-auto opacity-0 group-hover:opacity-100 transition-opacity">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                </div>
                <pre className="whitespace-pre-wrap break-words leading-relaxed pl-1 text-zinc-300 font-medium drop-shadow-sm">{formatLogOutput(log)}</pre>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center opacity-20">
                <Terminal className="w-12 h-12 mb-4" />
                <span className="text-xs uppercase tracking-widest font-bold">System Ready</span>
              </div>
            )}
          </div>
        </section>

        {/* Right: Audit */}
        <aside className="w-80 border-l border-zinc-800 bg-zinc-900/20 p-6 flex flex-col gap-6 overflow-y-auto">
          <label className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-2"><ShieldCheck className="w-3.5 h-3.5" /> Verification</label>
          
          {sessionRoot ? (
            <div className="space-y-4 animate-in slide-in-from-right-4 duration-500">
              <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold text-emerald-400">Cryptographically Verified</span>
                </div>
                <div className="bg-black/50 rounded p-2 border border-white/5 cursor-pointer hover:bg-black/80 transition-colors" onClick={() => {navigator.clipboard.writeText(sessionRoot); toast.success("Root Copied")}}>
                  <p className="text-[9px] text-zinc-500 font-mono break-all">{sessionRoot}</p>
                </div>
              </div>

              {attestationTx && (
                <a href={`https://sepolia.basescan.org/tx/${attestationTx}`} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between w-full p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-400 hover:text-white hover:border-zinc-700 transition-all">
                  <span>View Attestation</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}

              <div className="flex gap-2">
                <button className="flex-1 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:bg-zinc-800 hover:text-white transition-all flex items-center justify-center gap-2" onClick={downloadProof}>
                  <Download className="w-3 h-3" /> Proof
                </button>
                <button className="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-white transition-all">
                  <QrCode className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-30 border-2 border-dashed border-zinc-800 rounded-xl">
              <Hash className="w-8 h-8 mb-2" />
              <span className="text-[10px] font-bold uppercase">No Audit Data</span>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
