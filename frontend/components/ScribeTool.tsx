'use client';

import React from 'react';
import { Feather, Shield, Sparkles, RefreshCw } from 'lucide-react';
import { useScribeStore } from '@/lib/stores/scribeStore';
import { useSessionStore } from '@/lib/stores/sessionStore';
import { apiClient } from '@/lib/api/client';
import { Button } from './ui/Button';

export const ScribeTool: React.FC = () => {
  const {
    rawText,
    sanitizedText,
    status,
    guardianReport,
    guardianNote,
    setRawText,
    setSanitizedText,
    setStatus,
    setGuardianReport,
    setGuardianNote,
  } = useScribeStore();

  const { sessions, setSession } = useSessionStore();
  const [scanProgress, setScanProgress] = React.useState<string>('');
  const [changeSummary, setChangeSummary] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState<boolean>(false);
  const [isInitializingSession, setIsInitializingSession] = React.useState<boolean>(false);
  const [sessionError, setSessionError] = React.useState<string | null>(null);

  // Get session ID for 'scribe' mode
  const sessionId = sessions['scribe'] || null;

  // Initialize session for 'scribe' mode if needed
  React.useEffect(() => {
    const initializeSession = async () => {
      const scribeSessionId = sessions['scribe'];
      
      if (!scribeSessionId && !isInitializingSession) {
        console.log('[ScribeTool] No scribe session found, creating one...');
        setIsInitializingSession(true);
        setSessionError(null);
        
        try {
          const isHealthy = await apiClient.healthCheck();
          if (!isHealthy) {
            console.warn('[ScribeTool] Health check failed, but attempting session creation anyway...');
          }

          // Retry logic with exponential backoff
          let retries = 3;
          let delay = 1000;
          
          while (retries > 0) {
            try {
              const session = await apiClient.createSession('demo_user');
              // Store session with 'scribe' mode
              setSession(session, 'scribe');
              console.log('[ScribeTool] Scribe session created successfully:', session.session_id);
              setIsInitializingSession(false);
              return; // Success, exit retry loop
            } catch (error: any) {
              console.error(`[ScribeTool] Failed to create session (${4 - retries}/3):`, error);
              retries--;
              
              if (retries > 0) {
                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
              } else {
                // Final failure
                const errorMessage = error?.message || 'Failed to create session';
                console.error('[ScribeTool] Failed to create session after all retries:', errorMessage);
                setSessionError(errorMessage);
                setIsInitializingSession(false);
              }
            }
          }
        } catch (error: any) {
          console.error('[ScribeTool] Error initializing session:', error);
          setSessionError(error?.message || 'Failed to initialize session');
          setIsInitializingSession(false);
        }
      }
    };

    initializeSession();
  }, [sessions, setSession, isInitializingSession]);

  const handleSanitize = async () => {
    if (!rawText.trim()) return;

    setStatus('processing');
    setGuardianNote(null);
    setGuardianReport(null);
    setChangeSummary(null);
    setScanProgress('Checking for PI names and institution identifiers...');

    try {
      // Combined progress steps for both Guardian and Scribe phases
      const allSteps = [
        // Phase 1: Guardian scanning
        'Checking for PI names and institution identifiers...',
        'Scanning for reagent names and chemical structures...',
        'Analyzing for unpublished data and sequences...',
        'Reviewing for proprietary information...',
        'Finalizing safety assessment...',
        // Phase 2: Scribe drafting
        'Analyzing raw thoughts...',
        'Transforming into professional narrative...',
        'Removing sensitive information...',
        'Crafting inspiring message...',
        'Adding professional hashtags...',
        'Finalizing draft...',
      ];
      
      let stepIndex = 0;
      const progressInterval = setInterval(() => {
        if (stepIndex < allSteps.length - 1) {
          stepIndex++;
          setScanProgress(allSteps[stepIndex]);
        }
      }, 1000); // Update every 1000ms
      
      // Get session ID for 'scribe' mode from store
      const currentSessions = useSessionStore.getState().sessions;
      let scribeSessionId = currentSessions['scribe'];
      
      // If no session, try to create one now (user might have clicked before initialization completed)
      if (!scribeSessionId) {
        console.log('[ScribeTool] No session found, attempting to create one now...');
        try {
          const session = await apiClient.createSession('demo_user');
          setSession(session, 'scribe');
          scribeSessionId = session.session_id;
          console.log('[ScribeTool] Session created on-demand:', scribeSessionId);
        } catch (error: any) {
          clearInterval(progressInterval);
          setScanProgress('');
          setStatus('risk');
          setGuardianNote(
            `Failed to create session: ${error?.message || 'Unknown error'}. Please try again or refresh the page.`
          );
          return;
        }
      }
      
      try {
        // Call Scribe directly - it handles Guardian scan + Scribe draft internally
        // This ensures the drafting phase is always triggered
        console.log('[ScribeTool] Calling draftSocialPost API...');
        const draftResponse = await apiClient.draftSocialPost(scribeSessionId, {
              memory_context: rawText,
            });

        clearInterval(progressInterval);
        console.log('[ScribeTool] draftSocialPost returned:', draftResponse);

        // Validate response has content
        if (!draftResponse || !draftResponse.content || draftResponse.content.trim().length === 0) {
          console.error('[ScribeTool] Scribe returned empty content:', draftResponse);
          throw new Error('Scribe agent returned empty content. Please try again.');
        }
        
        setScanProgress('');
        setSanitizedText(draftResponse.content);
              setStatus('success');
              
              // Update guardian report from draft response
              if (draftResponse.guardian_report) {
                setGuardianReport(draftResponse.guardian_report);
              }
        
        // Generate change summary from draft response
        const reportToUse = draftResponse.guardian_report;
        
        // Generate change summary if concerns were detected
        if (reportToUse && reportToUse.concerns && reportToUse.concerns.length > 0) {
          const concerns = reportToUse.concerns;
          // Extract key changes from concerns
          const changes: string[] = [];
          
          concerns.forEach(concern => {
            if (concern.includes('PI name')) {
              const match = concern.match(/Detected PI name\(s\): (.+)/);
              if (match) {
                changes.push(`Removed PI name${match[1].includes(',') ? 's' : ''} (${match[1]})`);
              } else {
                changes.push('Removed PI name(s)');
              }
            } else if (concern.includes('reagent name')) {
              const match = concern.match(/Detected reagent name\(s\): (.+)/);
              if (match) {
                changes.push(`Removed reagent name${match[1].includes(',') ? 's' : ''} (${match[1]})`);
              } else {
                changes.push('Removed reagent name(s)');
              }
            } else if (concern.includes('institution name')) {
              const match = concern.match(/Detected institution name\(s\): (.+)/);
              if (match) {
                changes.push(`Removed institution name${match[1].includes(',') ? 's' : ''} (${match[1]})`);
            } else {
                changes.push('Removed institution name(s)');
              }
            } else if (concern.toLowerCase().includes('defamation')) {
              changes.push('Removed content to prevent defamation risk');
            } else if (concern.toLowerCase().includes('ip') || concern.toLowerCase().includes('sensitive')) {
              changes.push('Sanitized sensitive information');
            }
          });
          
          if (changes.length > 0) {
            setChangeSummary(changes.join('. '));
          }
            }
      } catch (scribeError: any) {
        clearInterval(progressInterval);
        console.error('[ScribeTool] Scribe draft failed:', scribeError);
        setScanProgress('');
        // Show error to user
        setStatus('risk');
        setGuardianNote(
          `Failed to generate professional draft: ${scribeError.message || 'Unknown error'}. Please try again.`
        );
        // Still provide a basic sanitized version
          const cleanDraft = rawText
            .replace(/professor\s+\w+/gi, 'my advisor')
            .replace(/dr\.\s+\w+/gi, 'my advisor')
            .replace(/lab\s+\w+/gi, 'the lab')
            .replace(/hate|terrible|awful/gi, 'challenging')
            .trim();
          setSanitizedText(
            cleanDraft ||
              "Currently iterating on research protocols. Facing some reproducibility challenges, but treating every iteration as a learning opportunity. #PhDLife #Research"
          );
      }
    } catch (error) {
      console.error('Failed to sanitize content:', error);
      setScanProgress('');
      setStatus('risk');
      setGuardianNote(
        'An error occurred while scanning content. Please review manually before posting.'
      );
      setSanitizedText(rawText);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sanitizedText);
      setCopied(true);
      // Reset after 2 seconds
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const handleShareLinkedIn = () => {
    const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
      sanitizedText
    )}`;
    window.open(url, '_blank');
  };

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-stone-800 flex items-center gap-2">
            <Feather className="text-green-600" /> The Scribe
          </h2>
          <p className="text-stone-500">Turn venting into value. Safe for public sharing.</p>
        </div>
        {status === 'success' && (
          <div className="bg-[#CCFF00] text-[#1A1A2E] px-4 py-2 rounded-full font-bold flex items-center gap-2 animate-bounce">
            <Sparkles size={18} /> Ready to Post!
          </div>
        )}
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 min-h-0">
        {/* Input Side */}
        <div className="flex flex-col gap-2 min-h-0">
          <label className="text-sm font-bold text-stone-600 ml-2">
            Raw Thoughts (Private)
          </label>
          <textarea
            className="flex-1 w-full p-6 rounded-3xl bg-white border-2 border-stone-100 focus:border-pink-300 focus:ring-4 focus:ring-pink-50 outline-none resize-none shadow-sm text-stone-600 leading-relaxed text-left"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Dump your frustrations here..."
            style={{ minHeight: '300px' }}
          />
        </div>

        {/* Output Side */}
        <div className="flex flex-col gap-2 relative">
          <label className="text-sm font-bold text-stone-600 ml-2 flex items-center justify-between">
            <span>Sanitized Draft (Public)</span>
            {status === 'risk' && (
              <span className="text-orange-500 flex items-center gap-1 text-xs">
                <Shield size={12} /> Guardian Active
              </span>
            )}
          </label>

          <div
            className={`flex-1 rounded-3xl border-2 p-6 relative transition-all duration-500 flex flex-col min-h-0 ${
              status === 'processing'
                ? 'bg-stone-50 border-stone-100'
                : status === 'success'
                ? 'bg-lime-50 border-lime-300'
                : status === 'risk'
                ? 'bg-orange-50 border-orange-200'
                : 'bg-stone-100 border-dashed border-stone-300'
            }`}
            style={{ maxHeight: 'calc(100vh - 400px)', minHeight: '300px' }}
          >
            {status === 'idle' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-stone-400 opacity-50">
                <RefreshCw size={48} className="mb-2" />
                <p>Waiting for input...</p>
              </div>
            )}

            {status === 'processing' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="w-12 h-12 border-4 border-green-200 border-t-green-500 rounded-full animate-spin mb-4"></div>
                <p className="text-green-700 font-medium animate-pulse text-center px-4">
                  {scanProgress || 'The Guardian is scanning...'}
                </p>
              </div>
            )}

            {(status === 'success' || status === 'risk') && (
              <div className="animate-in fade-in zoom-in duration-300 flex flex-col h-full min-h-0">
                {changeSummary && status === 'success' && (
                  <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-xl flex items-start gap-3 flex-shrink-0">
                    <Shield className="text-orange-600 flex-shrink-0 mt-0.5" size={18} />
                    <p className="text-orange-800 text-sm font-medium leading-relaxed">
                      {changeSummary}
                    </p>
                  </div>
                )}
                <div className="flex-1 overflow-y-auto pr-2 min-h-0">
                  <p className="text-stone-800 text-base leading-relaxed font-normal text-left whitespace-pre-wrap break-words">
                    {sanitizedText.replace(/^(Here is|Of course|I'll help you|I can help|Let me|Sure, here|Here's|Here are|I've|I have).*?(\n\n|\n|$)/i, '').trim()}
                </p>
                </div>
                <div className="mt-6 flex gap-2 flex-shrink-0 pt-4 border-t border-lime-200">
                  <button
                    onClick={handleCopy}
                    className={`px-4 py-2 rounded-xl text-sm font-bold shadow-sm transition-all duration-200 ${
                      copied
                        ? 'bg-black text-white border border-black hover:bg-gray-800'
                        : 'bg-white text-stone-800 border border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    {copied ? 'Copied' : 'Copy Text'}
                  </button>
                  <button
                    onClick={handleShareLinkedIn}
                    className="px-4 py-2 bg-[#0077b5] text-white rounded-xl text-sm font-bold shadow-sm hover:bg-[#006097]"
                  >
                    Share to LinkedIn
                  </button>
                </div>
              </div>
            )}

            {status === 'risk' && guardianNote && (
              <div className="absolute bottom-4 left-4 right-4 bg-white/80 backdrop-blur-sm p-3 rounded-xl border border-orange-200 flex items-start gap-3 text-sm text-orange-800 shadow-sm">
                <Shield className="shrink-0 mt-0.5" size={16} />
                <p>{guardianNote}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-center">
        <Button
          onClick={handleSanitize}
          disabled={status === 'processing' || !rawText.trim() || isInitializingSession}
          className="w-full md:w-auto min-w-[200px]"
        >
          {isInitializingSession ? 'Initializing...' : status === 'processing' ? 'Processing...' : 'Generate Safe Draft'}
        </Button>
      </div>
      
      {/* Show session initialization error */}
      {sessionError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800 text-center">
          <p>Session error: {sessionError}</p>
          <button
            onClick={() => {
              setSessionError(null);
              setIsInitializingSession(false);
              // Trigger re-initialization by clearing the session
              const currentSessions = useSessionStore.getState().sessions;
              if (currentSessions['scribe']) {
                // Force re-initialization
                window.location.reload();
              }
            }}
            className="mt-2 text-red-600 underline hover:text-red-800"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
};


