import { useState, useCallback } from 'react';
import { MessageCircle, Send, Mic, MicOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Chat() {
  const { user: _user } = useAuth();
  const toast = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const onTranscript = useCallback((transcript: string) => {
    setInput(prev => prev ? `${prev} ${transcript}` : transcript);
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
  }, [toast]);
  const { isRecording, isTranscribing, hasSpeechApi, toggleRecording } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const apiBase = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.post(
        `${apiBase}/chat/`,
        { messages: newMessages },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages([...newMessages, { role: 'assistant', content: response.data.reply }]);
    } catch (error: any) {
      console.error('Chat error:', error);
      setMessages([
        ...newMessages,
        { role: 'assistant', content: 'Error: ' + (error.response?.data?.detail || 'Failed to get response') },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center gap-3 mb-4">
        <MessageCircle className="w-8 h-8" />
        <h1 className="text-3xl font-bold text-[var(--text)]">Chat</h1>
      </div>

      <div className="flex-1 overflow-y-auto bg-[var(--surface)] rounded-lg border border-[var(--border)] p-4 mb-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-[var(--muted)] py-12">
            Ask me anything about your training!
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--surfaceElev)] text-[var(--text)]'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[var(--surfaceElev)] rounded-lg px-4 py-2">
              <div className="text-sm text-[var(--muted)]">Thinking...</div>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={loading}
          className="flex-1 px-4 py-2 border border-[var(--border)] rounded-lg bg-[var(--surface)] text-[var(--text)] placeholder-[var(--muted)] disabled:opacity-50"
        />
        {hasSpeechApi && (
          <button
            type="button"
            onClick={toggleRecording}
            disabled={isTranscribing || loading}
            className="px-3 py-2 rounded-lg transition-all"
            style={{
              backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
              color: isRecording ? '#FFFFFF' : 'var(--muted)',
              opacity: isTranscribing ? 0.6 : 1,
            }}
            aria-label={isTranscribing ? 'Transcribing...' : isRecording ? 'Stop recording' : 'Voice input'}
          >
            {isTranscribing ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>
        )}
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="px-4 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          Send
        </button>
      </div>
    </div>
  );
}
