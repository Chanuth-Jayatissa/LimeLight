import { BrowserRouter, Routes, Route, Link, Outlet, Navigate, useLocation } from 'react-router-dom';
import Portfolio from './pages/Portfolio';
import Profile from './pages/Profile';
import Feed from './pages/Feed';
import Landing from './pages/Landing';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import { Wallet, Users, LayoutDashboard, LogOut } from 'lucide-react';

function Navigation() {
  const location = useLocation();
  
  const isActive = (path: string) => {
    if (path === '/app' && location.pathname === '/app') return true;
    if (path !== '/app' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-1 p-1.5 rounded-full bg-zinc-900/60 backdrop-blur-xl border border-white/10 shadow-2xl">
      <Link 
        to="/app" 
        className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${
          isActive('/app') 
            ? 'bg-white/10 text-white shadow-sm' 
            : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
        }`}
      >
        <LayoutDashboard className="w-4 h-4" />
        <span className="text-sm font-medium">Feed</span>
      </Link>
      
      <Link 
        to="/app/portfolio" 
        className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${
          isActive('/app/portfolio') 
            ? 'bg-white/10 text-white shadow-sm' 
            : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
        }`}
      >
        <Wallet className="w-4 h-4" />
        <span className="text-sm font-medium">Portfolio</span>
      </Link>
      
      <Link 
        to="/app/profile/1" 
        className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${
          isActive('/app/profile') 
            ? 'bg-white/10 text-white shadow-sm' 
            : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
        }`}
      >
        <Users className="w-4 h-4" />
        <span className="text-sm font-medium">Profile</span>
      </Link>

      <div className="w-px h-6 bg-white/10 mx-2" />

      <Link 
        to="/" 
        className="flex items-center gap-2 px-4 py-2 rounded-full text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-300"
      >
        <LogOut className="w-4 h-4" />
        <span className="text-sm font-medium">Exit</span>
      </Link>
    </nav>
  );
}

function Layout() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex flex-col relative">
      <Navigation />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pt-28 pb-12">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/app" element={<Layout />}>
          <Route index element={<Feed />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="profile/:id" element={<Profile />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
