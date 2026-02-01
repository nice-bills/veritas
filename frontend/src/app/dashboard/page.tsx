"use client";

import React, { useState, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  ShieldCheck, LayoutGrid, ArrowLeft, ExternalLink, 
  Trash2, Play, Hash, Calendar, Wallet, Bot, Sparkles
} from 'lucide-react';
import { toast, Toaster } from 'sonner';

interface AgentHistoryItem {
  id: string;
  name: string;
  objective: string;
  root: string;
  tx?: string;
  timestamp: number;
  address?: string;
}

// Particle background component
function ParticleBackground() {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    let animationId: number;
    let particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      opacity: number;
    }> = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    const createParticles = () => {
      particles = [];
      const count = Math.floor((canvas.width * canvas.height) / 15000);
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
        
        // Draw connections
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
    
    window.addEventListener('resize', () => {
      resize();
      createParticles();
    });
    
    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
    };
  }, []);
  
  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}

// Animated grid background
function GridBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
      <div className="absolute inset-0 animated-grid opacity-20" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#0a0a0a]" />
    </div>
  );
}

const formatAddress = (address?: string): string => {
  if (!address) return 'Unknown';
  return `${address.slice(0,6)}...${address.slice(-4)}`;
};

// Agent card component with animations
function AgentCard({ agent, index, onRerun }: { 
  agent: AgentHistoryItem; 
  index: number; 
  onRerun: (agent: AgentHistoryItem) => void;
}) {
  return (
    <div 
      className="glass rounded-2xl p-6 hover-lift card-glow group relative overflow-hidden opacity-0 animate-scale-in"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Top accent line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="flex justify-between items-start mb-5">
        <div>
          <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
            {agent.name}
          </h3>
          <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-mono bg-white/5 rounded-lg px-2 py-1 w-fit">
            <Wallet className="w-3 h-3" />
            {formatAddress(agent.address)}
          </div>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 p-2 rounded-xl glow-green">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
        </div>
      </div>

      <div className="space-y-3 mb-5">
        <div className="bg-black/40 rounded-xl p-3 border border-white/5">
          <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Objective</p>
          <p className="text-xs text-zinc-300 line-clamp-2 leading-relaxed">{agent.objective}</p>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-black/40 rounded-xl p-3 border border-white/5">
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Hash className="w-3 h-3" /> 
              Session Root
            </p>
            <p className="text-[10px] font-mono text-zinc-400 truncate" title={agent.root}>
              {agent.root.slice(0, 12)}...
            </p>
          </div>
          <div className="bg-black/40 rounded-xl p-3 border border-white/5">
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Calendar className="w-3 h-3" /> 
              Deployed
            </p>
            <p className="text-[10px] font-mono text-zinc-400">
              {new Date(agent.timestamp).toLocaleDateString(undefined, { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
              })}
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button 
          onClick={() => onRerun(agent)} 
          className="flex-1 py-3 bg-white text-black rounded-xl font-semibold text-xs uppercase tracking-wider hover:bg-zinc-200 transition-all btn-press flex items-center justify-center gap-2 group/btn"
        >
          <Play className="w-3 h-3 fill-current" /> 
          <span>Rerun Agent</span>
        </button>
        {agent.tx && (
          <a 
            href={`https://sepolia.basescan.org/tx/${agent.tx}`} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="px-4 py-3 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white rounded-xl border border-white/10 transition-all flex items-center justify-center"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  );
}

// Empty state component
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-zinc-600 space-y-6 animate-fade-in">
      <div className="w-24 h-24 bg-white/5 rounded-3xl flex items-center justify-center glow-white">
        <LayoutGrid className="w-10 h-10 opacity-50" />
      </div>
      <div className="text-center space-y-2">
        <p className="font-bold uppercase tracking-[0.2em] text-xs text-zinc-500">No Agents Deployed</p>
        <p className="text-xs text-zinc-600 max-w-xs">Create your first AI agent to start trading on Base with cryptographic proof</p>
      </div>
      <Link 
        href="/" 
        className="px-6 py-3 bg-white text-black rounded-xl font-semibold text-xs uppercase tracking-wider hover:bg-zinc-200 transition-all btn-press flex items-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        Create New Agent
      </Link>
    </div>
  );
}

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
  const [isLoaded, setIsLoaded] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const handleClearHistory = useCallback(() => {
    if (confirm("Are you sure you want to clear all agent history? This action cannot be undone.")) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('veritas_agent_history');
      }
      setHistory([]);
      toast.success("All agent history cleared");
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
    toast.success("Agent configuration loaded", {
      description: "Redirecting to playground..."
    });
    router.push('/');
  }, [router]);

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a] text-white overflow-hidden relative">
      <ParticleBackground />
      <GridBackground />
      <Toaster position="bottom-right" theme="dark" />

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl z-10">
        <div className="flex items-center gap-4">
          <Link 
            href="/" 
            aria-label="Back to playground" 
            className="p-2 hover:bg-white/10 rounded-xl text-zinc-500 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <h1 className="text-lg font-bold tracking-tight">
              My Agents
              <span className="ml-3 px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[10px] rounded-full border border-emerald-500/20">
                {history.length}
              </span>
            </h1>
          </div>
        </div>
        
        {history.length > 0 && (
          <button 
            onClick={handleClearHistory} 
            aria-label="Clear history" 
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 rounded-xl border border-white/10 text-xs font-semibold uppercase tracking-wider transition-all"
          >
            <Trash2 className="w-4 h-4" /> 
            Clear History
          </button>
        )}
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6 z-10 custom-scrollbar">
        {!isLoaded ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : history.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-7xl mx-auto">
            {history.map((agent, i) => (
              <AgentCard 
                key={agent.id || i} 
                agent={agent} 
                index={i}
                onRerun={loadAgent}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
