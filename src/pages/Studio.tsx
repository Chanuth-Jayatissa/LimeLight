import React, { useState, useEffect } from 'react';
import { ArrowLeft, Link as LinkIcon, FileText, Loader2, CheckCircle2, Wand2, Coins, ExternalLink } from 'lucide-react';
import StartupCard, { StartupData } from '../components/StartupCard';

const mockUserStartups: StartupData[] = [
  {
    id: 'user-1',
    name: 'My Awesome AI',
    logo: 'M',
    tag: 'AI',
    status: 'Draft',
    hook: 'The best AI ever created.',
    problem: 'Things are too slow.',
    solution: 'Make them fast with AI.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    websiteUrl: 'https://example.com',
    tokenPrice: 0,
    marketCap: 0,
    radarData: [
      { subject: 'Team', score: 80 },
      { subject: 'Tech', score: 90 },
      { subject: 'Market', score: 85 },
      { subject: 'Traction', score: 50 },
    ],
    lineData: [
      { month: 'Jan', users: 100 },
      { month: 'Feb', users: 200 },
      { month: 'Mar', users: 400 },
    ]
  }
];

export default function Studio() {
  const [view, setView] = useState<'dashboard' | 'create'>('dashboard');
  const [startups, setStartups] = useState<StartupData[]>(mockUserStartups);
  
  // Create State
  const [urlInput, setUrlInput] = useState('');
  const [generationState, setGenerationState] = useState<'idle' | 'generating' | 'done'>('idle');
  const [loadingZones, setLoadingZones] = useState({ text: true, audio: true, video: true });
  
  const [generatedData, setGeneratedData] = useState<Partial<StartupData>>({});
  
  // Token Modal State
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [phantomAddress, setPhantomAddress] = useState('HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH');
  const [tokenSymbol, setTokenSymbol] = useState('');
  const [isMinting, setIsMinting] = useState(false);
  const [mintSuccess, setMintSuccess] = useState(false);
  const [txHash, setTxHash] = useState('');

  const handleGenerate = () => {
    if (!urlInput) return;
    
    setGenerationState('generating');
    setLoadingZones({ text: true, audio: true, video: true });
    setGeneratedData({
      id: 'new-startup',
      name: 'Generating...',
      logo: '?',
      tag: 'AI',
      status: 'Draft',
      hook: '...',
      problem: '...',
      solution: '...',
      videoUrl: '',
      audioUrl: '',
      websiteUrl: urlInput,
      tokenPrice: 0.001,
      marketCap: 100000,
      radarData: [
        { subject: 'Team', score: 85 },
        { subject: 'Tech', score: 90 },
        { subject: 'Market', score: 75 },
        { subject: 'Traction', score: 60 },
      ],
      lineData: [
        { month: 'Jan', users: 0 },
        { month: 'Feb', users: 1000 },
        { month: 'Mar', users: 5000 },
        { month: 'Apr', users: 15000 },
      ]
    });

    // Zone 1: Text (2s)
    setTimeout(() => {
      setLoadingZones(prev => ({ ...prev, text: false }));
      setGeneratedData(prev => ({
        ...prev,
        name: 'AutoScale AI',
        logo: 'A',
        hook: 'Elastic compute scaling for any workload.',
        problem: 'Cloud costs are spiraling out of control due to inefficient resource allocation.',
        solution: 'An AI-driven orchestrator that predicts load and scales infrastructure in real-time, saving 40% on AWS bills.',
      }));
    }, 2000);

    // Zone 2: Audio (4s)
    setTimeout(() => {
      setLoadingZones(prev => ({ ...prev, audio: false }));
      setGeneratedData(prev => ({
        ...prev,
        audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
      }));
    }, 4000);

    // Zone 3: Video (6s)
    setTimeout(() => {
      setLoadingZones(prev => ({ ...prev, video: false }));
      setGeneratedData(prev => ({
        ...prev,
        videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
      }));
      setGenerationState('done');
    }, 6000);
  };

  const handleMint = async () => {
    if (!tokenSymbol || tokenSymbol.length > 5) return;
    setIsMinting(true);
    
    // Simulate Solana smart contract interaction
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    setIsMinting(false);
    setMintSuccess(true);
    setTxHash('5xY9...aB2c');
    
    setTimeout(() => {
      setShowTokenModal(false);
    }, 2000);
  };

  const handlePublish = () => {
    const newStartup = { ...generatedData } as StartupData;
    if (txHash) {
      newStartup.status = 'Live Token';
    } else {
      newStartup.status = 'Published';
    }
    setStartups([newStartup, ...startups]);
    setView('dashboard');
    setGenerationState('idle');
    setGeneratedData({});
    setTxHash('');
    setMintSuccess(false);
    setUrlInput('');
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      {view === 'dashboard' ? (
        <div className="space-y-8 animate-in fade-in duration-500">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2 text-white">Studio</h1>
              <p className="text-zinc-400 text-lg">Manage your startups, tweak AI pitches, and launch to the community.</p>
            </div>
            <button 
              onClick={() => setView('create')}
              className="bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold px-8 py-4 rounded-xl transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)]"
            >
              <Wand2 className="w-5 h-5" />
              Create New Startup
            </button>
          </div>

          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {startups.map(startup => (
              <div key={startup.id} className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-bold text-xl text-emerald-400">
                    {startup.logo}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{startup.name}</h3>
                    <span className="px-2 py-0.5 bg-zinc-800 text-zinc-300 text-xs font-medium rounded-md mt-1 inline-block">
                      {startup.status}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-zinc-400 line-clamp-2">{startup.hook}</p>
                <div className="mt-auto pt-4 flex gap-2">
                  <button className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                    Edit
                  </button>
                  <button className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 py-2 rounded-lg text-sm font-medium transition-colors border border-emerald-500/20">
                    View Stats
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="max-w-5xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 duration-500">
          <button 
            onClick={() => setView('dashboard')}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </button>

          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Create New Startup</h1>
            <p className="text-zinc-400">Provide a source and let our AI agents generate your pitch, audio, and video.</p>
          </div>

          {generationState === 'idle' && (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-4">
                <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4">
                  <LinkIcon className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-white">Paste Website URL</h3>
                <p className="text-sm text-zinc-400">We'll scrape the landing page and docs to understand the core value prop.</p>
                <input 
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://your-startup.com"
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                />
                <button 
                  onClick={handleGenerate}
                  disabled={!urlInput}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-500 text-zinc-950 font-bold py-3 rounded-xl transition-colors"
                >
                  Generate
                </button>
              </div>

              <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-2xl p-6 space-y-4 relative overflow-hidden group">
                <div className="absolute top-4 right-4 px-3 py-1 bg-zinc-800 text-zinc-400 text-xs font-bold rounded-full uppercase tracking-wider">
                  Coming Soon
                </div>
                <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-4 opacity-50">
                  <FileText className="w-6 h-6 text-zinc-400" />
                </div>
                <h3 className="text-xl font-semibold text-zinc-300">Upload Document</h3>
                <p className="text-sm text-zinc-500">Upload a pitch deck or whitepaper (PDF) for deep analysis.</p>
                <div className="w-full border-2 border-dashed border-zinc-800 rounded-xl p-8 flex flex-col items-center justify-center text-zinc-600">
                  <FileText className="w-8 h-8 mb-2 opacity-50" />
                  <span className="text-sm font-medium">Drag & drop PDF</span>
                </div>
              </div>
            </div>
          )}

          {generationState !== 'idle' && (
            <div className="space-y-8">
              {/* Progressive Loading Indicators */}
              <div className="grid md:grid-cols-3 gap-4">
                <div className={`p-4 rounded-xl border flex items-center gap-3 transition-colors ${loadingZones.text ? 'bg-zinc-900 border-zinc-800' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                  {loadingZones.text ? <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                  <div>
                    <p className="text-sm font-medium text-white">AI Summaries</p>
                    <p className="text-xs text-zinc-400">{loadingZones.text ? 'Scraping URL & Summarizing...' : 'Content Generated'}</p>
                  </div>
                </div>
                <div className={`p-4 rounded-xl border flex items-center gap-3 transition-colors ${loadingZones.audio ? 'bg-zinc-900 border-zinc-800' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                  {loadingZones.audio ? <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                  <div>
                    <p className="text-sm font-medium text-white">Audio Pitch</p>
                    <p className="text-xs text-zinc-400">{loadingZones.audio ? 'Cloning Voice & Generating...' : 'Audio Ready'}</p>
                  </div>
                </div>
                <div className={`p-4 rounded-xl border flex items-center gap-3 transition-colors ${loadingZones.video ? 'bg-zinc-900 border-zinc-800' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                  {loadingZones.video ? <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                  <div>
                    <p className="text-sm font-medium text-white">Cinematic Video</p>
                    <p className="text-xs text-zinc-400">{loadingZones.video ? 'Rendering B-Roll...' : 'Video Rendered'}</p>
                  </div>
                </div>
              </div>

              {/* Preview Card */}
              <div className="relative">
                <div className="absolute -inset-4 bg-emerald-500/5 rounded-3xl blur-xl -z-10" />
                <StartupCard startup={generatedData as StartupData} />
              </div>

              {/* Actions */}
              {generationState === 'done' && (
                <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-zinc-800">
                  <button 
                    onClick={() => setShowTokenModal(true)}
                    className="flex-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-colors"
                  >
                    <Coins className="w-5 h-5 text-yellow-400" />
                    Generate Token for Startup
                  </button>
                  <button 
                    onClick={handlePublish}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 py-4 rounded-xl font-bold transition-colors shadow-[0_0_20px_rgba(16,185,129,0.2)]"
                  >
                    Publish to Discover
                  </button>
                </div>
              )}

              {/* Token Modal */}
              {showTokenModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                    <h3 className="text-2xl font-bold text-white mb-2">Mint SPL Token</h3>
                    <p className="text-zinc-400 text-sm mb-6">Create a tradable token for your startup on Solana.</p>
                    
                    <div className="space-y-4 mb-8">
                      <div>
                        <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Phantom Address</label>
                        <input 
                          type="text" 
                          value={phantomAddress}
                          readOnly
                          className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-400 font-mono text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Token Symbol (Max 5 chars)</label>
                        <input 
                          type="text" 
                          value={tokenSymbol}
                          onChange={(e) => setTokenSymbol(e.target.value.toUpperCase().slice(0, 5))}
                          placeholder="$TICKER"
                          className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white font-mono placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                        />
                      </div>
                    </div>

                    {mintSuccess ? (
                      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex flex-col items-center justify-center gap-2">
                        <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                        <p className="text-emerald-400 font-medium">Token Minted Successfully!</p>
                        <a href="#" className="text-xs text-emerald-500 hover:text-emerald-300 flex items-center gap-1 mt-1">
                          View Transaction <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    ) : (
                      <div className="flex gap-3">
                        <button 
                          onClick={() => setShowTokenModal(false)}
                          className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl font-medium transition-colors"
                        >
                          Cancel
                        </button>
                        <button 
                          onClick={handleMint}
                          disabled={isMinting || !tokenSymbol}
                          className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-zinc-950 rounded-xl font-bold transition-colors flex items-center justify-center gap-2"
                        >
                          {isMinting ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> Minting...</>
                          ) : (
                            'Generate Token'
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
