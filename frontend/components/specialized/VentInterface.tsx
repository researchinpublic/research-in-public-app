import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Wind, Activity, Brain, RefreshCw } from 'lucide-react';

interface EmotionalMetadata {
  emotional_spectrum?: string;
  emotional_intensity?: number;
  grounding_technique?: string;
}

interface VentInterfaceProps {
  metadata: EmotionalMetadata | null;
  children?: React.ReactNode;
  onReset?: () => void;
}

export const VentInterface: React.FC<VentInterfaceProps> = ({ metadata, children, onReset }) => {
  // Default to "Neutral" if no metadata yet
  const emotion = metadata?.emotional_spectrum || "Neutral";
  const intensity = metadata?.emotional_intensity || 3;
  const groundingTech = metadata?.grounding_technique || "Focus on your breathing";

  // Map emotions to colors (Tailwind classes)
  const getEmotionColor = (emotion: string) => {
    const e = emotion.toLowerCase();
    
    // High Intensity / Negative
    if (e.includes('anxiety') || e.includes('fear') || e.includes('panic')) return 'from-orange-400 to-red-500';
    if (e.includes('anger') || e.includes('frustration') || e.includes('rage')) return 'from-red-500 to-pink-600';
    if (e.includes('overwhelm') || e.includes('stress') || e.includes('burnout')) return 'from-purple-500 to-red-500';
    
    // Low Mood / Depressive
    if (e.includes('sad') || e.includes('grief') || e.includes('depression')) return 'from-blue-400 to-indigo-500';
    if (e.includes('isolation') || e.includes('lonely') || e.includes('alone')) return 'from-indigo-400 to-slate-600';
    if (e.includes('exhaustion') || e.includes('tired') || e.includes('fatigue')) return 'from-slate-400 to-stone-500';
    
    // Complex / Cognitive
    if (e.includes('imposter') || e.includes('inadequacy')) return 'from-violet-400 to-purple-600';
    if (e.includes('confusion') || e.includes('stuck') || e.includes('uncertainty')) return 'from-amber-300 to-orange-400';
    if (e.includes('rejection') || e.includes('failure')) return 'from-rose-400 to-red-600';
    if (e.includes('stagnation') || e.includes('blocked')) return 'from-stone-400 to-gray-500';

    // Positive / Relief
    if (e.includes('happy') || e.includes('joyful') || e.includes('joy') || e.includes('cheerful')) return 'from-yellow-300 to-orange-400';
    if (e.includes('calm') || e.includes('peace') || e.includes('grounded')) return 'from-teal-400 to-emerald-500';
    if (e.includes('relief') || e.includes('better')) return 'from-emerald-400 to-cyan-500';
    if (e.includes('clarity') || e.includes('clear')) return 'from-cyan-400 to-blue-500';
    if (e.includes('hope') || e.includes('optimism')) return 'from-sky-400 to-blue-400';
    if (e.includes('pride') || e.includes('accomplish')) return 'from-yellow-400 to-amber-500';
    if (e.includes('curiosity') || e.includes('interest')) return 'from-lime-400 to-green-500';

    // Default
    return 'from-slate-300 to-gray-400';
  };

  const getEmoji = (emotion: string) => {
    const e = emotion.toLowerCase();
    
    if (e.includes('anxiety')) return '😰';
    if (e.includes('frustration')) return '😤';
    if (e.includes('anger')) return '😡';
    if (e.includes('sad')) return '😢';
    if (e.includes('overwhelm')) return '🤯';
    if (e.includes('imposter')) return '🎭';
    if (e.includes('isolation')) return '🌑';
    if (e.includes('confusion')) return '😵‍💫';
    if (e.includes('exhaustion')) return '😫';
    if (e.includes('rejection')) return '💔';
    if (e.includes('stagnation')) return '🪨';
    
    // Positive emotions - check happy/joyful first for accurate detection
    if (e.includes('joyful') || e.includes('joy')) return '😁';
    if (e.includes('happy') || e.includes('cheerful') || e.includes('glad')) return '😊';
    if (e.includes('calm')) return '😌';
    if (e.includes('relief')) return '😮‍💨';
    if (e.includes('clarity')) return '✨';
    if (e.includes('hope')) return '🌱';
    if (e.includes('pride')) return '🦁';
    if (e.includes('curiosity')) return '🧐';
    
    return '😐';
  };

  const gradientClass = getEmotionColor(emotion);
  const emoji = getEmoji(emotion);

  // Determine ambient background intensity based on emotional intensity (1-10)
  const pulseDuration = Math.max(2, 12 - intensity); // Faster pulse for higher intensity

  return (
    <div className="h-full w-full relative overflow-hidden rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col">
      {/* Ambient Background */}
      <motion.div 
        className={`absolute inset-0 opacity-10 bg-gradient-to-br ${gradientClass}`}
        animate={{ opacity: [0.05, 0.15, 0.05] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Header: Grounding Dashboard */}
      <div className="relative z-10 p-4 border-b border-slate-100 flex items-center justify-between bg-white/80 backdrop-blur-sm shrink-0">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Heart className={`w-5 h-5 ${intensity > 7 ? 'text-red-500 animate-pulse' : 'text-pink-500'}`} />
            Emotional Monitor
          </h2>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Intensity Meter */}
          <div className="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
            <Activity className="w-3 h-3 text-slate-400" />
            <div className="flex flex-col">
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider leading-none mb-0.5">Intensity</span>
              <div className="flex items-center gap-0.5">
                {[...Array(10)].map((_, i) => (
                  <motion.div 
                    key={i}
                    initial={{ height: 3 }}
                    animate={{ 
                      height: i < intensity ? 8 : 3,
                      backgroundColor: i < intensity ? (i > 7 ? '#EF4444' : i > 4 ? '#F59E0B' : '#10B981') : '#E2E8F0'
                    }}
                    className="w-1 rounded-full"
                  />
                ))}
              </div>
            </div>
            <span className="text-base font-bold text-slate-700 w-5 text-center">{intensity}</span>
          </div>
          
          <button 
            onClick={onReset}
            className="p-2 text-slate-400 hover:text-pink-500 hover:bg-pink-50 rounded-lg transition-colors"
            title="New Conversation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 relative z-10 flex overflow-hidden">
        {/* Visualization Panel (Left/Top) */}
        <div className="w-1/3 border-r border-slate-100 bg-slate-50/50 p-4 flex flex-col items-center justify-start gap-6 overflow-y-auto hide-scrollbar">
            {/* Emotional State Visualization */}
            <div className="flex flex-col items-center text-center gap-2 mt-4">
              <div className="relative">
                <motion.div 
                  className={`w-32 h-32 rounded-full bg-gradient-to-br ${gradientClass} opacity-20 blur-xl absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2`}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: pulseDuration, repeat: Infinity }}
                />
                <div className="w-24 h-24 rounded-full bg-white border-4 border-white shadow-lg flex items-center justify-center relative z-10">
                  <span className="text-5xl">
                    {emoji}
                  </span>
                </div>
              </div>
              
              <div>
                <h3 className="text-base font-medium text-slate-700">State: <span className="font-bold capitalize">{emotion}</span></h3>
              </div>
            </div>

            {/* Grounding Technique Card */}
            {metadata && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full bg-white rounded-xl border border-indigo-100 shadow-sm p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600">
                    <Wind className="w-4 h-4" />
                  </div>
                  <h4 className="font-semibold text-sm text-indigo-900">Grounding Tip</h4>
                </div>
                
                <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                  <h5 className="font-bold text-slate-800 text-sm mb-1">{groundingTech}</h5>
                  <p className="text-slate-600 text-xs leading-relaxed">
                    {getTechniqueDescription(groundingTech)}
                  </p>
                </div>
                
                <div className="mt-3 flex justify-center">
                  <a 
                    href={getGroundingArticleLink(groundingTech)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] font-medium text-indigo-500 hover:text-indigo-700 flex items-center gap-1 transition-colors cursor-pointer hover:underline"
                  >
                    <Brain className="w-3 h-3" /> Why helps?
                  </a>
                </div>
              </motion.div>
            )}

             {/* Breathing Guide */}
            <div className="mt-auto mb-4">
              <motion.div 
                className="w-16 h-16 rounded-full border-2 border-slate-200 flex items-center justify-center text-slate-400 text-[10px]"
                animate={{ scale: [1, 1.1, 1], borderColor: ['#E2E8F0', '#94A3B8', '#E2E8F0'] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                Breathe
              </motion.div>
            </div>
        </div>

        {/* Chat Area (Right/Bottom) */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-white/50 relative">
           {children}
        </div>
      </div>
    </div>
  );
};

// Helper to provide descriptions for common techniques
function getTechniqueDescription(tech: string): string {
  const t = tech.toLowerCase();
  if (t.includes('5-4-3-2-1')) return "Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste. This grounds your senses.";
  if (t.includes('box breathing')) return "Inhale 4s, hold 4s, exhale 4s, hold 4s. Regulates the nervous system.";
  if (t.includes('muscle')) return "Tense and relax muscles from toes to head. Releases physical tension.";
  if (t.includes('sensory')) return "Focus entirely on one object nearby. Interrupts ruminating thoughts.";
  if (t.includes('grounding object')) return "Hold a physical object. Notice its weight, texture, and temperature.";
  if (t.includes('visual anchor')) return "Find 5 things of a specific color in the room. Re-engages the visual cortex.";
  return "Pause. Feel your feet on the floor. You are safe.";
}

// Helper to get professional article links for grounding techniques
function getGroundingArticleLink(tech: string): string {
  const t = tech.toLowerCase();
  
  // Professional articles from reputable sources
  if (t.includes('5-4-3-2-1') || t.includes('sensory')) {
    return "https://www.healthline.com/health/grounding-techniques#5-4-3-2-1-technique";
  }
  if (t.includes('box breathing') || t.includes('breathing')) {
    return "https://www.health.harvard.edu/mind-and-mood/relaxation-techniques-breath-control-helps-quell-errant-stress-response";
  }
  if (t.includes('muscle') || t.includes('progressive')) {
    return "https://www.mayoclinic.org/healthy-lifestyle/stress-management/in-depth/relaxation-technique/art-20045368";
  }
  if (t.includes('grounding') || t.includes('object')) {
    return "https://www.psychologytoday.com/us/basics/grounding";
  }
  if (t.includes('visual') || t.includes('anchor')) {
    return "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3772975/";
  }
  
  // Default to general grounding techniques article
  return "https://www.verywellmind.com/grounding-techniques-for-ptsd-2797300";
}
