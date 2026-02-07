import { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Trash2, MessageCircle, AlertCircle, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';
import axios from 'axios';

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

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const [tierRes, sessionsRes] = await Promise.all([
          axios.get(`${getApiBase()}/grapple/info`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          axios.get(`${getApiBase()}/grapple/sessions`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
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
        const token = localStorage.getItem('access_token');
        const response = await axios.get(`${getApiBase()}/grapple/sessions/${currentSessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
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

  const getApiBase = () => import.meta.env.VITE_API_URL || '/api/v1';

  const loadSessions = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${getApiBase()}/grapple/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
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
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${getApiBase()}/grapple/chat`,
        {
          message: userMessage.content,
          session_id: currentSessionId,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

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

      // Update current session
      if (!currentSessionId) {
        setCurrentSessionId(response.data.session_id);
        loadSessions(); // Refresh sessions list
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
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${getApiBase()}/grapple/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

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
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${getApiBase()}/admin/grapple/feedback`,
        {
          message_id: messageId,
          rating: rating,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
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
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8">
          <AlertCircle className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2 text-[var(--text)]">
            Grapple AI Coach
          </h2>
          <p className="text-[var(--muted)] mb-4">
            Get personalized BJJ coaching powered by AI. Upgrade to Premium to unlock Grapple.
          </p>
          <p className="text-sm text-[var(--muted)]">
            Current tier: {tierInfo.tier}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4">
      {/* Sidebar - Sessions */}
      <div className="w-64 bg-[var(--surface)] rounded-lg border border-[var(--border)] p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-[var(--text)]">Chats</h2>
          <button
            onClick={newChat}
            className="text-sm px-3 py-1 bg-[var(--accent)] text-white rounded hover:opacity-90"
          >
            New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`flex items-center justify-between p-2 rounded cursor-pointer group ${
                currentSessionId === session.id
                  ? 'bg-primary-50 dark:bg-primary-900/20'
                  : 'hover:bg-[var(--surfaceElev)]'
              }`}
              onClick={() => setCurrentSessionId(session.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate text-[var(--text)]">
                  {session.title}
                </div>
                <div className="text-xs text-[var(--muted)]">
                  {session.message_count} messages
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteSessionConfirmId(session.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded"
              >
                <Trash2 className="w-4 h-4 text-red-600" />
              </button>
            </div>
          ))}
        </div>

        {tierInfo.is_beta && (
          <div className="mt-4 pt-4 border-t border-[var(--border)]">
            <div className="text-xs text-[var(--muted)]">
              <span className="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 rounded font-medium">
                BETA
              </span>
              <p className="mt-2">
                {rateLimit
                  ? `${rateLimit.remaining}/${rateLimit.limit} messages left this hour`
                  : `${tierInfo.limits.grapple_messages_per_hour} messages per hour`}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="w-8 h-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">Grapple AI Coach</h1>
            <p className="text-sm text-[var(--muted)]">
              Your personalized BJJ training advisor
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-[var(--surface)] rounded-lg border border-[var(--border)] p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-[var(--muted)] py-12">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg font-medium mb-2">Start a conversation with Grapple</p>
              <p className="text-sm">
                Ask about techniques, training advice, recovery, or anything BJJ-related!
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="flex flex-col max-w-[80%]">
                <div
                  className={`rounded-lg px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-[var(--accent)] text-white'
                      : 'bg-[var(--surfaceElev)] text-[var(--text)]'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                </div>

                {msg.role === 'assistant' && !msg.id.startsWith('temp-') && !msg.id.startsWith('error-') && (
                  <div className="flex gap-2 mt-1 ml-2">
                    <button
                      onClick={() => submitFeedback(msg.id, 'positive')}
                      className="text-[var(--muted)] hover:text-green-600"
                      title="Helpful"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => submitFeedback(msg.id, 'negative')}
                      className="text-[var(--muted)] hover:text-red-600"
                      title="Not helpful"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-[var(--surfaceElev)] rounded-lg px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="animate-bounce">💭</div>
                  <div className="text-sm text-[var(--muted)]">Grapple is thinking...</div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2 mt-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask about techniques, training, recovery..."
            disabled={loading}
            className="flex-1 px-4 py-3 border border-[var(--border)] rounded-lg bg-[var(--surface)] text-[var(--text)] placeholder-[var(--muted)] disabled:opacity-50 focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 font-medium"
          >
            <Send className="w-5 h-5" />
            Send
          </button>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteSessionConfirmId !== null}
        onClose={() => setDeleteSessionConfirmId(null)}
        onConfirm={() => deleteSessionConfirmId && deleteSession(deleteSessionConfirmId)}
        title="Delete Chat Session"
        message="Are you sure you want to delete this chat session? All messages will be lost."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}
