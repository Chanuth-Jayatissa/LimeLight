import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, LayoutDashboard, TrendingUp, Shield, Globe } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-emerald-500/30">
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-zinc-950" />
          </div>
          <span className="font-semibold text-xl tracking-tight">LimeLight</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">Log in</Link>
          <Link to="/signup" className="text-sm font-medium bg-white text-zinc-950 px-4 py-2 rounded-full hover:bg-zinc-200 transition-colors">Sign up</Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pt-24 pb-32 text-center">
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-7xl font-bold tracking-tight mb-8 max-w-4xl mx-auto leading-tight"
        >
          The premier platform for <span className="text-emerald-500">startup investing</span>
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto"
        >
          Discover, fund, and manage your portfolio of high-growth startups all in one place. Join thousands of investors building the future.
        </motion.p>
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center justify-center gap-4"
        >
          <Link to="/signup" className="flex items-center gap-2 bg-emerald-500 text-zinc-950 px-8 py-4 rounded-full font-semibold text-lg hover:bg-emerald-400 transition-colors">
            Get Started <ArrowRight className="w-5 h-5" />
          </Link>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8 text-left"
        >
          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
            <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-6">
              <TrendingUp className="w-6 h-6 text-emerald-500" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Track Portfolio</h3>
            <p className="text-zinc-400">Monitor your investments in real-time with advanced analytics and performance metrics.</p>
          </div>
          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
            <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-6">
              <Globe className="w-6 h-6 text-emerald-500" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Discover Startups</h3>
            <p className="text-zinc-400">Access a curated feed of high-potential startups and connect directly with founders.</p>
          </div>
          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
            <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-6">
              <Shield className="w-6 h-6 text-emerald-500" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Secure Investing</h3>
            <p className="text-zinc-400">Bank-grade security and seamless wallet integration for safe and easy transactions.</p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
