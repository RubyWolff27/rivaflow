import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { Sparkles, Send, Trash2, MessageCircle, ThumbsUp, ThumbsDown, Zap, Brain, BookOpen, Mic, MicOff, Settings, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { grappleApi } from '../api/client';
import { logger } from '../utils/logger';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import ConfirmDialog from '../components/ConfirmDialog';
import SessionExtractionPanel from '../components/grapple/SessionExtractionPanel';
import InsightsPanel from '../components/grapple/InsightsPanel';
import TechniqueQAPanel from '../components/grapple/TechniqueQAPanel';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
}

interface TierInfo {
  tier: string;
  is_beta: boolean;
  features: {
    grapple: boolean;
  };
  limits: {
    grapple_messages_per_hour: number;
  };
}

type ActivePanel = 'chat' | 'extract' | 'insights' | 'technique-qa';

export default function Grapple() {
  usePageTitle('Grapple AI');
  const { user: _user } = useAuth();
  const toast = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [tierInfo, setTierInfo] = useState<TierInfo | null>(null);
  const [rateLimit, setRateLimit] = useState<{ remaining: number; limit: number } | null>(null);
  const [deleteSessionConfirmId, setDeleteSessionConfirmId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<ActivePanel>('chat');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const onTranscript = useCallback((transcript: string) => {
    setInput(prev => prev ? `${prev} ${transcript}` : transcript);
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
  }, [toast]);
  const { isRecording, isTranscribing, hasSpeechApi, toggleRecording } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

  // Handle query params: ?session= (insight click-through), ?panel= (dashboard deep link)
  useEffect(() => {
    const sessionParam = searchParams.get('session');
    const panelParam = searchParams.get('panel');
    let changed = false;
    if (sessionParam) {
      setCurrentSessionId(sessionParam);
      setActivePanel('chat');
      changed = true;
    }
    if (panelParam) {
      const panelMap: Record<string, ActivePanel> = {
        chat: 'chat',
        extract: 'extract',
        technique: 'technique-qa',
        insights: 'insights',
      };
      if (panelMap[panelParam]) {
        setActivePanel(panelMap[panelParam]);
        changed = true;
      }
    }
    if (changed) {
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [tierRes, sessionsRes] = await Promise.all([
          grappleApi.getInfo(),
          grappleApi.getSessions(),
        ]);
        if (!cancelled) {
          setTierInfo(tierRes.data);
          setSessions(sessionsRes.data.sessions);
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Failed to load grapple data:', error);
          toast.error('Failed to load Grapple AI');
        }
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!currentSessionId) return;
    let cancelled = false;
    const doLoad = async () => {
      try {
        const response = await grappleApi.getSession(currentSessionId);
        if (!cancelled) setMessages(response.data.messages || []);
      } catch (error) {
        if (!cancelled) {
          logger.error('Failed to load session:', error);
          toast.error('Failed to load chat session');
        }
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [currentSessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    try {
      const response = await grappleApi.getSessions();
      setSessions(response.data.sessions);
    } catch (error) {
      logger.error('Failed to load sessions:', error);
      toast.error('Failed to load chat sessions');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!tierInfo?.features.grapple) {
      toast.error('Grapple AI Coach requires a Premium subscription');
      return;
    }

    const userMessage: Message = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await grappleApi.chat({
        message: userMessage.content,
        session_id: currentSessionId,
      });

      const assistantMessage: Message = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setRateLimit({
        remaining: response.data.rate_limit_remaining,
        limit: tierInfo?.limits.grapple_messages_per_hour || 30,
      });

      if (!currentSessionId) {
        setCurrentSessionId(response.data.session_id);
        loadSessions();
      }
    } catch (error: unknown) {
      logger.error('Chat error:', error);
      const e = error as { response?: { status?: number; data?: { detail?: string | { message?: string } } } };
      const detail = e.response?.data?.detail;
      const errorMsg = (typeof detail === 'object' ? detail?.message : detail) || 'Failed to get response';

      setMessages((prev) => [
        ...prev,
        { id: 'error-' + Date.now(), role: 'assistant', content: `Error: ${errorMsg}` },
      ]);

      if (e.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait before sending more messages.');
      } else if (e.response?.status === 403) {
        toast.error('Grapple AI Coach requires a Premium subscription');
      } else {
        toast.error('Failed to send message');
      }
    } finally {
      setLoading(false);
    }
  };

  const newChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setActivePanel('chat');
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await grappleApi.deleteSession(sessionId);

      toast.success('Session deleted');
      setDeleteSessionConfirmId(null);
      loadSessions();

      if (currentSessionId === sessionId) {
        newChat();
      }
    } catch (error) {
      logger.error('Failed to delete session:', error);
      toast.error('Failed to delete session');
    }
  };

  const submitFeedback = async (messageId: string, rating: 'positive' | 'negative') => {
    try {
      await grappleApi.submitFeedback({ message_id: messageId, rating });
      toast.success('Thank you for your feedback!');
    } catch (error) {
      logger.error('Failed to submit feedback:', error);
      toast.error('Failed to submit feedback');
    }
  };

  if (!tierInfo) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!tierInfo.features.grapple) {
    const features = [
      { icon: Mic, label: 'Voice Logging', desc: 'Describe your session and let AI extract the data' },
      { icon: BookOpen, label: 'Technique Q&A', desc: 'Ask about any technique and get sourced answers' },
      { icon: MessageCircle, label: 'AI Coaching', desc: 'Chat with a coach that knows your training history' },
      { icon: Brain, label: 'Smart Insights', desc: 'Weekly pattern analysis and focus recommendations' },
    ];
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6">
        <div className="text-center">
          <Sparkles className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--accent)' }} />
          <h2 className="text-2xl font-bold mb-1" style={{ color: 'var(--text)' }}>Grapple AI Coach</h2>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>Your personal BJJ training advisor, powered by AI</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {features.map((f) => (
            <div
              key={f.label}
              className="rounded-[14px] p-4 space-y-2"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <f.icon className="w-6 h-6" style={{ color: 'var(--accent)' }} />
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{f.label}</h3>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>{f.desc}</p>
            </div>
          ))}
        </div>
        <div className="text-center space-y-1">
          <p className="text-xs" style={{ color: 'var(--muted)' }}>Current tier: {tierInfo.tier}</p>
          <p className="text-sm font-medium" style={{ color: 'var(--muted)' }}>Upgrade to Premium to unlock Grapple</p>
        </div>
      </div>
    );
  }

  const quickActions = [
    { id: 'chat' as ActivePanel, label: 'Chat', icon: MessageCircle },
    { id: 'extract' as ActivePanel, label: 'Log Session', icon: Zap },
    { id: 'technique-qa' as ActivePanel, label: 'Ask Technique', icon: BookOpen },
    { id: 'insights' as ActivePanel, label: 'Insights', icon: Brain },
  ];

  return (
    <div className="h-[calc(100dvh-8rem)] md:h-[calc(100dvh-8rem)] flex flex-col md:flex-row gap-4">
      {/* Mobile sidebar backdrop */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Sessions */}
      <div className={`w-64 ${mobileSidebarOpen ? 'flex fixed inset-y-0 left-0 z-50 mt-16' : 'hidden'} md:flex md:static md:z-auto flex-col rounded-[14px] p-4 shrink-0`} style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold" style={{ color: 'var(--text)' }}>Chats</h2>
          <button
            onClick={newChat}
            className="text-sm px-3 py-1 rounded-lg text-white"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="flex items-center justify-between p-2 rounded-lg cursor-pointer group"
              style={{
                backgroundColor: currentSessionId === session.id ? 'var(--surfaceElev)' : 'transparent',
              }}
              onClick={() => { setCurrentSessionId(session.id); setActivePanel('chat'); setMobileSidebarOpen(false); }}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
                  {session.title}
                </div>
                <div className="text-xs" style={{ color: 'var(--muted)' }}>
                  {session.message_count} messages
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setDeleteSessionConfirmId(session.id); }}
                className="md:opacity-0 md:group-hover:opacity-100 p-1 rounded"
              >
                <Trash2 className="w-4 h-4" style={{ color: 'var(--error)' }} />
              </button>
            </div>
          ))}
        </div>

        {tierInfo.is_beta && (
          <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="text-xs" style={{ color: 'var(--muted)' }}>
              <span className="inline-block px-2 py-1 rounded font-medium" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                BETA
              </span>
              <p className="mt-2">
                {rateLimit
                  ? `${rateLimit.remaining}/${rateLimit.limit} messages left`
                  : `${tierInfo.limits.grapple_messages_per_hour} messages/hour`}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <button
            className="md:hidden p-2 rounded-lg"
            style={{ color: 'var(--muted)' }}
            onClick={() => setMobileSidebarOpen(prev => !prev)}
            title="Chat history"
          >
            {mobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <Sparkles className="w-8 h-8" style={{ color: 'var(--accent)' }} />
          <div className="flex-1">
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Grapple AI Coach</h1>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Your BJJ training advisor</p>
          </div>
          <Link
            to="/coach-settings"
            className="p-2 rounded-lg transition-colors hover:opacity-80"
            style={{ color: 'var(--muted)' }}
            title="Coach Settings"
          >
            <Settings className="w-5 h-5" />
          </Link>
        </div>

        {/* Quick Action Chips */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={() => setActivePanel(action.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all"
              style={{
                backgroundColor: activePanel === action.id ? 'var(--accent)' : 'var(--surface)',
                color: activePanel === action.id ? '#fff' : 'var(--text)',
                border: `1px solid ${activePanel === action.id ? 'var(--accent)' : 'var(--border)'}`,
              }}
            >
              <action.icon className="w-3.5 h-3.5" />
              {action.label}
            </button>
          ))}
        </div>

        {/* Panel Content */}
        {activePanel === 'extract' ? (
          <div className="flex-1 overflow-y-auto rounded-[14px] p-4" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <SessionExtractionPanel />
          </div>
        ) : activePanel === 'insights' ? (
          <div className="flex-1 overflow-y-auto rounded-[14px] p-4" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <InsightsPanel />
          </div>
        ) : activePanel === 'technique-qa' ? (
          <div className="flex-1 overflow-y-auto rounded-[14px] p-4" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <TechniqueQAPanel />
          </div>
        ) : (
          <>
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto rounded-[14px] p-4 space-y-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
              {messages.length === 0 && (
                <div className="text-center py-12" style={{ color: 'var(--muted)' }}>
                  <MessageCircle className="w-16 h-16 mx-auto mb-4 opacity-20" />
                  <p className="text-lg font-medium mb-2">Start a conversation</p>
                  <p className="text-sm mb-4">Ask about techniques, training advice, recovery...</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {[
                      'What should I focus on this week?',
                      'How do I improve my guard retention?',
                      'Analyse my recent training',
                      'Help me build a comp game plan',
                    ].map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => setInput(prompt)}
                        className="text-xs px-3 py-1.5 rounded-full transition-colors"
                        style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className="flex flex-col max-w-[80%]">
                    <div
                      className="rounded-lg px-4 py-3"
                      style={{
                        backgroundColor: msg.role === 'user' ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: msg.role === 'user' ? '#fff' : 'var(--text)',
                      }}
                    >
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    </div>
                    {msg.role === 'assistant' && !msg.id.startsWith('temp-') && !msg.id.startsWith('error-') && (
                      <div className="flex gap-2 mt-1 ml-2">
                        <button onClick={() => submitFeedback(msg.id, 'positive')} className="hover:opacity-80" style={{ color: 'var(--muted)' }} title="Helpful">
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button onClick={() => submitFeedback(msg.id, 'negative')} className="hover:opacity-80" style={{ color: 'var(--muted)' }} title="Not helpful">
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-lg px-4 py-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                    <div className="flex items-center gap-2">
                      <div className="animate-bounce">💭</div>
                      <div className="text-sm" style={{ color: 'var(--muted)' }}>Grapple is thinking...</div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="flex gap-2 mt-4 pb-16 md:pb-0">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                placeholder="Ask about techniques, training, recovery..."
                disabled={loading}
                className="flex-1 px-4 py-3 rounded-lg border text-sm disabled:opacity-50"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
              />
              {hasSpeechApi && (
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={isTranscribing || loading}
                  className="px-3 py-3 rounded-lg transition-all"
                  style={{
                    backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
                    color: isRecording ? '#FFFFFF' : 'var(--muted)',
                    opacity: isTranscribing ? 0.6 : 1,
                  }}
                  aria-label={isTranscribing ? 'Transcribing...' : isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {isTranscribing ? (
                    <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : isRecording ? (
                    <MicOff className="w-5 h-5" />
                  ) : (
                    <Mic className="w-5 h-5" />
                  )}
                </button>
              )}
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="px-6 py-3 rounded-lg text-white font-medium flex items-center gap-2 disabled:opacity-50"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                <Send className="w-5 h-5" />
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
          </>
        )}
      </div>

      <ConfirmDialog
        isOpen={deleteSessionConfirmId !== null}
        onClose={() => setDeleteSessionConfirmId(null)}
        onConfirm={() => deleteSessionConfirmId && deleteSession(deleteSessionConfirmId)}
        title="Delete Chat Session"
        message="Are you sure? All messages will be lost."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}
