'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Heart, Zap, Feather, Send, Users, Shield } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSessionStore } from '@/lib/stores/sessionStore';
import type { ChatMessage } from '@/lib/stores/sessionStore';
import { apiClient } from '@/lib/api/client';
import { Card } from './ui/Card';
import { AGENTS } from '@/lib/constants/theme';
import type { AgentMode } from '@/lib/types/api';
import { VentInterface } from './specialized/VentInterface';
import { MatchmakerInterface } from './specialized/MatchmakerInterface';
import { PIInterface } from './specialized/PIInterface';

interface ChatInterfaceProps {
  forcedAgentMode?: 'vent' | 'pi' | 'scribe' | 'matchmaker' | null;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ forcedAgentMode = null }) => {
  const {
    sessions,
    userId,
    activeAgent,
    isTyping,
    currentMode,
    addUserMessage,
    addAgentMessage,
    setIsTyping,
    setActiveAgent,
    setSession,
    setMode,
    clearMessages,
    getMessages,
  } = useSessionStore();
  
  // Get session ID for current mode
  const modeKey = forcedAgentMode || 'auto';
  const sessionId = sessions[modeKey] || null;
  
  // Get messages for current mode (each mode has its own conversation history)
  const messages = getMessages(forcedAgentMode);

  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Set active agent when forcedAgentMode changes
  const prevForcedModeRef = React.useRef(forcedAgentMode);
  
  React.useEffect(() => {
    const modeChanged = prevForcedModeRef.current !== forcedAgentMode;
    
    if (modeChanged) {
      prevForcedModeRef.current = forcedAgentMode;
      
      // Update mode in store (each mode maintains its own message history)
      setMode(forcedAgentMode);
      
      // Set active agent immediately based on forced mode
      if (forcedAgentMode === 'vent') {
        setActiveAgent('Vent Validator');
      } else if (forcedAgentMode === 'matchmaker') {
        setActiveAgent('Semantic Matchmaker');
      } else if (forcedAgentMode === 'pi') {
        setActiveAgent('PI Simulator');
      } else if (forcedAgentMode === 'scribe') {
        setActiveAgent('The Scribe');
      } else {
        setActiveAgent(null);
      }
    }
  }, [forcedAgentMode, setActiveAgent, setMode]);
  
  // Use forced agent mode if provided, otherwise use 'auto' for intent detection
  // Each mode is isolated: auto, vent, matchmaker, scribe, pi
  const agentMode: AgentMode = forcedAgentMode || 'auto';

  // Get metadata from the latest agent message
  const lastAgentMessage = [...messages].reverse().find(m => m.sender === 'agent');
  const agentMetadata = lastAgentMessage?.metadata || null;
  
  // Debug: Log metadata when it changes
  React.useEffect(() => {
    if (agentMetadata && forcedAgentMode === 'vent') {
      console.log('[VentInterface] Metadata received:', agentMetadata);
    }
  }, [agentMetadata, forcedAgentMode]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Initialize session for current mode if needed (each mode has its own session)
  useEffect(() => {
    const initializeSession = async () => {
      const currentModeKey = forcedAgentMode || 'auto';
      const currentSessionId = sessions[currentModeKey];
      
      if (!currentSessionId) {
        // Quick readiness check (non-blocking) - only wait 2 seconds max
        console.log('[ChatInterface] Checking backend readiness...');
        const readinessPromise = apiClient.readinessCheck();
        const timeoutPromise = new Promise<boolean>(resolve => setTimeout(() => resolve(false), 2000));
        const isReady = await Promise.race([readinessPromise, timeoutPromise]);
        
        if (!isReady) {
          console.log('[ChatInterface] Backend readiness check timed out or failed, attempting session creation anyway...');
        } else {
          console.log('[ChatInterface] Backend is ready');
        }

        // Try to create session immediately (orchestrator should already be initialized)
        try {
          const session = await apiClient.createSession('demo_user');
          // Store session with mode key
          setSession(session, forcedAgentMode);
          console.log(`[ChatInterface] Session created for mode: ${currentModeKey}`);
        } catch (error: any) {
          console.error(`[ChatInterface] Failed to create session:`, error);
          // Only show error if it's not a 503 (service unavailable - backend still starting)
          if (!error.message?.includes('503') && !error.message?.includes('initializing')) {
            addAgentMessage({
              main_response:
                `Unable to create session. Error: ${error.message}. Please check that the backend is running and accessible.`,
              agent_used: 'Vent Validator',
              trace_id: '',
            }, forcedAgentMode);
            setActiveAgent('Vent Validator');
          }
        }
      }
    };

    initializeSession();
  }, [forcedAgentMode, sessions, setSession, addAgentMessage, setActiveAgent]);

  const handleSend = async () => {
    if (!input.trim()) {
      return; // Don't send empty messages
    }

    // Get session ID for current mode
    const currentModeKey = forcedAgentMode || 'auto';
    let currentSessionId = sessions[currentModeKey];
    
    // If no session for this mode, try to create one immediately (skip health check for speed)
    if (!currentSessionId) {
      try {
        // Create session directly without health check (orchestrator should already be ready)
        const session = await apiClient.createSession('demo_user');
        setSession(session, forcedAgentMode);
        currentSessionId = session.session_id;
        console.log(`[ChatInterface] Created session on-demand for mode: ${modeKey}`);
      } catch (error: any) {
        // Only show error if it's not a temporary 503 (backend still initializing)
        if (!error.message?.includes('503') && !error.message?.includes('initializing')) {
          addAgentMessage({
            main_response: `Failed to create session: ${error.message}. Please try again.`,
            agent_used: 'Vent Validator',
            trace_id: '',
          }, forcedAgentMode);
          setActiveAgent('Vent Validator');
        }
        return;
      }
    }

    const userText = input.trim();
    addUserMessage(userText, modeKey); // Use modeKey for consistency (modeKey is 'auto' when forcedAgentMode is null)
    setInput('');
    setIsTyping(true);

    try {
      // No need to force matchmaker anymore - matchmaker mode handles it directly
      // Try streaming first, fallback to regular if it fails
      let accumulatedText = '';
      let streamingAgentId = 'vent-validator';
      let streamingMessageId: string | null = null;
      let finalResponse: any = null;

      try {
        console.log('[ChatInterface] Starting stream for message:', userText.substring(0, 50));
        for await (const chunk of apiClient.streamMessage(
          currentSessionId!,
          { content: userText },
          agentMode,
          false // No force_matchmaker needed - mode isolation handles it
        )) {
          console.log('[ChatInterface] Received chunk:', chunk.type, chunk);
          
          if (chunk.type === 'text' && chunk.text) {
            accumulatedText += chunk.text;
            
            // Create or update streaming message
            if (!streamingMessageId) {
              // Create new message
              const tempId = `streaming-${Date.now()}`;
              streamingMessageId = tempId;
              // Default to Vent Validator, but will be updated when we get agent_used from complete chunk
              streamingAgentId = mapAgentToId('Vent Validator');
              // Add initial message - use modeKey instead of forcedAgentMode for consistency
              const currentMessages = useSessionStore.getState().getMessages(modeKey);
              const currentModeMessages = useSessionStore.getState().messages;
              useSessionStore.setState({
                messages: {
                  ...currentModeMessages,
                  [modeKey]: [
                    ...currentMessages,
                    {
                      id: streamingMessageId,
                      sender: 'agent' as const,
                      agentId: streamingAgentId,
                      text: accumulatedText,
                      timestamp: new Date(),
                      traceId: currentSessionId!,
                    },
                  ],
                },
              });
            } else {
              // Update existing message - use functional update to avoid race conditions
              useSessionStore.setState((state) => {
                const modeMessages = state.messages[modeKey] || [];
                const messageIndex = modeMessages.findIndex(m => m.id === streamingMessageId);
                if (messageIndex >= 0) {
                  const updatedMessages = [...modeMessages];
                  updatedMessages[messageIndex] = {
                    ...updatedMessages[messageIndex],
                    text: accumulatedText,
                  };
                  return {
                    messages: {
                      ...state.messages,
                      [modeKey]: updatedMessages,
                    },
                  };
                }
                return state;
              });
            }
          } else if (chunk.type === 'complete') {
            finalResponse = chunk;
            accumulatedText = chunk.main_response || accumulatedText;
            
            // Finalize the message
            if (streamingMessageId) {
              // Update the streaming message with final data
              useSessionStore.setState((state) => {
                const modeMessages = state.messages[modeKey] || [];
                const messageIndex = modeMessages.findIndex(m => m.id === streamingMessageId);
                if (messageIndex >= 0) {
                  const updatedMessages = [...modeMessages];
                  updatedMessages[messageIndex] = {
                    ...updatedMessages[messageIndex],
                    agentId: mapAgentToId(chunk.agent_used || 'Vent Validator'),
                    text: accumulatedText,
                    traceId: chunk.trace_id || currentSessionId!,
                    metadata: chunk.agent_metadata, // Store metadata
                  };
                  return {
                    messages: {
                      ...state.messages,
                      [modeKey]: updatedMessages,
                    },
                    activeAgent: chunk.agent_used || 'Vent Validator',
                  };
                }
                return state;
              });
            } else {
              // Use modeKey instead of forcedAgentMode for consistency
              addAgentMessage({
                main_response: accumulatedText,
                agent_used: chunk.agent_used || 'Vent Validator',
                trace_id: chunk.trace_id || currentSessionId!,
                agent_metadata: chunk.agent_metadata, // Pass metadata
              }, modeKey);
            }
            
            setActiveAgent(chunk.agent_used || 'Vent Validator');
            
            // Add peer matches if available (only in auto mode)
            // In matchmaker mode, peer_matches are already in main_response
            if (chunk.peer_matches && agentMode === 'auto') {
              addAgentMessage({
                main_response: chunk.peer_matches,
                agent_used: 'Semantic Matchmaker',
                trace_id: currentSessionId!,
              }, 'auto');
            }
            
            // Add social draft if available (only in auto or scribe mode)
            // In scribe mode, social_draft is already in main_response
            if (chunk.social_draft && agentMode === 'auto') {
              addAgentMessage({
                main_response: chunk.social_draft,
                agent_used: 'The Scribe',
                trace_id: currentSessionId!,
              }, 'auto');
            }
          } else if (chunk.type === 'error') {
            throw new Error(chunk.error || 'Unknown error');
          }
        }
      } catch (streamError: any) {
        console.warn('Streaming failed, falling back to regular request:', streamError);
        
        // Check if it's a session not found error
        if (streamError.message && streamError.message.includes('Session not found')) {
          // Clear the session and try to create a new one for this mode
          console.log('[ChatInterface] Session not found in stream, creating new session...');
          try {
            const newSession = await apiClient.createSession('demo_user');
            setSession(newSession, forcedAgentMode); // setSession handles null correctly
            // Retry with new session (non-streaming)
            const response = await apiClient.processMessage(
              newSession.session_id,
              { content: userText },
              agentMode
            );
            addAgentMessage(response, modeKey);
            setActiveAgent(response.agent_used);
            return; // Exit early
          } catch (sessionError: any) {
            addAgentMessage({
              main_response:
                `Session error: ${sessionError.message}. Please refresh the page.`,
              agent_used: 'Vent Validator',
              trace_id: '',
            }, modeKey);
            setActiveAgent('Vent Validator');
            return;
          }
        }
        
        // Fallback to non-streaming for other errors
        try {
          const response = await apiClient.processMessage(
            currentSessionId!,
            { content: userText },
            agentMode
          );
          addAgentMessage(response, modeKey);
          setActiveAgent(response.agent_used);
        } catch (fallbackError: any) {
          // If fallback also fails with session error, handle it
          if (fallbackError.message && fallbackError.message.includes('Session not found')) {
            console.log('[ChatInterface] Session not found in fallback, creating new session...');
            try {
              const newSession = await apiClient.createSession('demo_user');
              setSession(newSession, forcedAgentMode); // setSession handles null correctly
              addAgentMessage({
                main_response:
                  `Session expired. I've created a new session. Please try sending your message again.`,
                agent_used: 'Vent Validator',
                trace_id: newSession.session_id,
              }, modeKey);
              setActiveAgent('Vent Validator');
            } catch (sessionError: any) {
              addAgentMessage({
                main_response:
                  `Session error: ${sessionError.message}. Please refresh the page.`,
                agent_used: 'System',
                trace_id: '',
              }, modeKey);
            }
          } else {
            throw fallbackError; // Re-throw if it's a different error
          }
        }
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
        // Check if it's a session not found error
        if (error.message && error.message.includes('Session not found')) {
          // Clear the session and try to create a new one
          console.log('[ChatInterface] Session not found, creating new session...');
          try {
            const newSession = await apiClient.createSession('demo_user');
            useSessionStore.getState().setSession(newSession, forcedAgentMode); // setSession handles null correctly
            // Retry the message with the new session
            console.log('[ChatInterface] Retrying message with new session...');
            // Don't retry automatically - let user try again
            addAgentMessage({
              main_response:
                `Session expired. I've created a new session. Please try sending your message again.`,
              agent_used: 'System',
              trace_id: newSession.session_id,
            }, modeKey);
        } catch (sessionError: any) {
          addAgentMessage({
            main_response:
              `Session error: ${sessionError.message}. Please refresh the page.`,
            agent_used: 'System',
            trace_id: '',
          }, modeKey);
        }
      } else {
        addAgentMessage({
          main_response:
            `I'm sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or check your connection.`,
          agent_used: 'Vent Validator',
          trace_id: currentSessionId || '',
        }, modeKey);
        setActiveAgent('Vent Validator');
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleReset = async () => {
    // Create new session
    try {
      // Create new session
      const newSession = await apiClient.createSession('demo_user');
      // Set session for current mode
      setSession(newSession, forcedAgentMode);
      // Clear messages for current mode only
      clearMessages(forcedAgentMode);
    } catch (error) {
      console.error("Failed to reset session:", error);
    }
  };

  const mapAgentToId = (agent: string): string => {
    const mapping: Record<string, string> = {
      'Vent Validator': 'vent-validator',
      'Semantic Matchmaker': 'semantic-matchmaker',
      'The Scribe': 'the-scribe',
      'PI Simulator': 'pi-simulator',
      'Auto Mode': 'auto-mode',
    };
    // Default to vent-validator for unknown agents (including System, Academic Peer, etc.)
    return mapping[agent] || 'vent-validator';
  };

  const getAgentIcon = (agentId?: string) => {
    if (!agentId) return MessageSquare;
    
    // Four distinct icons for the main agents
    if (agentId === 'vent-validator') return Heart;
    if (agentId === 'semantic-matchmaker') return Users;
    if (agentId === 'the-scribe') return Feather;
    if (agentId === 'pi-simulator') return Zap;
    if (agentId === 'the-guardian') return Shield;
    if (agentId === 'auto-mode') return MessageSquare; // Auto mode uses MessageSquare icon
    return MessageSquare;
  };

  const getAgentColor = (agentId?: string) => {
    if (!agentId) return 'text-gray-500';
    
    if (agentId === 'vent-validator') return 'text-pink-500';
    if (agentId === 'pi-simulator') return 'text-blue-600';
    if (agentId === 'the-scribe') return 'text-green-600';
    if (agentId === 'semantic-matchmaker') return 'text-purple-600';
    return 'text-gray-500';
  };

  const getAgentBgColor = (agentId?: string) => {
    if (!agentId) return 'bg-gray-50 border-gray-100 text-gray-900';
    
    // Distinct color schemes for each agent
    if (agentId === 'vent-validator') return 'bg-pink-50 border-pink-200 text-pink-900';
    if (agentId === 'semantic-matchmaker') return 'bg-purple-50 border-purple-200 text-purple-900';
    if (agentId === 'the-scribe') return 'bg-emerald-50 border-emerald-200 text-emerald-900';
    if (agentId === 'pi-simulator') return 'bg-blue-50 border-blue-200 text-blue-900';
    if (agentId === 'the-guardian') return 'bg-amber-50 border-amber-200 text-amber-900';
    return 'bg-gray-50 border-gray-100 text-gray-900';
  };
  
  const getAgentIconBg = (agentId?: string) => {
    if (!agentId) return 'bg-gray-100 text-gray-600';
    
    // Matching icon background colors
    if (agentId === 'vent-validator') return 'bg-pink-100 text-pink-600';
    if (agentId === 'semantic-matchmaker') return 'bg-purple-100 text-purple-600';
    if (agentId === 'the-scribe') return 'bg-emerald-100 text-emerald-600';
    if (agentId === 'pi-simulator') return 'bg-blue-100 text-blue-600';
    if (agentId === 'the-guardian') return 'bg-amber-100 text-amber-600';
    return 'bg-gray-100 text-gray-600';
  };

  // --- RENDER HELPERS ---

  // Standard Chat Header (for Auto Mode)
  const StandardHeader = () => (
      <div className="flex items-center justify-between mb-4 px-2">
        <div className="flex items-center gap-3">
          {(() => {
            // Determine active agent: use forcedAgentMode if set, otherwise use activeAgent from store
            // For Auto Mode (forcedAgentMode === null), show "Auto Mode"
            let displayAgent: string | null = null;
            if (forcedAgentMode === null) {
              displayAgent = 'Auto Mode'; 
            } else if (activeAgent) {
              displayAgent = activeAgent;
            }
            
            if (sessionId && displayAgent) {
              const activeAgentId = mapAgentToId(displayAgent);
              const ActiveIcon = getAgentIcon(activeAgentId);
              return (
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shadow-sm ${getAgentIconBg(activeAgentId)}`}>
                  <ActiveIcon size={20} />
                </div>
              );
            }
            return null;
          })()}
          <div>
            <h2 className="text-xl font-bold text-stone-800 font-display">
              {sessionId ? 'Session Active' : 'Connecting...'}
            </h2>
            <div className="flex items-center gap-2 mt-1">
                <div
                  className={`w-2 h-2 rounded-full ${
                    !sessionId
                      ? 'bg-yellow-500 animate-pulse'
                      : 'bg-indigo-500' // Default/Auto color
                  }`}
                />
                <span className="text-xs text-stone-500 font-medium">
                  {!sessionId 
                    ? 'Initializing session...' 
                    : currentMode === 'auto' ? 'Auto Mode' : 'Ready'}
                </span>
            </div>
          </div>
        </div>
      </div>
  );

  // Chat Content (Messages + Input)
  const ChatContent = (
    <>
      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 px-2 py-4 custom-scrollbar"
      >
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const Icon = getAgentIcon(msg.agentId);
          const agentStyle = !isUser ? getAgentBgColor(msg.agentId) : '';

          return (
            <div
              key={msg.id}
              className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 mt-1 shadow-md ${getAgentIconBg(msg.agentId)}`}
                >
                  <Icon size={18} />
                </div>
              )}
              <div
                className={`max-w-[80%] p-4 rounded-2xl shadow-sm border ${
                  isUser
                    ? 'bg-white text-stone-800 border-stone-100 rounded-br-none'
                    : `${agentStyle} rounded-bl-none`
                }`}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                ) : (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                        code: ({ children, className }) => {
                          const isInline = !className;
                          return isInline ? (
                            <code className="bg-stone-100 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                          ) : (
                            <code className="block bg-stone-100 p-2 rounded text-sm font-mono overflow-x-auto">{children}</code>
                          );
                        },
                        ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                        li: ({ children }) => <li className="ml-2">{children}</li>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-stone-300 pl-4 italic my-2">{children}</blockquote>
                        ),
                        h1: ({ children }) => <h1 className="text-xl font-bold mb-2 mt-4 first:mt-0">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-4 first:mt-0">{children}</h3>,
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {isTyping && (
          <div className="flex items-center gap-2 ml-10 text-stone-400 text-xs animate-pulse">
            <span className="w-2 h-2 bg-stone-300 rounded-full"></span>
            <span className="w-2 h-2 bg-stone-300 rounded-full animation-delay-100"></span>
            <span className="w-2 h-2 bg-stone-300 rounded-full animation-delay-200"></span>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="mt-4 relative shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={sessionId ? "Type your thoughts..." : "Waiting for session..."}
          disabled={isTyping}
          className={`w-full bg-white border-2 rounded-2xl py-4 px-6 pr-16 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50 transition-all shadow-sm text-stone-700 placeholder-stone-400 ${
            !sessionId ? 'border-yellow-200 bg-yellow-50' : 'border-stone-100'
          } ${isTyping ? 'opacity-60 cursor-wait' : ''}`}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isTyping}
          className="absolute right-2 top-2 p-2 bg-[#1A1A2E] text-white rounded-xl hover:scale-95 transition-transform disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
          title={!input.trim() ? "Type a message" : isTyping ? "Sending..." : "Send message"}
        >
          <Send size={20} />
        </button>
      </div>
    </>
  );

  // Main Render Logic
  if (forcedAgentMode === 'vent') {
    return (
      <VentInterface metadata={agentMetadata} onReset={handleReset}>
        {ChatContent}
      </VentInterface>
    );
  }

  if (forcedAgentMode === 'matchmaker') {
    // Extract matches from Semantic Matchmaker messages
    const matchmakerMessages = messages.filter(m => 
      m.agentId === 'semantic-matchmaker' && m.metadata?.matches
    );
    const matches = matchmakerMessages.length > 0 
      ? matchmakerMessages[matchmakerMessages.length - 1].metadata?.matches || []
      : [];
    
    return (
      <MatchmakerInterface 
        isTyping={isTyping} 
        onReset={handleReset}
        matches={matches}
      >
         {ChatContent}
      </MatchmakerInterface>
    );
  }

  if (forcedAgentMode === 'pi') {
    return (
      <PIInterface metadata={agentMetadata} onReset={handleReset}>
        {ChatContent}
      </PIInterface>
    );
  }

  // Default / Auto Mode
  return (
    <div className="flex flex-col h-full">
      <StandardHeader />
      {ChatContent}
    </div>
  );
};
