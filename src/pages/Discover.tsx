import React, { useState, useEffect } from 'react';
import StartupCard, { StartupData } from '../components/StartupCard';

const mockStartups: StartupData[] = [
  {
    id: '1',
    name: 'Nexus Protocol',
    logo: 'N',
    tag: 'DePIN',
    status: 'Live Curve',
    hook: 'Decentralizing AI compute through consumer GPUs.',
    problem: 'AI training is monopolized by big tech, making compute prohibitively expensive for startups and researchers.',
    solution: 'A decentralized network allowing anyone to monetize their idle GPU power for AI training tasks, reducing costs by 80%.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    websiteUrl: 'https://example.com/nexus',
    tokenPrice: 0.0042,
    marketCap: 1250000,
    radarData: [
      { subject: 'Team', score: 85 },
      { subject: 'Tech', score: 95 },
      { subject: 'Market', score: 70 },
      { subject: 'Traction', score: 60 },
    ],
    lineData: [
      { month: 'Jan', users: 1000 },
      { month: 'Feb', users: 2500 },
      { month: 'Mar', users: 5000 },
      { month: 'Apr', users: 12000 },
      { month: 'May', users: 25000 },
      { month: 'Jun', users: 45000 },
      { month: 'Jul', users: 80000 },
      { month: 'Aug', users: 120000 },
      { month: 'Sep', users: 180000 },
      { month: 'Oct', users: 250000 },
      { month: 'Nov', users: 350000 },
      { month: 'Dec', users: 500000 },
    ]
  },
  {
    id: '2',
    name: 'Aura Finance',
    logo: 'A',
    tag: 'DeFi',
    status: 'Live Curve',
    hook: 'The first zero-knowledge lending protocol on Solana.',
    problem: 'Current lending protocols expose user positions and borrowing history, compromising financial privacy on-chain.',
    solution: 'Aura uses zk-SNARKs to allow users to prove collateralization without revealing their total assets or transaction history.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
    websiteUrl: 'https://example.com/aura',
    tokenPrice: 0.0185,
    marketCap: 4500000,
    radarData: [
      { subject: 'Team', score: 90 },
      { subject: 'Tech', score: 88 },
      { subject: 'Market', score: 95 },
      { subject: 'Traction', score: 80 },
    ],
    lineData: [
      { month: 'Jan', users: 500 },
      { month: 'Feb', users: 1200 },
      { month: 'Mar', users: 3000 },
      { month: 'Apr', users: 8000 },
      { month: 'May', users: 15000 },
      { month: 'Jun', users: 28000 },
      { month: 'Jul', users: 45000 },
      { month: 'Aug', users: 70000 },
      { month: 'Sep', users: 100000 },
      { month: 'Oct', users: 150000 },
      { month: 'Nov', users: 220000 },
      { month: 'Dec', users: 300000 },
    ]
  },
  {
    id: '3',
    name: 'Voxel Space',
    logo: 'V',
    tag: 'Gaming',
    status: 'Live Curve',
    hook: 'Fully on-chain physics engine for metaverse scaling.',
    problem: 'Web3 games struggle with server-authoritative physics, leading to lag and centralized points of failure.',
    solution: 'A highly optimized Solana program that calculates rigid-body physics natively on-chain, enabling trustless multiplayer.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
    websiteUrl: 'https://example.com/voxel',
    tokenPrice: 0.0021,
    marketCap: 850000,
    radarData: [
      { subject: 'Team', score: 75 },
      { subject: 'Tech', score: 98 },
      { subject: 'Market', score: 85 },
      { subject: 'Traction', score: 40 },
    ],
    lineData: [
      { month: 'Jan', users: 200 },
      { month: 'Feb', users: 400 },
      { month: 'Mar', users: 900 },
      { month: 'Apr', users: 2000 },
      { month: 'May', users: 4500 },
      { month: 'Jun', users: 8000 },
      { month: 'Jul', users: 15000 },
      { month: 'Aug', users: 25000 },
      { month: 'Sep', users: 40000 },
      { month: 'Oct', users: 60000 },
      { month: 'Nov', users: 90000 },
      { month: 'Dec', users: 140000 },
    ]
  },
  {
    id: '4',
    name: 'Synthetix AI',
    logo: 'S',
    tag: 'AI Agents',
    status: 'Live Curve',
    hook: 'Autonomous trading agents powered by LLM sentiment analysis.',
    problem: 'Retail traders lack the tools to analyze millions of social media posts and news articles in real-time.',
    solution: 'Deploy custom AI agents that execute trades automatically based on real-time sentiment shifts across Twitter and Discord.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
    websiteUrl: 'https://example.com/synthetix',
    tokenPrice: 0.0540,
    marketCap: 12400000,
    radarData: [
      { subject: 'Team', score: 95 },
      { subject: 'Tech', score: 90 },
      { subject: 'Market', score: 80 },
      { subject: 'Traction', score: 95 },
    ],
    lineData: [
      { month: 'Jan', users: 5000 },
      { month: 'Feb', users: 15000 },
      { month: 'Mar', users: 35000 },
      { month: 'Apr', users: 60000 },
      { month: 'May', users: 100000 },
      { month: 'Jun', users: 180000 },
      { month: 'Jul', users: 250000 },
      { month: 'Aug', users: 380000 },
      { month: 'Sep', users: 500000 },
      { month: 'Oct', users: 700000 },
      { month: 'Nov', users: 950000 },
      { month: 'Dec', users: 1200000 },
    ]
  },
  {
    id: '5',
    name: 'OmniChain',
    logo: 'O',
    tag: 'Infrastructure',
    status: 'Live Curve',
    hook: 'Zero-latency cross-chain messaging protocol.',
    problem: 'Bridging assets and data between blockchains is slow, expensive, and highly vulnerable to hacks.',
    solution: 'A novel consensus mechanism that verifies cross-chain state instantly, eliminating the need for traditional bridges.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',
    websiteUrl: 'https://example.com/omnichain',
    tokenPrice: 0.0110,
    marketCap: 3200000,
    radarData: [
      { subject: 'Team', score: 88 },
      { subject: 'Tech', score: 92 },
      { subject: 'Market', score: 90 },
      { subject: 'Traction', score: 65 },
    ],
    lineData: [
      { month: 'Jan', users: 800 },
      { month: 'Feb', users: 1500 },
      { month: 'Mar', users: 3200 },
      { month: 'Apr', users: 7000 },
      { month: 'May', users: 12000 },
      { month: 'Jun', users: 22000 },
      { month: 'Jul', users: 35000 },
      { month: 'Aug', users: 55000 },
      { month: 'Sep', users: 80000 },
      { month: 'Oct', users: 120000 },
      { month: 'Nov', users: 180000 },
      { month: 'Dec', users: 250000 },
    ]
  },
  {
    id: '6',
    name: 'BioSync',
    logo: 'B',
    tag: 'DeSci',
    status: 'Live Curve',
    hook: 'Tokenizing genomic data for decentralized medical research.',
    problem: 'Individuals have no control or ownership over their genomic data, which is sold by corporations for billions.',
    solution: 'A secure, encrypted vault where users store their DNA data and earn tokens when researchers access it for studies.',
    videoUrl: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
    websiteUrl: 'https://example.com/biosync',
    tokenPrice: 0.0085,
    marketCap: 2100000,
    radarData: [
      { subject: 'Team', score: 92 },
      { subject: 'Tech', score: 85 },
      { subject: 'Market', score: 75 },
      { subject: 'Traction', score: 50 },
    ],
    lineData: [
      { month: 'Jan', users: 300 },
      { month: 'Feb', users: 800 },
      { month: 'Mar', users: 1500 },
      { month: 'Apr', users: 3000 },
      { month: 'May', users: 6000 },
      { month: 'Jun', users: 10000 },
      { month: 'Jul', users: 18000 },
      { month: 'Aug', users: 28000 },
      { month: 'Sep', users: 45000 },
      { month: 'Oct', users: 70000 },
      { month: 'Nov', users: 100000 },
      { month: 'Dec', users: 150000 },
    ]
  }
];

export default function Discover() {
  const [columns, setColumns] = useState(3);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1280) {
        setColumns(3);
      } else if (window.innerWidth >= 1024) {
        setColumns(2);
      } else {
        setColumns(1);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Distribute startups into columns to create a true masonry layout
  const colArrays: StartupData[][] = Array.from({ length: columns }, () => []);
  mockStartups.forEach((startup, index) => {
    colArrays[index % columns].push(startup);
  });

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      <div className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight mb-3 text-white">Discover the Community</h1>
        <p className="text-zinc-400 text-lg">Your front-row seat to the latest innovations. Browse cinematic pitches from passionate builders, connect with verified founders, and back the visions you believe in.</p>
      </div>
      
      <div className={`grid gap-8 ${columns === 3 ? 'grid-cols-3' : columns === 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {colArrays.map((col, colIndex) => (
          <div key={colIndex} className="flex flex-col gap-8">
            {col.map((startup) => (
              <StartupCard key={startup.id} startup={startup} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
