import { useState, useCallback } from 'react';
import { useToast } from '../../contexts/ToastContext';
import { grappleApi, getErrorMessage } from '../../api/client';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { Mic, MicOff } from 'lucide-react';

export default function TechniqueQAPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<{ answer: string; sources: { id: number; name: string; category?: string }[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const onTranscript = useCallback((transcript: string) => {
    setQuestion(prev => prev ? `${prev} ${transcript}` : transcript);
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
  }, [toast]);
  const { isRecording: qaRecording, isTranscribing: qaTranscribing, hasSpeechApi: qaHasSpeech, toggleRecording: qaToggle } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

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
          {qaHasSpeech && (
            <button
              type="button"
              onClick={qaToggle}
              disabled={qaTranscribing}
              className="p-2 rounded-lg transition-all"
              style={{
                backgroundColor: qaRecording ? 'var(--error)' : 'var(--surfaceElev)',
                color: qaRecording ? '#FFFFFF' : 'var(--muted)',
                opacity: qaTranscribing ? 0.6 : 1,
              }}
              aria-label={qaTranscribing ? 'Transcribing...' : qaRecording ? 'Stop recording' : 'Voice input'}
            >
              {qaTranscribing ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : qaRecording ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </button>
          )}
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
