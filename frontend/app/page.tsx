'use client';

import { useState, useEffect } from 'react';
import { Users, MessageSquare, Feather, Zap, Heart, Menu, X, LayoutDashboard, AlertCircle, Phone } from 'lucide-react';
import { ChatInterface } from '@/components/ChatInterface';
import { ScribeTool } from '@/components/ScribeTool';
import { StruggleMap } from '@/components/StruggleMap';
import { Card } from '@/components/ui/Card';
import { THEME, AGENTS } from '@/lib/constants/theme';
import { apiClient } from '@/lib/api/client';
import { useSessionStore } from '@/lib/stores/sessionStore';

interface RecentSession {
  session_id: string;
  summary: string;
  created_at: string;
  message_count: number;
}

type ViewType = 'dashboard' | 'session' | 'scribe' | 'vent' | 'matchmaker' | 'pi';

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard');
  const [forcedAgentMode, setForcedAgentMode] = useState<'vent' | 'scribe' | 'pi' | 'matchmaker' | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const { userId, setSession, clearMessages } = useSessionStore();

  // Load recent sessions
  useEffect(() => {
    const loadRecentSessions = async () => {
      if (!userId) {
        setLoadingSessions(false);
        return;
      }
      try {
        const data = await apiClient.getRecentSessions(userId, 3);
        setRecentSessions(data.sessions || []);
      } catch (error) {
        console.error('Failed to load recent sessions:', error);
        setRecentSessions([]);
      } finally {
        setLoadingSessions(false);
      }
    };
    loadRecentSessions();
  }, [userId]);

  const handleSessionClick = async (sessionId: string) => {
    try {
      const session = await apiClient.getSession(sessionId);
      setSession(session, 'auto'); // Dashboard uses auto mode
      // Load session history would go here - for now just switch to session view
      setActiveView('session');
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleAgentView = (view: 'vent' | 'scribe' | 'matchmaker' | 'pi') => {
    // Map view to agent mode
    // For matchmaker, we use 'matchmaker' mode which will force matchmaker to run
    const agentModeMap: Record<string, 'vent' | 'scribe' | 'pi' | 'matchmaker'> = {
      'vent': 'vent',
      'scribe': 'scribe',
      'matchmaker': 'matchmaker', // Special mode for matchmaker
      'pi': 'pi',
    };
    setForcedAgentMode(agentModeMap[view] || null);
    setActiveView(view);
    setMobileMenuOpen(false);
  };

  const NavItem = ({
    id,
    icon: Icon,
    label,
  }: {
    id: ViewType;
    icon: typeof Users;
    label: string;
  }) => {
    const isActive = activeView === id;
    
    // Get color classes for each agent
    const getColorClasses = (agentId: string, active: boolean) => {
      if (active) {
        return {
          container: 'bg-[#1A1A2E] text-white shadow-lg',
          icon: 'text-white',
        };
      }
      
      const colors: Record<string, { container: string; icon: string }> = {
        'vent': { container: 'text-pink-500 hover:bg-pink-50 hover:text-pink-700', icon: 'text-pink-500' },
        'matchmaker': { container: 'text-purple-500 hover:bg-purple-50 hover:text-purple-700', icon: 'text-purple-500' },
        'scribe': { container: 'text-emerald-500 hover:bg-emerald-50 hover:text-emerald-700', icon: 'text-emerald-500' },
        'pi': { container: 'text-blue-500 hover:bg-blue-50 hover:text-blue-700', icon: 'text-blue-500' },
      };
      
      return colors[agentId] || { container: 'text-stone-500 hover:bg-stone-100 hover:text-stone-800', icon: 'text-stone-500' };
    };
    
    const colors = getColorClasses(id, isActive);
    
    return (
      <button
        onClick={() => {
          if (id === 'vent' || id === 'scribe' || id === 'matchmaker' || id === 'pi') {
            handleAgentView(id);
          } else {
            setForcedAgentMode(null);
            setActiveView(id);
            setMobileMenuOpen(false);
          }
        }}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 font-medium ${colors.container}`}
      >
        <Icon size={20} className={colors.icon} />
        <span>{label}</span>
      </button>
    );
  };

  return (
    <div className={`flex h-screen w-full ${THEME.bg} font-sans overflow-hidden text-stone-900`}>
      {/* Sidebar (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 p-6 border-r border-stone-200 bg-white/50 backdrop-blur-xl z-20">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="w-10 h-10 bg-[#5B4BFF] rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200">
            <Zap size={24} fill="currentColor" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-tight">
              Research<br />In Public
            </h1>
          </div>
        </div>
        <nav className="space-y-2 flex-1">
          <NavItem id="dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavItem id="session" icon={MessageSquare} label="Auto Mode" />
          <div className="pt-2 pb-1">
            <p className="text-xs font-bold text-stone-400 uppercase tracking-wider px-4 mb-2">Agents</p>
          </div>
          <NavItem id="vent" icon={Heart} label="Vent Validator" />
          <NavItem id="matchmaker" icon={Users} label="Matchmaker" />
          <NavItem id="scribe" icon={Feather} label="The Scribe" />
          <NavItem id="pi" icon={Zap} label="PI Simulator" />
        </nav>
        <div className="mt-auto">
          <Card className="bg-gradient-to-br from-indigo-500 to-purple-600 border-none text-white p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="bg-white/20 p-2 rounded-lg backdrop-blur-md">
                <Heart size={16} className="text-white" fill="currentColor" />
              </div>
              <span className="text-xs font-mono opacity-70">BETA v0.9</span>
            </div>
            <p className="text-sm font-medium mb-1">Streak Active!</p>
            <p className="text-xs opacity-80">You've journaled 3 days in a row.</p>
          </Card>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-stone-100 flex items-center justify-between px-4 z-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[#5B4BFF] rounded-lg flex items-center justify-center text-white">
            <Zap size={18} fill="currentColor" />
          </div>
          <span className="font-bold text-stone-800">Research In Public</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 bg-stone-100 rounded-lg"
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 bg-white z-40 pt-20 px-6 space-y-4">
          <NavItem id="dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavItem id="session" icon={MessageSquare} label="Auto Mode" />
          <div className="pt-2 pb-1">
            <p className="text-xs font-bold text-stone-400 uppercase tracking-wider px-4 mb-2">Agents</p>
          </div>
          <NavItem id="vent" icon={Heart} label="Vent Validator" />
          <NavItem id="matchmaker" icon={Users} label="Matchmaker" />
          <NavItem id="scribe" icon={Feather} label="The Scribe" />
          <NavItem id="pi" icon={Zap} label="PI Simulator" />
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative pt-16 md:pt-0">
        {/* Top Bar */}
        <header className="h-16 px-8 flex items-center justify-between shrink-0">
          <div className="hidden md:block">
            <h2 className="font-bold text-2xl text-stone-800">
              {activeView === 'dashboard' && 'Welcome back, Doc.'}
              {activeView === 'session' && 'Auto Mode'}
              {activeView === 'scribe' && 'The Scribe'}
              {activeView === 'vent' && 'Vent Validator'}
              {activeView === 'matchmaker' && 'Semantic Matchmaker'}
              {activeView === 'pi' && 'PI Simulator'}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-stone-200 rounded-full shadow-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-bold text-stone-600">System Online</span>
            </div>
            <div className="w-10 h-10 rounded-full bg-stone-200 overflow-hidden border-2 border-white shadow-md">
              <img
                src="https://api.dicebear.com/7.x/notionists/svg?seed=Felix"
                alt="User"
              />
            </div>
          </div>
        </header>

        {/* Scrollable Viewport */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
          <div className="max-w-6xl mx-auto h-full">
            {/* VIEW: DASHBOARD */}
            {activeView === 'dashboard' && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <Card className="lg:col-span-2 flex flex-col justify-between min-h-[300px] relative overflow-hidden bg-gradient-to-br from-white to-stone-50">
                    <div>
                      <h3 className="text-xl font-bold text-stone-800 mb-2">
                        Emotional Context
                      </h3>
                      <p className="text-stone-500 mb-6 max-w-md">
                        Your research journey is shared by 12 others today. You are currently
                        clustered near "Methodology fatigue".
                      </p>
                    </div>
                    <StruggleMap />
                  </Card>

                  <div className="space-y-6">
                    <Card>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-stone-700">Recent Sessions</h3>
                        <MessageSquare size={16} className="text-stone-400" />
                      </div>
                      <div className="space-y-3">
                        {loadingSessions ? (
                          <div className="text-stone-400 text-sm py-4 text-center">Loading sessions...</div>
                        ) : recentSessions.length === 0 ? (
                          <div className="text-stone-400 text-sm py-4 text-center">No recent sessions</div>
                        ) : (
                          recentSessions.map((session) => (
                            <div
                              key={session.session_id}
                              onClick={() => handleSessionClick(session.session_id)}
                              className="p-3 rounded-xl bg-stone-50 hover:bg-stone-100 transition-colors cursor-pointer group"
                            >
                              <div className="flex justify-between mb-1">
                                <span className="text-xs font-bold text-stone-400">
                                  {formatTimeAgo(session.created_at)}
                                </span>
                                <span className="w-2 h-2 rounded-full bg-green-400"></span>
                              </div>
                              <p className="text-sm font-medium text-stone-700 line-clamp-2">
                                {session.summary}
                              </p>
                              <p className="text-xs text-stone-400 mt-1">
                                {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    </Card>

                    {/* Weekly Goal Card Removed */}
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Vent Validator */}
                  <div
                    onClick={() => handleAgentView('vent')}
                    className="cursor-pointer group"
                  >
                    <Card animate className="h-full border-l-8 border-l-pink-500">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-pink-100 text-pink-600 rounded-2xl group-hover:scale-110 transition-transform">
                          <Heart size={24} fill="currentColor" className="opacity-50" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">Vent Validator</h3>
                          <p className="text-stone-500 text-sm">Available • Active Listening Mode</p>
                        </div>
                      </div>
                      <p className="text-stone-600">
                        Feeling stuck? Talk it out. I'll help you process the block without judgment.
                      </p>
                    </Card>
                  </div>
                  
                  {/* Semantic Matchmaker */}
                  <div
                    onClick={() => handleAgentView('matchmaker')}
                    className="cursor-pointer group"
                  >
                    <Card animate className="h-full border-l-8 border-l-purple-500">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-purple-100 text-purple-600 rounded-2xl group-hover:scale-110 transition-transform">
                          <Users size={24} fill="currentColor" className="opacity-50" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">Semantic Matchmaker</h3>
                          <p className="text-stone-500 text-sm">Available • Connection Mode</p>
                        </div>
                      </div>
                      <p className="text-stone-600">
                        Find your tribe. I'll connect you with peers who've walked similar paths.
                      </p>
                    </Card>
                  </div>
                  
                  {/* The Scribe */}
                  <div
                    onClick={() => handleAgentView('scribe')}
                    className="cursor-pointer group"
                  >
                    <Card animate className="h-full border-l-8 border-l-emerald-500">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-emerald-100 text-emerald-600 rounded-2xl group-hover:scale-110 transition-transform">
                          <Feather size={24} fill="currentColor" className="opacity-50" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">The Scribe</h3>
                          <p className="text-stone-500 text-sm">Available • Drafting Mode</p>
                        </div>
                      </div>
                      <p className="text-stone-600">
                        Transform your journey into shareable stories. I'll craft your narrative with wisdom and grace.
                      </p>
                    </Card>
                  </div>
                  
                  {/* PI Simulator */}
                  <div
                    onClick={() => handleAgentView('pi')}
                    className="cursor-pointer group"
                  >
                    <Card animate className="h-full border-l-8 border-l-blue-500">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-blue-100 text-blue-600 rounded-2xl group-hover:scale-110 transition-transform">
                          <Zap size={24} fill="currentColor" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">PI Simulator</h3>
                          <p className="text-stone-500 text-sm">Available • Critical Mode</p>
                        </div>
                      </div>
                      <p className="text-stone-600">
                        Need a harsh but fair review? I'll critique your logic before you send it to the real boss.
                      </p>
                    </Card>
                  </div>
                </div>
                
                {/* Crisis Helpline Notice - Bottom of Dashboard */}
                <Card className="bg-red-50 border-2 border-red-300 p-6 mt-6 shadow-lg">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="p-3 bg-red-100 rounded-xl flex-shrink-0">
                      <AlertCircle size={24} className="text-red-600" />
                    </div>
                    <h4 className="text-base font-bold text-red-900">If you are in a crisis or your safety is at risk</h4>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-white rounded-xl border border-red-200 shadow-sm">
                      <div className="flex items-center gap-2 mb-2">
                        <Phone size={18} className="text-red-600" />
                        <span className="text-xs font-semibold text-red-900 uppercase tracking-wide">If you are in a crisis</span>
                      </div>
                      <a href="tel:988" className="block text-2xl font-mono font-bold text-red-600 hover:text-red-700 hover:underline mb-1">
                        CALL OR TEXT 9-8-8
                      </a>
                      <p className="text-sm text-red-700">Suicide Crisis Helpline</p>
                    </div>
                    <div className="p-4 bg-white rounded-xl border border-red-200 shadow-sm">
                      <div className="flex items-center gap-2 mb-2">
                        <Phone size={18} className="text-red-600" />
                        <span className="text-xs font-semibold text-red-900 uppercase tracking-wide">If your safety is at risk</span>
                      </div>
                      <a href="tel:911" className="block text-2xl font-mono font-bold text-red-600 hover:text-red-700 hover:underline mb-1">
                        CALL 9-1-1
                      </a>
                      <p className="text-sm text-red-700">Emergency Services</p>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* VIEW: SESSION (CHAT) - Auto routing */}
            {activeView === 'session' && (
              <Card className="h-[calc(100vh-140px)] animate-in fade-in zoom-in-95 duration-300 flex flex-col overflow-hidden p-0">
                <ChatInterface forcedAgentMode={null} />
              </Card>
            )}

            {/* VIEW: VENT VALIDATOR - Direct agent */}
            {activeView === 'vent' && (
              <Card className="h-[calc(100vh-140px)] animate-in fade-in zoom-in-95 duration-300 flex flex-col overflow-hidden p-0">
                <ChatInterface forcedAgentMode="vent" />
              </Card>
            )}

            {/* VIEW: SEMANTIC MATCHMAKER - Direct agent (uses vent mode but forces matchmaker) */}
            {activeView === 'matchmaker' && (
              <Card className="h-[calc(100vh-140px)] animate-in fade-in zoom-in-95 duration-300 flex flex-col overflow-hidden p-0">
                <ChatInterface forcedAgentMode="matchmaker" />
              </Card>
            )}

            {/* VIEW: PI SIMULATOR - Direct agent */}
            {activeView === 'pi' && (
              <Card className="h-[calc(100vh-140px)] animate-in fade-in zoom-in-95 duration-300 flex flex-col overflow-hidden p-0">
                <ChatInterface forcedAgentMode="pi" />
              </Card>
            )}

            {/* VIEW: SCRIBE */}
            {activeView === 'scribe' && (
              <Card className="h-[calc(100vh-140px)] animate-in fade-in zoom-in-95 duration-300 overflow-hidden">
                <ScribeTool />
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}


