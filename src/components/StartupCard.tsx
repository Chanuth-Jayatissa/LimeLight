import React, { useState, useRef } from 'react';
import { Play, Pause, Activity, CheckCircle2, ChevronDown, ChevronUp, Quote, Sparkles, ExternalLink } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, LineChart, Line, XAxis, Tooltip } from 'recharts';

export interface StartupData {
  id: string;
  name: string;
  logo: string;
  tag: string;
  status: string;
  hook: string;
  problem: string;
  solution: string;
  videoUrl: string;
  audioUrl: string;
  websiteUrl: string;
  tokenPrice: number;
  marketCap: number;
  radarData: { subject: string; score: number }[];
  lineData: { month: string; users: number }[];
}

export default function StartupCard({ startup }: { startup: StartupData; key?: React.Key }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const current = audioRef.current.currentTime;
      const duration = audioRef.current.duration;
      if (duration > 0) {
        setProgress((current / duration) * 100);
      }
    }
  };

  const toggleAudio = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (audioRef.current && videoRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        setIsPlaying(true);
        const audioPromise = audioRef.current.play();
        const videoPromise = videoRef.current.play();
        
        if (audioPromise !== undefined) {
          audioPromise.catch(error => {
            console.error("Audio playback failed:", error);
            setIsPlaying(false);
          });
        }
        if (videoPromise !== undefined) {
          videoPromise.catch(error => {
            console.error("Video playback failed:", error);
            setIsPlaying(false);
          });
        }
      }
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setProgress(0);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  const handleInvest = async () => {
    if (!amount || isNaN(Number(amount))) return;
    setIsProcessing(true);
    
    // Simulate Web3 transaction on Solana
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    setIsProcessing(false);
    setIsSuccess(true);
    setAmount('');
    
    setTimeout(() => setIsSuccess(false), 3000);
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
      {/* Immersive Audio & Video Player (Top section) */}
      <div 
        className="relative h-72 w-full bg-zinc-950 group cursor-pointer overflow-hidden"
        onClick={toggleAudio}
      >
        <video 
          ref={videoRef}
          loop 
          muted 
          playsInline 
          src={startup.videoUrl || undefined}
          className={`w-full h-full object-cover transition-all duration-700 ${
            isPlaying ? 'opacity-100 scale-105' : 'opacity-40 group-hover:opacity-50 scale-100'
          }`}
        />
        <div className={`absolute inset-0 transition-opacity duration-700 pointer-events-none ${
          isPlaying 
            ? 'bg-gradient-to-t from-zinc-950 via-transparent to-transparent opacity-60' 
            : 'bg-gradient-to-t from-zinc-900 via-zinc-900/40 to-transparent opacity-100'
        }`} />

        {/* Audio Element */}
        <audio 
          ref={audioRef} 
          src={startup.audioUrl || undefined} 
          onEnded={handleEnded} 
          onTimeUpdate={handleTimeUpdate}
        />

        {/* Header Overlay */}
        <div className={`absolute top-6 left-6 right-6 flex justify-between items-start z-10 transition-opacity duration-500 ${isPlaying ? 'opacity-0 group-hover:opacity-100' : 'opacity-100'}`}>
           <div className="flex items-center gap-4">
             <div className="w-12 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-bold text-2xl text-emerald-400 shadow-lg">
               {startup.logo}
             </div>
             <div>
               <h3 className="text-2xl font-bold text-white drop-shadow-md">{startup.name}</h3>
               <div className="flex items-center gap-2 mt-1.5">
                 <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/30 backdrop-blur-sm">
                   {startup.tag}
                 </span>
                 <span className="px-2.5 py-1 bg-blue-500/20 text-blue-400 text-xs font-semibold rounded-full border border-blue-500/30 flex items-center gap-1.5 backdrop-blur-sm">
                   <Activity className="w-3 h-3 animate-pulse" /> {startup.status}
                 </span>
               </div>
             </div>
           </div>

           <div className="px-3 py-1.5 bg-zinc-950/60 border border-zinc-700/50 rounded-full backdrop-blur-md flex items-center gap-1.5 shadow-xl">
             <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
             <span className="text-[10px] font-medium text-zinc-300 uppercase tracking-widest">AI Pitch</span>
           </div>
        </div>

        {/* Play Button Overlay */}
        <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
           <div 
             className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 backdrop-blur-md ${
               isPlaying 
                 ? 'bg-zinc-900/40 border border-zinc-700/50 text-white opacity-0 group-hover:opacity-100 scale-90 group-hover:scale-100' 
                 : 'bg-emerald-500/90 text-zinc-950 shadow-[0_0_30px_rgba(16,185,129,0.3)] opacity-100 scale-100 group-hover:scale-110'
             }`}
           >
             {isPlaying ? <Pause className="w-8 h-8 fill-current" /> : <Play className="w-8 h-8 fill-current ml-1" />}
           </div>
        </div>

        {/* Audio Visualizer (Shows when playing) */}
        {isPlaying && (
          <div className="absolute bottom-6 right-6 flex items-end gap-1 h-6 z-10">
            {[...Array(4)].map((_, i) => (
              <div 
                key={i} 
                className="w-1.5 bg-emerald-400 rounded-full animate-pulse" 
                style={{ 
                  height: `${Math.random() * 60 + 40}%`, 
                  animationDelay: `${i * 0.15}s`,
                  animationDuration: '0.5s'
                }} 
              />
            ))}
          </div>
        )}

        {/* Progress Bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-800/50 z-10">
          <div 
            className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-100 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="p-8 space-y-10 flex-1 flex flex-col">
        {/* Startup Identity & AI Pitch */}
        <div className="space-y-6">
          <div className="relative pt-4 pb-2">
            <Quote className="absolute top-0 left-0 w-8 h-8 text-emerald-500/20 rotate-180 -translate-x-2 -translate-y-2" />
            <h4 className="text-2xl font-medium text-white leading-snug italic relative z-10">
              "{startup.hook}"
            </h4>
          </div>
          <div className="flex flex-col gap-4 text-sm">
            <div className="bg-zinc-950/50 p-5 rounded-xl border border-zinc-800/50">
              <span className="text-zinc-500 font-semibold uppercase tracking-wider text-xs block mb-2">The Problem</span>
              <p className="text-zinc-300 leading-relaxed text-base">{startup.problem}</p>
            </div>
            <div className="bg-zinc-950/50 p-5 rounded-xl border border-zinc-800/50">
              <span className="text-zinc-500 font-semibold uppercase tracking-wider text-xs block mb-2">The Solution</span>
              <p className="text-zinc-300 leading-relaxed text-base">{startup.solution}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mt-2">
          <a 
            href={startup.websiteUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 py-3 flex items-center justify-center gap-2 bg-zinc-800/40 hover:bg-zinc-700/50 text-zinc-200 hover:text-white rounded-xl transition-colors text-sm font-medium border border-zinc-700/50"
          >
            Visit Website <ExternalLink className="w-4 h-4" />
          </a>
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-1 py-3 flex items-center justify-center gap-2 text-zinc-400 hover:text-white hover:bg-zinc-800/50 rounded-xl transition-colors text-sm font-medium border border-transparent hover:border-zinc-700/50"
          >
            {isExpanded ? (
              <>Hide Analysis & Invest <ChevronUp className="w-4 h-4" /></>
            ) : (
              <>View Analysis & Invest <ChevronDown className="w-4 h-4" /></>
            )}
          </button>
        </div>

        {isExpanded && (
          <div className="space-y-10 flex-1 flex flex-col animate-in fade-in slide-in-from-top-4 duration-500">
            {/* The "Potential" Dashboard */}
            <div>
          <h4 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4" /> AI Venture Analysis
          </h4>
          <div className="flex flex-col gap-6 bg-zinc-950/30 p-6 rounded-xl border border-zinc-800/30">
            <div className="h-56 flex flex-col items-center">
              <h5 className="text-xs text-zinc-500 font-medium mb-2">Core Metrics Score</h5>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={startup.radarData}>
                  <PolarGrid stroke="#3f3f46" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="h-56 flex flex-col">
              <h5 className="text-xs text-zinc-500 font-medium mb-2 text-center">Projected User Growth (12m)</h5>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={startup.lineData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                  <XAxis dataKey="month" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px', borderRadius: '8px' }}
                    itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                    labelStyle={{ color: '#a1a1aa', marginBottom: '4px' }}
                  />
                  <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981', stroke: '#18181b', strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Web3 Investment Interface */}
        <div className="border-t border-zinc-800 pt-8 mt-auto">
          <div className="flex flex-col 2xl:flex-row 2xl:items-center justify-between gap-4 mb-6">
            <div>
              <p className="text-sm text-zinc-400 mb-1">Current Token Price</p>
              <p className="text-3xl font-mono font-semibold text-white">${startup.tokenPrice.toFixed(4)}</p>
            </div>
            <div className="2xl:text-right">
              <p className="text-sm text-zinc-400 mb-1">Bonding Curve Market Cap</p>
              <p className="text-2xl font-mono font-medium text-emerald-500">${startup.marketCap.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span className="text-zinc-500 font-mono font-medium">SOL</span>
              </div>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.1"
                min="0"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-4 pl-14 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono text-lg transition-all"
              />
            </div>
            <button
              onClick={handleInvest}
              disabled={isProcessing || !amount || Number(amount) <= 0}
              className="bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold px-10 py-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[180px] text-lg shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)]"
            >
              {isProcessing ? (
                <span className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-zinc-950/30 border-t-zinc-950 rounded-full animate-spin" />
                  Processing...
                </span>
              ) : isSuccess ? (
                <span className="flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6" />
                  Success
                </span>
              ) : (
                'INVEST'
              )}
            </button>
          </div>
        </div>
          </div>
        )}
      </div>
    </div>
  );
}
