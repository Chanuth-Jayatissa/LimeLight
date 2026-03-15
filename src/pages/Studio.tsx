import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Link as LinkIcon, FileText, Loader2, CheckCircle2, Wand2, Coins, ExternalLink, Mic, Square } from 'lucide-react';
import { fetchAuthSession } from 'aws-amplify/auth';
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
    tokenPrice: 0.0015,
    marketCap: 150000,
    tokenAddress: 'Token11111111111111111111111111111111111111',
    tokenSymbol: 'AWAI',
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
  const [startups, setStartups] = useState<StartupData[]>(() => {
    const saved = localStorage.getItem('userStartups');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse user startups', e);
      }
    }
    return mockUserStartups;
  });
  
  // Create State
  const [urlInput, setUrlInput] = useState('');
  const [createStep, setCreateStep] = useState<'idle' | 'voice' | 'generating' | 'done'>('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [loadingZones, setLoadingZones] = useState({ text: true, audio: true, video: true });
  const [voiceStatus, setVoiceStatus] = useState<string>('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  const [generatedData, setGeneratedData] = useState<Partial<StartupData>>({});
  
  // Token Modal State
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [phantomAddress, setPhantomAddress] = useState('HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH');
  const [tokenSymbol, setTokenSymbol] = useState('');
  const [isMinting, setIsMinting] = useState(false);
  const [mintSuccess, setMintSuccess] = useState(false);
  const [txHash, setTxHash] = useState('');

  useEffect(() => {
    if (createStep === 'generating' && !loadingZones.text && !loadingZones.audio && !loadingZones.video) {
      setCreateStep('done');
    }
  }, [createStep, loadingZones]);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  const processVoicePipeline = async (file: File, targetUrl: string) => {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString() || session.tokens?.accessToken?.toString();

      setVoiceStatus('Cloning voice from audio...');
      const base64Audio = await fileToBase64(file);
      
      // 1. Create Voice
      const voiceRes = await fetch('/api/createVoice', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ audio_base64: base64Audio, name: 'Founder' })
      });
      
      if (!voiceRes.ok) {
        const errorText = await voiceRes.text();
        console.error('Voice creation API error:', voiceRes.status, errorText);
        throw new Error(`API error ${voiceRes.status}: ${errorText}`);
      }
      
      let voiceData = await voiceRes.json();
      console.log('Voice creation response:', voiceData);
      
      // Handle API Gateway proxy response format if necessary
      if (voiceData.body && typeof voiceData.body === 'string') {
        try {
          voiceData = JSON.parse(voiceData.body);
        } catch (e) {
          console.error('Failed to parse voiceData.body', e);
        }
      }
      
      if (voiceData.statusCode && voiceData.statusCode !== 200) {
        throw new Error(`Lambda error ${voiceData.statusCode}: ${JSON.stringify(voiceData)}`);
      }
      
      const voiceId = voiceData.voice_id;

      if (!voiceId) {
        console.error('Voice creation failed. Response:', voiceData);
        throw new Error('Failed to create voice');
      }

      setVoiceStatus('Writing pitch...');
      // 2. Get Pitch
      const pitchRes = await fetch('/api/getPitchFromBedrock', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url: targetUrl })
      });
      
      if (!pitchRes.ok) {
        const errorText = await pitchRes.text();
        console.error('Pitch generation API error:', pitchRes.status, errorText);
        throw new Error(`Pitch API error ${pitchRes.status}: ${errorText}`);
      }
      
      let pitchData = await pitchRes.json();
      
      if (pitchData.body && typeof pitchData.body === 'string') {
        try {
          pitchData = JSON.parse(pitchData.body);
        } catch (e) {
          console.error('Failed to parse pitchData.body', e);
        }
      }
      
      const pitchText = pitchData.text || pitchData.pitch;

      setVoiceStatus('Synthesizing audio...');
      // 3. Generate TTS
      const ttsRes = await fetch('/tts/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text: pitchText, voice_id: voiceId, name: 'Founder' })
      });
      
      if (!ttsRes.ok) {
        const errorText = await ttsRes.text();
        console.error('TTS generation API error:', ttsRes.status, errorText);
        throw new Error(`TTS API error ${ttsRes.status}: ${errorText}`);
      }
      
      let ttsData = await ttsRes.json();
      
      if (ttsData.body && typeof ttsData.body === 'string') {
        try {
          ttsData = JSON.parse(ttsData.body);
        } catch (e) {
          console.error('Failed to parse ttsData.body', e);
        }
      }
      
      const audioUrl = ttsData.s3_url || ttsData.audio_url;

      setVoiceStatus('Cleaning up...');
      // 4. Delete Voice
      await fetch('/api/deleteVoice', {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ voice_id: voiceId })
      });

      setVoiceStatus('');
      return audioUrl;
    } catch (error: any) {
      console.error('Voice pipeline error:', error);
      
      let errorMessage = 'Failed to generate voice pitch.';
      if (error.message === 'Failed to fetch') {
        errorMessage = 'Network error (Failed to fetch). This usually means CORS is not enabled on your AWS API Gateway for the voice endpoints, or the API URL is missing a stage name (like /prod).';
      } else {
        errorMessage = error.message || errorMessage;
      }
      
      setVoiceStatus(errorMessage);
      return null;
    }
  };

  const handleInitialize = async () => {
    if (!urlInput) return;
    setCreateStep('voice');
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

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString() || session.tokens?.accessToken?.toString();

      const response = await fetch('/api/scrapeURL', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url: urlInput })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Scrape URL API error:', response.status, errorText);
        throw new Error(`API error ${response.status}: ${errorText}`);
      }

      const responseText = await response.text();
      let data: any = {};
      
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch (e) {
        console.warn('Response was not valid JSON, using raw text');
        data = { summary: responseText };
      }
      
      setLoadingZones(prev => ({ ...prev, text: false }));
      setGeneratedData(prev => ({
        ...prev,
        ...data,
        name: data.context_file?.project_name || data.name || 'Unknown Startup',
        logo: (data.context_file?.project_name || data.name || 'S').charAt(0),
        hook: data.one_sentence_summary || data.hook || data.summary || 'No hook generated.',
        problem: data.problem || 'Problem not specified.',
        solution: data.solution || 'Solution not specified.',
        radarData: data.projected_growth ? [
          { subject: 'Team', score: (data.projected_growth.team || 0) * 20 },
          { subject: 'Tech', score: (data.projected_growth.tech || 0) * 20 },
          { subject: 'Market', score: (data.projected_growth.market || 0) * 20 },
          { subject: 'Traction', score: (data.projected_growth.traction || 0) * 20 },
        ] : prev.radarData,
        lineData: data.user_growth_projection_12_months ? [
          { month: 'M1', users: data.user_growth_projection_12_months.month_1 || 0 },
          { month: 'M2', users: data.user_growth_projection_12_months.month_2 || 0 },
          { month: 'M3', users: data.user_growth_projection_12_months.month_3 || 0 },
          { month: 'M4', users: data.user_growth_projection_12_months.month_4 || 0 },
          { month: 'M5', users: data.user_growth_projection_12_months.month_5 || 0 },
          { month: 'M6', users: data.user_growth_projection_12_months.month_6 || 0 },
          { month: 'M7', users: data.user_growth_projection_12_months.month_7 || 0 },
          { month: 'M8', users: data.user_growth_projection_12_months.month_8 || 0 },
          { month: 'M9', users: data.user_growth_projection_12_months.month_9 || 0 },
          { month: 'M10', users: data.user_growth_projection_12_months.month_10 || 0 },
          { month: 'M11', users: data.user_growth_projection_12_months.month_11 || 0 },
          { month: 'M12', users: data.user_growth_projection_12_months.month_12 || 0 },
        ] : prev.lineData
      }));
    } catch (error: any) {
      console.error('Error fetching startup summary:', error);
      
      let errorMessage = 'Failed to generate summary from the provided URL.';
      if (error.message === 'Failed to fetch') {
        errorMessage = 'Network error (Failed to fetch). This usually means CORS is not enabled on your AWS API Gateway, or the API URL is missing a stage name (like /prod).';
      } else {
        errorMessage = error.message || errorMessage;
      }

      setLoadingZones(prev => ({ ...prev, text: false }));
      setGeneratedData(prev => ({
        ...prev,
        name: 'Connection Error',
        hook: errorMessage,
      }));
    }

    // Zone 3: Video (Starts immediately in background, takes ~6s)
    setTimeout(() => {
      setLoadingZones(prev => ({ ...prev, video: false }));
      setGeneratedData(prev => ({
        ...prev,
        videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
      }));
    }, 6000);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const file = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
        setAudioFile(file);
        // We must call handleGenerate here because state updates are async
        handleGenerate(file);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please ensure permissions are granted.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleGenerate = async (recordedFile?: File) => {
    setCreateStep('generating');
    
    const fileToProcess = recordedFile || audioFile;
    
    if (!fileToProcess) {
      // Fallback if no audio recorded
      setTimeout(() => {
        setLoadingZones(prev => ({ ...prev, audio: false }));
        setGeneratedData(prev => ({
          ...prev,
          audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
        }));
      }, 4000);
    } else {
      // Process the actual voice pipeline
      const generatedAudioUrl = await processVoicePipeline(fileToProcess, urlInput);
      
      setLoadingZones(prev => ({ ...prev, audio: false }));
      if (generatedAudioUrl) {
        setGeneratedData(prev => ({
          ...prev,
          audioUrl: generatedAudioUrl,
        }));
      } else {
        // Fallback on error
        setGeneratedData(prev => ({
          ...prev,
          audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
        }));
      }
    }
  };

  const handleMint = async () => {
    if (!tokenSymbol || tokenSymbol.length > 5) return;
    setIsMinting(true);
    
    // Simulate Solana smart contract interaction
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    setIsMinting(false);
    setMintSuccess(true);
    setTxHash('5xY9...aB2c');
    
    setGeneratedData(prev => ({
      ...prev,
      tokenAddress: 'Token11111111111111111111111111111111111111',
      tokenSymbol: tokenSymbol
    }));
    
    setTimeout(() => {
      setShowTokenModal(false);
    }, 2000);
  };

  const handlePublish = () => {
    const newStartup = { 
      ...generatedData,
      id: `startup-${Date.now()}`
    } as StartupData;
    if (txHash) {
      newStartup.status = 'Live Token';
    } else {
      newStartup.status = 'Published';
    }
    const updatedStartups = [newStartup, ...startups];
    setStartups(updatedStartups);
    localStorage.setItem('userStartups', JSON.stringify(updatedStartups));
    setView('dashboard');
    setCreateStep('idle');
    setGeneratedData({});
    setTxHash('');
    setMintSuccess(false);
    setUrlInput('');
    setLoadingZones({ text: true, audio: true, video: true });
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

          {createStep === 'idle' && (
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
                  onClick={handleInitialize}
                  disabled={!urlInput}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-500 text-zinc-950 font-bold py-3 rounded-xl transition-colors"
                >
                  Initialize Startup
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

          {createStep === 'voice' && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 space-y-8 animate-in slide-in-from-right-8 duration-500">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold text-white">Voice Studio</h3>
                <p className="text-zinc-400">Read the manifesto below to clone your voice for the pitch.</p>
              </div>

              <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-8 relative">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-zinc-800 text-zinc-300 text-xs font-bold px-4 py-1 rounded-full uppercase tracking-widest">
                  Teleprompter
                </div>
                <p className="text-xl leading-relaxed text-zinc-300 font-medium text-center">
                  "We believe in a future where technology empowers everyone. Our mission is to build tools that are not only powerful but accessible. We are creating a platform that bridges the gap between complex infrastructure and intuitive design. By leveraging the latest advancements in artificial intelligence, we are automating the mundane and unlocking human creativity. Our vision is a world where anyone can turn their ideas into reality without being hindered by technical barriers. We are committed to open standards, community-driven development, and relentless innovation. Join us on this journey to reshape the digital landscape. Together, we can build a more connected, efficient, and inspiring future for all."
                </p>
              </div>

              <div className="flex justify-center">
                <button
                  onClick={toggleRecording}
                  className={`relative group flex items-center justify-center w-24 h-24 rounded-full transition-all duration-300 ${
                    isRecording 
                      ? 'bg-rose-500/20 hover:bg-rose-500/30 border-2 border-rose-500' 
                      : 'bg-emerald-500 hover:bg-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)]'
                  }`}
                >
                  {isRecording && (
                    <div className="absolute inset-0 rounded-full border-4 border-rose-500 animate-ping opacity-20" />
                  )}
                  {isRecording ? (
                    <Square className="w-8 h-8 text-rose-500 fill-rose-500" />
                  ) : (
                    <Mic className="w-10 h-10 text-zinc-950" />
                  )}
                </button>
              </div>
              <div className="text-center">
                <p className={`text-sm font-medium ${isRecording ? 'text-rose-400 animate-pulse' : 'text-zinc-500'}`}>
                  {isRecording ? 'Recording... Click to stop' : 'Click to start recording'}
                </p>
              </div>
            </div>
          )}

          {(createStep === 'generating' || createStep === 'done') && (
            <div className="space-y-8 animate-in fade-in duration-500">
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
                    <p className="text-xs text-zinc-400">{loadingZones.audio ? (voiceStatus || 'Cloning Voice & Generating...') : 'Audio Ready'}</p>
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
              {createStep === 'done' && (
                <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-zinc-800">
                  {!generatedData.tokenAddress && (
                    <button 
                      onClick={() => setShowTokenModal(true)}
                      className="flex-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-colors"
                    >
                      <Coins className="w-5 h-5 text-yellow-400" />
                      Generate Token for Startup
                    </button>
                  )}
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
