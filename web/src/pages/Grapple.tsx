import { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Trash2, MessageCircle, AlertCircle, ThumbsUp, ThumbsDown, Zap, Brain, BookOpen } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { grappleApi, getErrorMessage } from '../api/client';
import ConfirmDialog from '../components/ConfirmDialog';
import type { AIInsight, ExtractedSession } from '../types';

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

function InsightCard({ insight }: { insight: AIInsight }) {
  const categoryColors: Record<string, string> = {
    observation: '#3B82F6',
    pattern: '#8B5CF6',
    focus: '#F59E0B',
    recovery: '#10B981',
  };
  const color = categoryColors[insight.category] || '#6B7280';

  return (
    <div
      className="p-4 rounded-[14px] space-y-2"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2">
        <span
          className="text-[10px] font-bold uppercase px-2 py-0.5 rounded"
          style={{ backgroundColor: color + '20', color }}
        >
          {insight.category}
        </span>
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          {insight.insight_type}
        </span>
      </div>
      <h4 className="font-semibold text-sm" style={{ color: 'var(--text)' }}>
        {insight.title}
      </h4>
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        {insight.content}
      </p>
    </div>
  );
}

function SessionExtractionPanel() {
  const [text, setText] = useState('');
  const [extracted, setExtracted] = useState<ExtractedSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const handleExtract = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const response = await grappleApi.extractSession(text);
      setExtracted(response.data);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!extracted) return;
    setSaving(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      await grappleApi.saveExtractedSession({
        session_date: extracted.session_date || today,
        class_type: extracted.class_type || 'gi',
        gym_name: extracted.gym_name || '',
        duration_mins: extracted.duration_mins || 60,
        intensity: extracted.intensity || 3,
        rolls: extracted.rolls || 0,
        submissions_for: extracted.submissions_for || 0,
        submissions_against: extracted.submissions_against || 0,
        partners: extracted.partners || [],
        techniques: extracted.techniques || [],
        notes: extracted.notes || '',
        events: extracted.events || [],
      });
      toast.success('Session saved!');
      setExtracted(null);
      setText('');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
          Describe your training session
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Did a gi class today at my gym. Worked on closed guard sweeps. Got 2 subs, got tapped once by armbar. Rolled with Mike and Sarah for 5 rounds..."
          rows={4}
          className="w-full px-4 py-3 rounded-[14px] border text-sm"
          style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
        />
        <button
          onClick={handleExtract}
          disabled={loading || !text.trim()}
          className="mt-2 px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          {loading ? 'Extracting...' : 'Extract Session Data'}
        </button>
      </div>

      {extracted && (
        <div
          className="p-4 rounded-[14px] space-y-3"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--accent)' }}
        >
          <h4 className="font-semibold text-sm" style={{ color: 'var(--text)' }}>
            Extracted Session Preview
          </h4>
          {extracted.parse_error && (
            <p className="text-xs" style={{ color: 'var(--error)' }}>
              Could not fully parse — please review and edit below.
            </p>
          )}
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span style={{ color: 'var(--muted)' }}>Date:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.session_date || 'Today'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Type:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.class_type || 'gi'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Duration:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.duration_mins || 60} min</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Intensity:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.intensity || 3}/5</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Rolls:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.rolls || 0}</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Subs:</span>{' '}
              <span style={{ color: 'var(--text)' }}>
                {extracted.submissions_for || 0} for / {extracted.submissions_against || 0} against
              </span>
            </div>
          </div>
          {extracted.partners && extracted.partners.length > 0 && (
            <div className="text-sm">
              <span style={{ color: 'var(--muted)' }}>Partners:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.partners.join(', ')}</span>
            </div>
          )}
          {extracted.techniques && extracted.techniques.length > 0 && (
            <div className="text-sm">
              <span style={{ color: 'var(--muted)' }}>Techniques:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.techniques.join(', ')}</span>
            </div>
          )}
          {extracted.notes && (
            <div className="text-sm">
              <span style={{ color: 'var(--muted)' }}>Notes:</span>{' '}
              <span style={{ color: 'var(--text)' }}>{extracted.notes}</span>
            </div>
          )}
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              {saving ? 'Saving...' : 'Confirm & Save'}
            </button>
            <button
              onClick={() => setExtracted(null)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ color: 'var(--muted)' }}
            >
              Discard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function InsightsPanel() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const toast = useToast();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await grappleApi.getInsights({ limit: 10 });
        if (!cancelled) setInsights(response.data.insights || []);
      } catch {
        // Insights not available
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const handleGenerateWeekly = async () => {
    setGenerating(true);
    try {
      const response = await grappleApi.generateInsight({ insight_type: 'weekly' });
      setInsights((prev) => [response.data, ...prev]);
      toast.success('Insight generated!');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div className="text-center py-4" style={{ color: 'var(--muted)' }}>Loading insights...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold" style={{ color: 'var(--text)' }}>AI Insights</h3>
        <button
          onClick={handleGenerateWeekly}
          disabled={generating}
          className="text-sm px-3 py-1.5 rounded-lg font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          {generating ? 'Generating...' : 'Generate Weekly'}
        </button>
      </div>
      {insights.length === 0 ? (
        <p className="text-sm text-center py-4" style={{ color: 'var(--muted)' }}>
          No insights yet. Train more and generate your first insight!
        </p>
      ) : (
        insights.map((insight) => <InsightCard key={insight.id} insight={insight} />)
      )}
    </div>
  );
}

function TechniqueQAPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<{ answer: string; sources: { id: number; name: string; category?: string }[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const response = await grappleApi.techniqueQA(question);
      setAnswer(response.data);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
          Ask about a technique
        </label>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How do I defend the armbar from closed guard?"
            className="flex-1 px-4 py-2 rounded-lg border text-sm"
            style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
          />
          <button
            onClick={handleAsk}
            disabled={loading || !question.trim()}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            {loading ? '...' : 'Ask'}
          </button>
        </div>
      </div>

      {answer && (
        <div
          className="p-4 rounded-[14px] space-y-3"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <p className="text-sm whitespace-pre-wrap" style={{ color: 'var(--text)' }}>
            {answer.answer}
          </p>
          {answer.sources.length > 0 && (
            <div>
              <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Sources:
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {answer.sources.map((s) => (
                  <span
                    key={s.id}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
                  >
                    {s.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Grapple() {
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
        if (!cancelled) console.error('Failed to load grapple data:', error);
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
          console.error('Failed to load session:', error);
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
      console.error('Failed to load sessions:', error);
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
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMsg = error.response?.data?.detail?.message || error.response?.data?.detail || 'Failed to get response';

      setMessages((prev) => [
        ...prev,
        { id: 'error-' + Date.now(), role: 'assistant', content: `Error: ${errorMsg}` },
      ]);

      if (error.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait before sending more messages.');
      } else if (error.response?.status === 403) {
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
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete session');
    }
  };

  const submitFeedback = async (messageId: string, rating: 'positive' | 'negative') => {
    try {
      await grappleApi.submitFeedback({ message_id: messageId, rating });
      toast.success('Thank you for your feedback!');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  if (!tierInfo) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!tierInfo.features.grapple) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="rounded-[14px] p-8" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <AlertCircle className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--accent)' }} />
          <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text)' }}>Grapple AI Coach</h2>
          <p className="mb-4" style={{ color: 'var(--muted)' }}>
            Get personalized BJJ coaching powered by AI. Upgrade to Premium to unlock Grapple.
          </p>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>Current tier: {tierInfo.tier}</p>
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
    <div className="h-[calc(100vh-8rem)] flex gap-4">
      {/* Sidebar - Sessions */}
      <div className="w-64 hidden md:flex flex-col rounded-[14px] p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
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
              onClick={() => { setCurrentSessionId(session.id); setActivePanel('chat'); }}
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
                className="opacity-0 group-hover:opacity-100 p-1 rounded"
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
          <Sparkles className="w-8 h-8" style={{ color: 'var(--accent)' }} />
          <div className="flex-1">
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Grapple AI Coach</h1>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Your BJJ training advisor</p>
          </div>
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
                  <p className="text-sm">Ask about techniques, training advice, recovery...</p>
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
            <div className="flex gap-2 mt-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="Ask about techniques, training, recovery..."
                disabled={loading}
                className="flex-1 px-4 py-3 rounded-lg border text-sm disabled:opacity-50"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="px-6 py-3 rounded-lg text-white font-medium flex items-center gap-2 disabled:opacity-50"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                <Send className="w-5 h-5" />
                Send
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
