import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { MessageSquare, MapPin, Link as LinkIcon, Twitter, Github, X, Send } from 'lucide-react';

// Mock data for the profile
const mockProfile = {
  id: '1',
  displayName: 'Alex Rivera',
  username: '@arivera',
  bio: 'Building the next generation of decentralized finance tools. Previously founded Nexus AI (acquired). Passionate about open source and community building.',
  location: 'San Francisco, CA',
  website: 'alexrivera.dev',
  skills: ['React', 'Solidity', 'System Design', 'Go', 'Product Strategy'],
  avatarUrl: 'https://picsum.photos/seed/alex/200/200',
  coverUrl: 'https://picsum.photos/seed/abstract/1200/400',
};

export default function Profile() {
  const { id } = useParams();
  const [isMessageModalOpen, setIsMessageModalOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  // In a real app, we'd fetch the profile based on the ID.
  const profile = mockProfile;

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    
    setIsSending(true);
    // Simulate API call
    setTimeout(() => {
      setIsSending(false);
      setIsMessageModalOpen(false);
      setMessage('');
      // Show success toast in a real app
    }, 1000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-zinc-950 pb-20"
    >
      {/* Cover Image */}
      <div className="h-64 w-full relative">
        <img 
          src={profile.coverUrl} 
          alt="Cover" 
          className="w-full h-full object-cover opacity-60"
          referrerPolicy="no-referrer"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 to-transparent" />
      </div>

      <div className="max-w-4xl mx-auto px-8 relative -mt-24">
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-end justify-between mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-end">
            <div className="w-32 h-32 rounded-2xl border-4 border-zinc-950 overflow-hidden bg-zinc-800 relative z-10">
              <img 
                src={profile.avatarUrl} 
                alt={profile.displayName} 
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
            </div>
            <div className="pb-2">
              <h1 className="text-3xl font-bold tracking-tight text-white mb-1">{profile.displayName}</h1>
              <p className="text-zinc-400 font-medium">{profile.username}</p>
            </div>
          </div>
          
          <div className="flex gap-3 pb-2 w-full md:w-auto">
            <button 
              onClick={() => setIsMessageModalOpen(true)}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 bg-zinc-50 text-zinc-950 font-medium rounded-lg hover:bg-zinc-200 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Message Founder
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {/* Main Info */}
          <div className="col-span-1 md:col-span-2 space-y-8">
            <section>
              <h2 className="text-xl font-semibold mb-4 text-zinc-100">About</h2>
              <p className="text-zinc-300 leading-relaxed text-lg">
                {profile.bio}
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4 text-zinc-100">Skills & Expertise</h2>
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill) => (
                  <span 
                    key={skill} 
                    className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-full text-sm font-medium text-zinc-300 hover:border-zinc-700 hover:text-zinc-100 transition-colors cursor-default"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          </div>

          {/* Sidebar Info */}
          <div className="col-span-1 space-y-6">
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-3 text-zinc-400">
                <MapPin className="w-5 h-5" />
                <span className="text-sm font-medium">{profile.location}</span>
              </div>
              <div className="flex items-center gap-3 text-zinc-400">
                <LinkIcon className="w-5 h-5" />
                <a href={`https://${profile.website}`} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:text-emerald-500 transition-colors">
                  {profile.website}
                </a>
              </div>
              <div className="flex items-center gap-3 text-zinc-400">
                <Twitter className="w-5 h-5" />
                <a href="#" className="text-sm font-medium hover:text-emerald-500 transition-colors">
                  {profile.username}
                </a>
              </div>
              <div className="flex items-center gap-3 text-zinc-400">
                <Github className="w-5 h-5" />
                <a href="#" className="text-sm font-medium hover:text-emerald-500 transition-colors">
                  github.com/{profile.username.replace('@', '')}
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Message Modal */}
      <AnimatePresence>
        {isMessageModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsMessageModalOpen(false)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-6 border-b border-zinc-800">
                <h3 className="text-lg font-semibold text-white">Message {profile.displayName}</h3>
                <button 
                  onClick={() => setIsMessageModalOpen(false)}
                  className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={handleSendMessage} className="p-6">
                <div className="mb-6">
                  <label htmlFor="message" className="block text-sm font-medium text-zinc-400 mb-2">
                    Your Message
                  </label>
                  <textarea
                    id="message"
                    rows={5}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Hi Alex, I'd love to chat about your latest project..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 resize-none transition-all"
                    required
                  />
                </div>
                
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setIsMessageModalOpen(false)}
                    className="px-5 py-2.5 text-sm font-medium text-zinc-300 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSending || !message.trim()}
                    className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 text-zinc-950 text-sm font-medium rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSending ? (
                      <span className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-zinc-950/30 border-t-zinc-950 rounded-full animate-spin" />
                        Sending...
                      </span>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Send Message
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
