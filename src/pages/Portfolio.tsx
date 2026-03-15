import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Wallet, TrendingUp, ArrowRight, Activity, LogOut } from 'lucide-react';

interface Investment {
  id: string;
  assetName: string;
  balance: number;
  currentValue: number;
  change: number;
}

const mockInvestments: Investment[] = [
  { id: '1', assetName: 'Acme Corp Equity', balance: 1500, currentValue: 45000, change: 12.5 },
  { id: '2', assetName: 'Nexus AI Tokens', balance: 50000, currentValue: 12500, change: -4.2 },
  { id: '3', assetName: 'Starlight Ventures', balance: 250, currentValue: 85000, change: 24.8 },
];

export default function Portfolio() {
  const [investments, setInvestments] = useState<Investment[]>(mockInvestments);
  const [isConnected, setIsConnected] = useState(true);

  const netWorth = investments.reduce((sum, inv) => sum + inv.currentValue, 0);

  const handleDisconnect = () => {
    setIsConnected(false);
    setInvestments([]);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-8 max-w-5xl mx-auto"
    >
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Portfolio</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Net Worth Card */}
        <div className="col-span-1 md:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6 opacity-10">
            <TrendingUp className="w-32 h-32" />
          </div>
          <p className="text-zinc-400 text-sm font-medium mb-2">Total Net Worth</p>
          <h2 className="text-5xl font-semibold tracking-tight mb-4">
            ${netWorth.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </h2>
          <div className="flex items-center gap-2 text-emerald-500 text-sm font-medium bg-emerald-500/10 w-fit px-3 py-1 rounded-full">
            <Activity className="w-4 h-4" />
            <span>+14.2% all time</span>
          </div>
        </div>

        {/* Wallet Status Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-zinc-400 text-sm font-medium">Wallet Status</p>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            </div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-zinc-800 rounded-full flex items-center justify-center">
                <Wallet className="w-5 h-5 text-zinc-300" />
              </div>
              <div>
                <p className="font-medium">{isConnected ? 'Connected' : 'Disconnected'}</p>
                <p className="text-xs text-zinc-500 font-mono">{isConnected ? '0x71C...976F' : 'No wallet linked'}</p>
              </div>
            </div>
          </div>
          
          <button 
            onClick={handleDisconnect}
            disabled={!isConnected}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border border-zinc-800 text-sm font-medium text-zinc-300 hover:bg-zinc-800 hover:text-zinc-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <LogOut className="w-4 h-4" />
            Disconnect Wallet
          </button>
        </div>
      </div>

      {/* Assets Section */}
      <h3 className="text-xl font-medium mb-6">Your Assets</h3>

      {investments.length > 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 text-sm text-zinc-400">
                <th className="px-6 py-4 font-medium">Asset Name</th>
                <th className="px-6 py-4 font-medium text-right">Balance</th>
                <th className="px-6 py-4 font-medium text-right">Current Value</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {investments.map((inv) => (
                <tr key={inv.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold">
                        {inv.assetName.charAt(0)}
                      </div>
                      <span className="font-medium">{inv.assetName}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right font-mono text-sm text-zinc-300">
                    {inv.balance.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-medium">
                        ${inv.currentValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                      <span className={`text-xs ${inv.change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                        {inv.change >= 0 ? '+' : ''}{inv.change}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="px-4 py-1.5 bg-zinc-100 text-zinc-900 text-sm font-medium rounded-md hover:bg-white transition-colors">
                      Trade
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-zinc-900/50 border border-dashed border-zinc-700 rounded-2xl p-12 flex flex-col items-center justify-center text-center"
        >
          <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mb-6">
            <Wallet className="w-8 h-8 text-zinc-400" />
          </div>
          <h3 className="text-xl font-medium mb-2">No assets found</h3>
          <p className="text-zinc-400 max-w-md mb-8">
            Your portfolio is currently empty. Start investing in promising startups to build your wealth.
          </p>
          <Link 
            to="/app" 
            className="flex items-center gap-2 px-6 py-3 bg-emerald-500 text-zinc-950 font-medium rounded-lg hover:bg-emerald-400 transition-colors"
          >
            Explore Startups
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      )}
    </motion.div>
  );
}
