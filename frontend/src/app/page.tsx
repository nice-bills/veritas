"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Play, Settings, X, Bot, CheckCircle2, ExternalLink, 
  Sparkles, Copy, LayoutGrid, Square, Send, Clock,
  Activity, Wallet, Zap
} from 'lucide-react';
import { toast, Toaster } from 'sonner';
import Link from 'next/link';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_BASE_URL = API_BASE_URL.replace("http", "ws");

// Types
interface LogEntry {
  event_type: string;
  tool_name: string;
  output_result: string | number | boolean | object;
  timestamp: number;
}

interface RunningAgent {
  id: string;
  name: string;
  address: string;
  status: 'running' | 'stopped';
  startedAt: number;
}

// Simplified templates - 3 essential ones only
const TEMPLATES = [
  {
    id: "balance",
    name: "Check Balance",
    capabilities: ["wallet"],
    objective: "Check my ETH balance and display it"
  },
  {
    id: "swap",
    name: "Token Swap",
    capabilities: ["wallet", "token", "trade"],
    objective: "Swap 0.01 ETH to USDC and show the price"
  },
  {
    id: "yield",
    name: "Supply to Aave",
    capabilities: ["wallet", "token", "aave"],
    objective: "Supply 50 USDC to Aave and show the APY"
  }
];

const CAPABILITIES = [
  { id: "wallet", name: "Wallet" },
  { id: "token", name: "Tokens" },
  { id: "trade", name: "Trading" },
  { id: "aave", name: "Aave" },
  { id: "compound", name: "Compound" },
  { id: "nft", name: "NFTs" },
  { id: "basename", name: "Basenames" },
  { id: "social", name: "Social" },
  { id: "payments", name: "Payments" },
  { id: "wow", name: "Creator" },
  { id: "nillion", name: "Privacy" },
  { id: "pyth", name: "Pyth" },
  { id: "chainlink", name: "Chainlink" },
  { id: "onramp", name: "Onramp" }
];

