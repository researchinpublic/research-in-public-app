import React, { useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion';
import { Users, ThumbsUp, MessageCircle, Sparkles, RefreshCw, X, Heart, GraduationCap, BookOpen, TrendingUp } from 'lucide-react';

interface PeerProfile {
  id: string;
  name: string;
  academicStage: string;
  researchArea: string;
  struggle: string;
  similarity: number;
  avatar?: string;
}

interface MatchmakerInterfaceProps {
  isTyping: boolean;
  children?: React.ReactNode;
  onReset?: () => void;
  matches?: Array<{
    id: string;
    similarity: number;
    reason?: string;
    role?: string;
    area?: string;
    struggle?: string;
    tags?: string[];
  }>;
}

// Convert backend match format to PeerProfile
const convertMatchesToProfiles = (matches: MatchmakerInterfaceProps['matches']): PeerProfile[] => {
  if (!matches || matches.length === 0) return [];
  
  return matches.map((match, index) => {
    // Generate a name from the match ID or use a placeholder
    const names = ['Alex Chen', 'Samira Patel', 'Jordan Kim', 'Morgan Taylor', 'Riley Davis', 'Casey Lee'];
    const name = names[index % names.length] || `Researcher ${index + 1}`;
    
    return {
      id: match.id,
      name: name,
      academicStage: match.role || 'Researcher',
      researchArea: match.area || 'Research',
      struggle: match.struggle || match.reason || 'Sharing a similar research journey.',
      similarity: Math.round(match.similarity * 100), // Convert 0-1 to percentage
    };
  });
};

// Demo profiles - fallback if no matches
const generateDemoProfiles = (): PeerProfile[] => {
  const stages = ['2nd year PhD', '3rd year PhD', '4th year PhD', 'Postdoc'];
  const areas = ['Machine Learning', 'Computational Biology', 'Neuroscience', 'Quantum Computing', 'Bioinformatics'];
  const struggles = [
    'Struggling with imposter syndrome after my first paper rejection.',
    'Feeling isolated working on a niche research topic.',
    'Overwhelmed by the amount of literature I need to review.',
    'Can\'t find the right balance between research and personal life.',
    'Worried my research direction isn\'t impactful enough.',
    'Experiencing burnout after months of failed experiments.',
    'Feeling stuck on a problem that seems unsolvable.',
    'Anxious about upcoming conference presentation.',
  ];
  
  const names = [
    'Alex Chen', 'Samira Patel', 'Jordan Kim', 'Morgan Taylor',
    'Riley Davis', 'Casey Lee', 'Taylor Brown', 'Quinn Martinez'
  ];

  return Array.from({ length: 8 }, (_, i) => ({
    id: `peer_${i}`,
    name: names[i],
    academicStage: stages[i % stages.length],
    researchArea: areas[i % areas.length],
    struggle: struggles[i % struggles.length],
    similarity: 75 + Math.floor(Math.random() * 20), // 75-95% match
  }));
};

const PeerCard: React.FC<{
  profile: PeerProfile;
  index: number;
  onSwipe: (direction: 'left' | 'right') => void;
  totalCards: number;
}> = ({ profile, index, onSwipe, totalCards }) => {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0, 1, 1, 1, 0]);

  const handleDragEnd = (event: any, info: any) => {
    const threshold = 100;
    if (info.offset.x > threshold) {
      onSwipe('right');
    } else if (info.offset.x < -threshold) {
      onSwipe('left');
    }
  };

  const isTopCard = index === 0;

  return (
    <motion.div
      style={{
        x: isTopCard ? x : 0,
        rotate: isTopCard ? rotate : 0,
        opacity: isTopCard ? opacity : 1,
        zIndex: totalCards - index,
        scale: 1 - index * 0.05,
        y: index * 8,
      }}
      drag={isTopCard ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={handleDragEnd}
      initial={{ scale: 0.8, opacity: 0, y: 50 }}
      animate={{ scale: 1 - index * 0.05, opacity: 1, y: index * 8 }}
      exit={{ x: isTopCard ? (x.get() > 0 ? 500 : -500) : 0, opacity: 0, scale: 0.5 }}
      className="absolute inset-0 cursor-grab active:cursor-grabbing"
    >
      <div className="h-full w-full bg-white rounded-3xl border border-purple-200/50 overflow-hidden flex flex-col" 
           style={{
             boxShadow: '0 10px 40px -8px rgba(139, 92, 246, 0.2), 0 4px 12px -2px rgba(139, 92, 246, 0.1), 0 0 0 1px rgba(139, 92, 246, 0.05)'
           }}>
        {/* Match Score Badge */}
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg flex items-center gap-1">
            <Heart className="w-3 h-3" fill="currentColor" />
            {profile.similarity}% Match
          </div>
        </div>

        {/* Card Content */}
        <div className="flex-1 p-6 flex flex-col">
          {/* Avatar Section */}
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-xl font-bold shadow-lg">
              {profile.name.charAt(0)}
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-stone-800">{profile.name}</h3>
              <div className="flex items-center gap-2 text-sm text-stone-500 mt-1">
                <GraduationCap className="w-4 h-4" />
                <span>{profile.academicStage}</span>
              </div>
            </div>
          </div>

          {/* Research Area */}
          <div className="mb-4">
            <div className="flex items-center gap-2 text-sm text-purple-600 mb-1">
              <BookOpen className="w-4 h-4" />
              <span className="font-semibold">Research Area</span>
            </div>
            <p className="text-stone-700 font-medium">{profile.researchArea}</p>
          </div>

          {/* Struggle/Story */}
          <div className="flex-1 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-4 border border-purple-100">
            <div className="flex items-center gap-2 text-xs text-purple-600 mb-2 font-semibold uppercase tracking-wider">
              <TrendingUp className="w-3 h-3" />
              Their Journey
            </div>
            <p className="text-stone-700 text-sm leading-relaxed italic">
              "{profile.struggle}"
            </p>
          </div>
        </div>

        {/* Action Hints */}
        {isTopCard && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-between px-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: x.get() < -50 ? 1 : 0, x: x.get() < -50 ? 0 : -20 }}
              className="text-red-500 text-4xl font-bold"
            >
              PASS
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: x.get() > 50 ? 1 : 0, x: x.get() > 50 ? 0 : 20 }}
              className="text-green-500 text-4xl font-bold"
            >
              CONNECT
            </motion.div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const MatchmakerInterface: React.FC<MatchmakerInterfaceProps> = ({ isTyping, children, onReset, matches = [] }) => {
  // Convert matches to profiles, or use empty array if no matches
  const initialProfiles = matches.length > 0 ? convertMatchesToProfiles(matches) : [];
  const [profiles, setProfiles] = useState<PeerProfile[]>(initialProfiles);
  const [swipedProfiles, setSwipedProfiles] = useState<Set<string>>(new Set());
  const [showConfetti, setShowConfetti] = useState(false);

  // Update profiles when matches change (new matches from user interaction)
  React.useEffect(() => {
    if (matches.length > 0) {
      const newProfiles = convertMatchesToProfiles(matches);
      setProfiles(newProfiles);
      setSwipedProfiles(new Set()); // Reset swiped when new matches arrive
    } else {
      setProfiles([]);
      setSwipedProfiles(new Set());
    }
  }, [matches]);

  const handleSwipe = (profileId: string, direction: 'left' | 'right') => {
    setSwipedProfiles(prev => new Set(prev).add(profileId));
    
    if (direction === 'right') {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 2000);
    }

    // Remove swiped card after animation
    setTimeout(() => {
      setProfiles(prev => prev.filter(p => p.id !== profileId));
    }, 300);
  };

  const handleConnect = () => {
    if (profiles.length > 0) {
      handleSwipe(profiles[0].id, 'right');
    }
  };

  const visibleProfiles = profiles.filter(p => !swipedProfiles.has(p.id)).slice(0, 3);

  return (
    <div className="h-full w-full bg-gradient-to-br from-purple-50 via-pink-50 to-white relative overflow-hidden rounded-2xl border border-purple-100 flex flex-col shadow-sm">
      {/* Dopamine Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <motion.div 
          className="absolute top-10 right-10 w-40 h-40 bg-yellow-300 rounded-full opacity-20 blur-3xl"
          animate={{ y: [0, 20, 0], x: [0, -10, 0] }}
          transition={{ duration: 5, repeat: Infinity }}
        />
        <motion.div 
          className="absolute bottom-20 left-10 w-60 h-60 bg-pink-300 rounded-full opacity-20 blur-3xl"
          animate={{ y: [0, -30, 0], x: [0, 20, 0] }}
          transition={{ duration: 7, repeat: Infinity }}
        />
      </div>

      {/* Confetti Effect */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none z-50 flex items-center justify-center">
          <motion.div 
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1.5, opacity: [1, 0] }}
            transition={{ duration: 0.8 }}
            className="text-8xl"
          >
            🎉✨🤝
          </motion.div>
        </div>
      )}

      {/* Header */}
      <div className="relative z-10 p-4 flex items-center justify-between bg-white/60 backdrop-blur-sm border-b border-purple-100 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-purple-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-600" />
            Community Finder
          </h2>
          <p className="text-xs text-purple-500 mt-1">
            {profiles.length > 0 
              ? `${profiles.length} potential connections available`
              : 'Share your journey to find peers'}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <button 
            onClick={handleConnect}
            className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full text-xs font-bold hover:bg-purple-200 transition-colors flex items-center gap-1"
          >
            <Sparkles className="w-3 h-3" />
            Connect
          </button>
          <button 
            onClick={onReset}
            className="p-2 text-purple-400 hover:text-purple-700 hover:bg-purple-100 rounded-lg transition-colors"
            title="New Conversation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content Split View */}
      <div className="flex-1 relative z-10 flex overflow-hidden bg-white/30">
        {/* Left Panel: Tinder-style Cards */}
        <div className="w-1/3 border-r border-purple-100 p-6 flex flex-col bg-white/40">
          {/* Card Stack Container - Takes remaining space, with padding for shadows */}
          <div className="flex-1 relative min-h-0 mb-4" style={{ padding: '12px' }}>
            {visibleProfiles.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-stone-400 px-6">
                  <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-semibold mb-2 text-purple-600">
                    {matches.length === 0 ? 'Start a conversation' : 'No more profiles'}
                  </p>
                  <p className="text-sm">
                    {matches.length === 0 
                      ? 'Share your research journey to discover peers with similar experiences.'
                      : 'Check back later for new connections!'}
                  </p>
                </div>
              </div>
            ) : (
              <AnimatePresence>
                {visibleProfiles.map((profile, index) => (
                  <PeerCard
                    key={`${profile.id}-${index}`}
                    profile={profile}
                    index={index}
                    onSwipe={(dir) => handleSwipe(profile.id, dir)}
                    totalCards={visibleProfiles.length}
                  />
                ))}
              </AnimatePresence>
            )}
          </div>

          {/* Action Buttons - Always visible when cards exist */}
          {visibleProfiles.length > 0 && (
            <div className="flex justify-center gap-4 pt-4 border-t border-purple-100 shrink-0">
              <button
                onClick={() => handleSwipe(visibleProfiles[0].id, 'left')}
                className="w-14 h-14 rounded-full bg-white border-2 border-red-200 text-red-500 flex items-center justify-center shadow-lg hover:bg-red-50 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
              <button
                onClick={() => handleSwipe(visibleProfiles[0].id, 'right')}
                className="w-14 h-14 rounded-full bg-gradient-to-r from-pink-500 to-purple-600 text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-all hover:scale-110"
              >
                <Heart className="w-6 h-6" fill="currentColor" />
              </button>
            </div>
          )}
        </div>

        {/* Right Panel: Chat */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
};