// Particle Background Component
function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    let animationId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; size: number; opacity: number }> = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    const createParticles = () => {
      particles = [];
      const count = Math.floor((canvas.width * canvas.height) / 20000);
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          size: Math.random() * 2 + 1,
          opacity: Math.random() * 0.3 + 0.1
        });
      }
    };
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((particle, i) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
        ctx.fill();
        
        particles.slice(i + 1).forEach((other) => {
          const dx = particle.x - other.x;
          const dy = particle.y - other.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < 100) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(other.x, other.y);
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.05 * (1 - distance / 100)})`;
            ctx.stroke();
          }
        });
      });
      animationId = requestAnimationFrame(animate);
    };
    
    resize();
    createParticles();
    animate();
    window.addEventListener('resize', () => { resize(); createParticles(); });
    return () => { cancelAnimationFrame(animationId); };
  }, []);
  
  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0" />;
}

function formatLogOutput(log: LogEntry): string {
  const result = log.output_result;
  if (typeof result === 'string' && result.startsWith('{')) {
    try {
      const parsed = JSON.parse(result);
      if (parsed.thought) return parsed.thought;
      if (parsed.balance_eth) return `Balance: ${parsed.balance_eth} ETH`;
      return JSON.stringify(parsed, null, 2);
    } catch { return result; }
  }
  return String(result);
}

function formatAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  if (mins > 60) return `${Math.floor(mins / 60)}h ${mins % 60}m`;
  return `${mins}m`;
}

export default function VeritasPlayground() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [userName, setUserName] = useState('');
  const [activeTab, setActiveTab] = useState<'templates' | 'playground' | 'capabilities' | 'running'>('templates');
  const [agentName, setAgentName] = useState('My Agent');
  const [objective, setObjective] = useState('');
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>(['wallet']);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [sessionRoot, setSessionRoot] = useState<string | null>(null);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [agentAddress, setAgentAddress] = useState<string | null>(null);
  const [runningAgents, setRunningAgents] = useState<RunningAgent[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [selectedRunningAgent, setSelectedRunningAgent] = useState<string | null>(null);
  const [persistentLogs, setPersistentLogs] = useState<Record<string, LogEntry[]>>({});
  const [showSettings, setShowSettings] = useState(false);
  const [cdpId, setCdpId] = useState('');
  const [cdpSecret, setCdpSecret] = useState('');
  const [minimaxKey, setMinimaxKey] = useState('');
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected'>('disconnected');
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/`);
        setBackendStatus(res.ok ? 'connected' : 'disconnected');
      } catch {
        setBackendStatus('disconnected');
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => { clearInterval(interval); wsRef.current?.close(); };
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('veritas_user');
      if (saved) { setUserName(saved); setShowWelcome(false); }
      setCdpId(localStorage.getItem('veritas_cdp_id') || '');
      setCdpSecret(localStorage.getItem('veritas_cdp_secret') || '');
      setMinimaxKey(localStorage.getItem('veritas_minimax_key') || '');
    }
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => { 
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight; 
  }, [logs]);

  const handleWelcome = () => { 
    if (userName.trim()) { 
      localStorage.setItem('veritas_user', userName); 
      setShowWelcome(false); 
    } 
  };

  const saveKeys = () => { 
    localStorage.setItem('veritas_cdp_id', cdpId); 
    localStorage.setItem('veritas_cdp_secret', cdpSecret); 
    localStorage.setItem('veritas_minimax_key', minimaxKey); 
    setShowSettings(false); 
    toast.success('Keys saved'); 
  };

  const toggleCapability = (capId: string) => {
    setSelectedCapabilities(prev => 
      prev.includes(capId) ? prev.filter(id => id !== capId) : [...prev, capId]
    );
  };

  const selectTemplate = (templateId: string) => {
    const template = TEMPLATES.find(t => t.id === templateId);
    if (template) {
      setSelectedCapabilities(template.capabilities);
      setObjective(template.objective);
      setAgentName(template.name);
      setActiveTab('playground');
    }
  };

  const createAgent = useCallback(async () => {
    if (!cdpId || !cdpSecret || !minimaxKey) {
      setShowSettings(true);
      return null;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentName,
          brain_provider: 'minimax',
          network: 'base-sepolia',
          capabilities: selectedCapabilities,
          cdp_api_key_id: cdpId.trim(),
          cdp_api_key_secret: cdpSecret.trim(),
          minimax_api_key: minimaxKey.trim()
        })
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Agent creation failed:', errorData);
        toast.error('Failed to create agent', { description: errorData.detail });
        return null;
      }
      const data = await res.json();
      setAgentAddress(data.address);
      return data.id;
    } catch (error) {
      console.error('Agent creation error:', error);
      toast.error('Failed to create agent');
      return null;
    }
  }, [agentName, selectedCapabilities, cdpId, cdpSecret, minimaxKey]);

  const runMission = useCallback(async () => {
    if (!objective.trim()) return;
    setIsRunning(true);
    setLogs([]);
    setSessionRoot(null);
    setAttestationTx(null);

    const id = await createAgent();
    if (!id) { setIsRunning(false); return; }

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/agents/${id}/ws?token=${encodeURIComponent(cdpId.trim())}`);
      wsRef.current = ws;
      ws.onmessage = (e) => setLogs(prev => [...prev, JSON.parse(e.data)]);
      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
      };

      const res = await fetch(`${API_BASE_URL}/agents/${id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Mission failed' }));
        throw new Error(errorData.detail || 'Mission failed');
      }
      
      const result = await res.json();
      setSessionRoot(result.session_root);
      setAttestationTx(result.attestation_tx);
      toast.success('Mission completed successfully!');
    } catch (error) {
      console.error('Mission error:', error);
      toast.error('Mission failed', { 
        description: error instanceof Error ? error.message : 'Unknown error' 
      });
    } finally {
      setIsRunning(false);
      wsRef.current?.close();
    }
  }, [objective, createAgent, cdpId]);

  const startPersistent = useCallback(async () => {
    if (!objective.trim()) return;
    const id = await createAgent();
    if (!id) return;

    try {
      await fetch(`${API_BASE_URL}/agents/${id}/start`, { method: 'POST' });
      setRunningAgents(prev => [...prev, { id, name: agentName, address: agentAddress || '', status: 'running', startedAt: Date.now() }]);
      setSelectedRunningAgent(id);
      setActiveTab('running');
      toast.success('Agent started');

      const ws = new WebSocket(`${WS_BASE_URL}/agents/${id}/ws?token=${encodeURIComponent(cdpId.trim())}`);
      ws.onmessage = (e) => {
        const log = JSON.parse(e.data);
        setPersistentLogs(prev => ({ ...prev, [id]: [...(prev[id] || []), log] }));
      };
      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
      };
    } catch (error) {
      console.error('Failed to start agent:', error);
      toast.error('Failed to start');
    }
  }, [objective, createAgent, agentName, agentAddress]);

  const stopAgent = useCallback(async (id: string) => {
    try {
      await fetch(`${API_BASE_URL}/agents/${id}/stop`, { method: 'POST' });
      setRunningAgents(prev => prev.filter(a => a.id !== id));
      if (selectedRunningAgent === id) setSelectedRunningAgent(null);
      toast.success('Stopped');
    } catch {
      toast.error('Failed to stop');
    }
  }, [selectedRunningAgent]);

  const sendMessage = useCallback(async () => {
    if (!selectedRunningAgent || !messageInput.trim()) return;
    try {
      await fetch(`${API_BASE_URL}/agents/${selectedRunningAgent}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageInput })
      });
      setMessageInput('');
      toast.success('Sent');
    } catch {
      toast.error('Failed to send');
    }
  }, [selectedRunningAgent, messageInput]);

  const copyAddress = () => {
    if (agentAddress) { navigator.clipboard.writeText(agentAddress); toast.success('Copied'); }
  };

  if (showWelcome) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center p-6 relative overflow-hidden">
        <ParticleBackground />
        <div className="absolute inset-0 animated-grid opacity-30 pointer-events-none" />
        <div className="absolute inset-0 aurora opacity-50" />
        
        <div className="relative z-10 text-center max-w-md w-full animate-fade-in-up">
          {/* Animated Logo */}
          <div className="relative w-24 h-24 mx-auto mb-8">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/30 to-blue-500/30 rounded-2xl blur-xl animate-pulse" />
            <div className="relative w-24 h-24 bg-gradient-to-br from-emerald-500/20 to-blue-500/20 rounded-2xl flex items-center justify-center border border-white/10 shadow-2xl animate-float">
              <Bot className="w-12 h-12 text-white animate-glow" />
            </div>
          </div>
          
          {/* Animated Title */}
          <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 bg-clip-text text-transparent animate-fade-in-up stagger-1">
            Veritas
          </h1>
          <p className="text-zinc-400 text-lg mb-2 animate-fade-in-up stagger-2">The Crypto AI Agent Playground</p>
          <p className="text-zinc-600 text-sm mb-10 animate-fade-in-up stagger-3">Deploy autonomous agents on Base with cryptographic proof</p>
          
          {/* Animated Input */}
          <div className="relative mb-4 animate-fade-in-up stagger-4">
            <input
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleWelcome()}
              placeholder="Enter your name"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-4 text-sm text-white placeholder:text-zinc-600 focus:border-emerald-500/50 focus:outline-none transition-all hover:border-white/20"
              autoFocus
            />
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-500/0 via-emerald-500/10 to-emerald-500/0 opacity-0 hover:opacity-100 transition-opacity pointer-events-none" />
          </div>
          
          {/* Animated Button */}
          <button
            onClick={handleWelcome}
            disabled={!userName.trim()}
            className="w-full py-4 bg-gradient-to-r from-emerald-500 via-emerald-500 to-blue-500 text-white rounded-xl text-sm font-semibold hover:from-emerald-400 hover:via-emerald-400 hover:to-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-[1.02] btn-press animate-fade-in-up stagger-5 relative overflow-hidden group"
          >
            <span className="relative z-10">Enter Playground</span>
            <Sparkles className="w-4 h-4 relative z-10 animate-bounce-subtle" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
          </button>
          
          {/* Animated Capability Badges */}
          <div className="mt-12 flex items-center justify-center gap-2 flex-wrap animate-fade-in-up stagger-5">
            {['Wallet', 'Tokens', 'Aave', 'Trading', 'NFTs', '+9 more'].map((badge, i) => (
              <span 
                key={badge} 
                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-zinc-400 border border-white/5 hover:border-white/20 transition-all hover:scale-105 cursor-default animate-fade-in"
                style={{ animationDelay: `${0.6 + i * 0.1}s` }}
              >
                {badge}
              </span>
            ))}
          </div>
        </div>
        <Toaster position="bottom-right" theme="dark" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      <ParticleBackground />
      <div className="absolute inset-0 animated-grid opacity-30 pointer-events-none z-0" />
      <div className="absolute inset-0 aurora opacity-30 pointer-events-none z-0" />
      <Toaster position="bottom-right" theme="dark" />
      
      {/* Animated Header */}
      <header className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500/20 to-blue-500/20 rounded-lg flex items-center justify-center border border-white/10 animate-pulse">
            <Bot className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="font-semibold text-white">Veritas</span>
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full border ${backendStatus === 'connected' ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === 'connected' ? 'bg-emerald-400 status-pulse' : 'bg-red-400'}`} />
            <span className={`text-[10px] ${backendStatus === 'connected' ? 'text-emerald-400' : 'text-red-400'}`}>
              {backendStatus === 'connected' ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/dashboard" className="text-zinc-400 hover:text-white transition-colors flex items-center gap-1.5 hover:scale-105">
            <LayoutGrid className="w-4 h-4" />
            My Agents
          </Link>
          <div className="h-4 w-px bg-white/10" />
          <span className="text-zinc-500">{userName}</span>
          <button 
            onClick={() => setShowSettings(true)} 
            className="p-2 hover:bg-white/10 rounded-lg transition-all hover:scale-110"
          >
            <Settings className="w-4 h-4 text-zinc-400 hover:text-white transition-colors" />
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-5xl mx-auto p-4 relative z-10">
        {/* Animated Tabs */}
        <div className="flex gap-1 mb-6 p-1 bg-white/5 rounded-xl border border-white/5 backdrop-blur-sm">
          {[
            { id: 'templates', label: 'Templates', icon: LayoutGrid },
            { id: 'playground', label: 'Playground', icon: Activity },
            { id: 'capabilities', label: 'Capabilities', icon: Zap },
            { id: 'running', label: 'Running', count: runningAgents.length, icon: Clock }
          ].map((tab, i) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${activeTab === tab.id ? 'bg-white text-black shadow-lg scale-105' : 'text-zinc-400 hover:text-white hover:bg-white/5 hover:scale-105'}`}
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${activeTab === tab.id ? 'bg-black/20' : 'bg-emerald-500/20 text-emerald-400'}`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Templates with Animations */}
        {activeTab === 'templates' && (
          <div className="grid grid-cols-3 gap-4 animate-fade-in">
            {TEMPLATES.map((t, i) => (
              <button
                key={t.id}
                onClick={() => selectTemplate(t.id)}
                className="group p-5 bg-white/5 rounded-xl border border-white/10 hover:border-emerald-500/50 text-left transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-emerald-500/10 card-glow"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-white group-hover:text-emerald-400 transition-colors">{t.name}</h3>
                  <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
                    <Activity className="w-4 h-4 text-emerald-400" />
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {t.capabilities.map(cap => (
                    <span key={cap} className="px-2 py-0.5 bg-white/5 rounded text-[10px] text-zinc-500 border border-white/5 group-hover:border-white/10 transition-colors">
                      {cap}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Playground with Enhanced UI */}
        {activeTab === 'playground' && (
          <div className="grid grid-cols-3 gap-4 animate-fade-in">
            <div className="col-span-2 space-y-4">
              <div className="glass-animated rounded-xl p-5 border border-white/10">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                    <Bot className="w-4 h-4 text-emerald-400" />
                  </div>
                  <h3 className="font-semibold text-white">Agent Configuration</h3>
                </div>
                
                <label className="text-xs text-zinc-500 mb-2 block">Agent Name</label>
                <input
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm mb-4 focus:border-emerald-500/50 focus:outline-none transition-all"
                  placeholder="My Trading Agent"
                />
                
                <label className="text-xs text-zinc-500 mb-2 block">Mission Objective</label>
                <textarea
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  rows={5}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono focus:border-emerald-500/50 focus:outline-none transition-all"
                  placeholder="What should the agent do?"
                />
                
                <div className="flex gap-3 mt-5">
                  {agentAddress && (
                    <button 
                      onClick={copyAddress} 
                      className="px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 font-mono hover:bg-emerald-500/20 transition-colors flex items-center gap-1"
                    >
                      {formatAddress(agentAddress)}
                      <Copy className="w-3 h-3" />
                    </button>
                  )}
                  <div className="flex-1" />
                  <button
                    onClick={startPersistent}
                    disabled={!objective.trim()}
                    className="px-4 py-2.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-lg text-sm font-medium hover:bg-emerald-500/20 disabled:opacity-50 transition-all hover:scale-105"
                  >
                    <Clock className="w-4 h-4 inline mr-1" />
                    Start Persistent
                  </button>
                  <button
                    onClick={runMission}
                    disabled={isRunning || !objective.trim()}
                    className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-lg text-sm font-semibold hover:from-emerald-400 hover:to-emerald-500 disabled:opacity-50 transition-all hover:scale-105 btn-press shadow-lg shadow-emerald-500/20 flex items-center gap-2"
                  >
                    {isRunning ? (
                      <><Activity className="w-4 h-4 animate-spin" /> Running...</>
                    ) : (
                      <><Play className="w-4 h-4" /> Run Agent</>
                    )}
                  </button>
                </div>
              </div>

              {/* Animated Logs */}
              <div className="glass rounded-xl p-5 border border-white/10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm text-zinc-400 flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    Output
                  </h3>
                  {logs.length > 0 && (
                    <span className="text-xs text-zinc-600">{logs.length} events</span>
                  )}
                </div>
                <div ref={scrollRef} className="font-mono text-xs space-y-2 max-h-[200px] overflow-y-auto custom-scrollbar">
                  {logs.map((log, i) => (
                    <div key={i} className="flex gap-3 p-1.5 rounded hover:bg-white/5 transition-colors">
                      <span className="text-zinc-600 shrink-0">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                      <span className={`uppercase font-bold shrink-0 w-16 ${log.event_type === 'ERROR' ? 'text-red-400' : log.event_type === 'THOUGHT' ? 'text-purple-400' : 'text-emerald-400'}`}>{log.event_type}</span>
                      <span className="text-zinc-500 shrink-0">{log.tool_name}</span>
                      <span className="text-zinc-400">{formatLogOutput(log)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Enhanced Sidebar */}
            <div className="space-y-4">
              <div className="glass rounded-xl p-5 border border-white/10">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-semibold text-white">Verification</h3>
                </div>
                {sessionRoot ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-emerald-400 font-medium">Verified on-chain</span>
                    </div>
                    <div className="p-3 bg-black/40 rounded-lg">
                      <p className="text-[10px] text-zinc-500 mb-1 uppercase">Session Root</p>
                      <p className="text-xs text-zinc-400 font-mono truncate">{sessionRoot}</p>
                    </div>
                    {attestationTx && (
                      <a href={`https://sepolia.basescan.org/tx/${attestationTx}`} target="_blank" className="flex items-center justify-center gap-1.5 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-zinc-400 hover:text-white transition-colors border border-white/5">
                        View on BaseScan
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-3">
                      <CheckCircle2 className="w-5 h-5 text-zinc-600" />
                    </div>
                    <p className="text-xs text-zinc-500">Run an agent to generate proof</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Capabilities with Enhanced UI */}
        {activeTab === 'capabilities' && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white">Capabilities</h2>
                <p className="text-sm text-zinc-500">Select what your agent can do</p>
              </div>
              <div className="text-sm text-zinc-500">
                <span className="text-emerald-400 font-semibold">{selectedCapabilities.length}</span> / {CAPABILITIES.length} selected
              </div>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {CAPABILITIES.map((cap, i) => (
                <button
                  key={cap.id}
                  onClick={() => toggleCapability(cap.id)}
                  className={`group p-4 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02] ${selectedCapabilities.includes(cap.id) ? 'border-emerald-500/50 bg-emerald-500/10 shadow-lg shadow-emerald-500/5' : 'border-white/10 bg-white/5 hover:border-white/30'}`}
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className={`font-medium ${selectedCapabilities.includes(cap.id) ? 'text-white' : 'text-zinc-300'}`}>{cap.name}</span>
                    {selectedCapabilities.includes(cap.id) && (
                      <div className="w-5 h-5 bg-emerald-500/20 rounded-full flex items-center justify-center">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedCapabilities.includes(cap.id) && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">Active</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Running with Enhanced UI */}
        {activeTab === 'running' && (
          <div className="animate-fade-in">
            {runningAgents.length === 0 ? (
              <div className="glass rounded-xl p-12 text-center">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Clock className="w-8 h-8 text-zinc-600" />
                </div>
                <p className="text-zinc-500 mb-2">No persistent agents running</p>
                <p className="text-xs text-zinc-600">Start a persistent agent from the Playground tab</p>
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-zinc-400 mb-2">Running Agents ({runningAgents.length})</h3>
                  {runningAgents.map((agent, i) => (
                    <div
                      key={agent.id}
                      onClick={() => setSelectedRunningAgent(agent.id)}
                      className={`p-4 glass rounded-xl border cursor-pointer transition-all duration-200 hover:scale-[1.02] ${selectedRunningAgent === agent.id ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-white/10 hover:border-white/30'}`}
                      style={{ animationDelay: `${i * 0.1}s` }}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="font-semibold text-white">{agent.name}</div>
                          <div className="text-xs text-zinc-500 font-mono">{formatAddress(agent.address)}</div>
                        </div>
                        <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full status-pulse" />
                          <span className="text-[10px] text-emerald-400">Running</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center text-xs text-zinc-500">
                        <span>{formatDuration(Math.floor((Date.now() - agent.startedAt) / 1000))}</span>
                        <button 
                          onClick={(e) => { e.stopPropagation(); stopAgent(agent.id); }}
                          className="p-1.5 hover:bg-red-500/10 hover:text-red-400 rounded-lg transition-colors"
                        >
                          <Square className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="col-span-2 space-y-4">
                  {selectedRunningAgent ? (
                    <>
                      <div className="glass-animated rounded-xl p-5 border border-white/10">
                        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                          <Send className="w-4 h-4 text-blue-400" />
                          Send Message
                        </h3>
                        <div className="flex gap-2">
                          <input
                            value={messageInput}
                            onChange={(e) => setMessageInput(e.target.value)}
                            className="flex-1 bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500/50 focus:outline-none transition-all"
                            placeholder="Enter message or objective..."
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                          />
                          <button 
                            onClick={sendMessage} 
                            className="px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-lg text-sm font-semibold hover:from-emerald-400 hover:to-emerald-500 transition-all hover:scale-105"
                          >
                            <Send className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      <div className="glass rounded-xl p-5 border border-white/10">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm text-zinc-400 flex items-center gap-2">
                            <Activity className="w-4 h-4" />
                            Live Logs
                          </h3>
                        </div>
                        <div className="font-mono text-xs space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                          {(persistentLogs[selectedRunningAgent] || []).map((log, i) => (
                            <div key={i} className="flex gap-3 p-1.5 rounded hover:bg-white/5 transition-colors">
                              <span className="text-zinc-600 shrink-0">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                              <span className={`uppercase font-bold shrink-0 w-16 ${log.event_type === 'ERROR' ? 'text-red-400' : log.event_type === 'THOUGHT' ? 'text-purple-400' : 'text-emerald-400'}`}>{log.event_type}</span>
                              <span className="text-zinc-500 shrink-0">{log.tool_name}</span>
                            </div>
                          ))}
                          {(persistentLogs[selectedRunningAgent] || []).length === 0 && (
                            <p className="text-zinc-600 text-center py-4">Waiting for activity...</p>
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="glass rounded-xl p-12 text-center">
                      <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Activity className="w-8 h-8 text-zinc-600" />
                      </div>
                      <p className="text-zinc-500">Select a running agent to view logs and send messages</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Settings with Enhanced UI */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="glass rounded-xl w-full max-w-md p-6 border border-white/10 shadow-2xl animate-scale-in">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-emerald-400" />
                <h2 className="font-semibold text-white">API Configuration</h2>
              </div>
              <button onClick={() => setShowSettings(false)} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-zinc-500 mb-1.5 block">CDP API Key ID</label>
                <input value={cdpId} onChange={(e) => setCdpId(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-zinc-300 focus:border-emerald-500/50 focus:outline-none transition-all" placeholder="organizations/.../apiKeys/..." />
              </div>
              <div>
                <label className="text-xs text-zinc-500 mb-1.5 block">CDP API Key Secret</label>
                <textarea value={cdpSecret} onChange={(e) => setCdpSecret(e.target.value)} rows={3} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-zinc-300 resize-none focus:border-emerald-500/50 focus:outline-none transition-all" placeholder="-----BEGIN EC PRIVATE KEY-----" />
              </div>
              <div>
                <label className="text-xs text-zinc-500 mb-1.5 block">MiniMax API Key</label>
                <input type="password" value={minimaxKey} onChange={(e) => setMinimaxKey(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-zinc-300 focus:border-emerald-500/50 focus:outline-none transition-all" placeholder="sk-..." />
              </div>
              <button onClick={saveKeys} className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-lg text-sm font-semibold hover:from-emerald-400 hover:to-emerald-500 transition-all shadow-lg shadow-emerald-500/20">
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
