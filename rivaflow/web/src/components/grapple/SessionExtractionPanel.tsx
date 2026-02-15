import { useState, useCallback } from 'react';
import { getLocalDateString } from '../../utils/date';
import { useToast } from '../../contexts/ToastContext';
import { grappleApi, getErrorMessage } from '../../api/client';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { Mic, MicOff } from 'lucide-react';
import type { ExtractedSession } from '../../types';

const CLASS_TYPES = ['gi', 'no_gi', 'open_mat', 'drilling', 'competition', 'wrestling', 'judo', 'mma', 'sc', 'mobility'];

export default function SessionExtractionPanel() {
  const [text, setText] = useState('');
  const [extracted, setExtracted] = useState<ExtractedSession | null>(null);
  const [editData, setEditData] = useState<ExtractedSession>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const onTranscript = useCallback((transcript: string) => {
    setText(prev => prev ? `${prev} ${transcript}` : transcript);
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
  }, [toast]);
  const { isRecording, isTranscribing, hasSpeechApi, toggleRecording } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

  const handleExtract = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const response = await grappleApi.extractSession(text);
      setExtracted(response.data);
      setEditData({ ...response.data });
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
      const today = getLocalDateString();
      await grappleApi.saveExtractedSession({
        session_date: editData.session_date || today,
        class_type: editData.class_type || 'gi',
        gym_name: editData.gym_name || '',
        duration_mins: editData.duration_mins || 60,
        intensity: editData.intensity || 3,
        rolls: editData.rolls || 0,
        submissions_for: editData.submissions_for || 0,
        submissions_against: editData.submissions_against || 0,
        partners: editData.partners || [],
        techniques: editData.techniques || [],
        notes: editData.notes || '',
        events: editData.events || [],
      });
      toast.success('Session saved!');
      setExtracted(null);
      setEditData({});
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
        <div className="relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. Did a gi class today at my gym. Worked on closed guard sweeps. Got 2 subs, got tapped once by armbar. Rolled with Mike and Sarah for 5 rounds..."
            rows={4}
            className="w-full px-4 py-3 rounded-[14px] border text-sm"
            style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
          />
          {hasSpeechApi && (
            <button
              type="button"
              onClick={toggleRecording}
              disabled={isTranscribing}
              className="absolute bottom-2 right-2 p-1.5 rounded-lg transition-all"
              style={{
                backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
                color: isRecording ? '#FFFFFF' : 'var(--muted)',
                opacity: isTranscribing ? 0.6 : 1,
              }}
              aria-label={isTranscribing ? 'Transcribing audio...' : isRecording ? 'Stop recording' : 'Start voice input'}
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
        </div>
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
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Review and edit the extracted fields below before saving.
          </p>
          {extracted.parse_error && (
            <p className="text-xs" style={{ color: 'var(--error)' }}>
              Could not fully parse — please check the fields below.
            </p>
          )}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Date</label>
              <input
                type="date"
                value={editData.session_date || getLocalDateString()}
                onChange={(e) => setEditData({ ...editData, session_date: e.target.value })}
                className="w-full px-2 py-1.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              />
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Type</label>
              <select
                value={editData.class_type || 'gi'}
                onChange={(e) => setEditData({ ...editData, class_type: e.target.value })}
                className="w-full px-2 py-1.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              >
                {CLASS_TYPES.map((t) => (
                  <option key={t} value={t}>{t.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Duration (min)</label>
              <input
                type="number"
                min={0}
                value={editData.duration_mins ?? 60}
                onChange={(e) => setEditData({ ...editData, duration_mins: parseInt(e.target.value) || 0 })}
                className="w-full px-2 py-1.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              />
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Intensity ({editData.intensity ?? 3}/5)</label>
              <input
                type="range"
                min={1}
                max={5}
                value={editData.intensity ?? 3}
                onChange={(e) => setEditData({ ...editData, intensity: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Rolls</label>
              <input
                type="number"
                min={0}
                value={editData.rolls ?? 0}
                onChange={(e) => setEditData({ ...editData, rolls: parseInt(e.target.value) || 0 })}
                className="w-full px-2 py-1.5 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Subs for</label>
                <input
                  type="number"
                  min={0}
                  value={editData.submissions_for ?? 0}
                  onChange={(e) => setEditData({ ...editData, submissions_for: parseInt(e.target.value) || 0 })}
                  className="w-full px-2 py-1.5 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Against</label>
                <input
                  type="number"
                  min={0}
                  value={editData.submissions_against ?? 0}
                  onChange={(e) => setEditData({ ...editData, submissions_against: parseInt(e.target.value) || 0 })}
                  className="w-full px-2 py-1.5 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
                />
              </div>
            </div>
          </div>
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Gym</label>
            <input
              type="text"
              value={editData.gym_name || ''}
              onChange={(e) => setEditData({ ...editData, gym_name: e.target.value })}
              placeholder="Gym name"
              className="w-full px-2 py-1.5 rounded-lg border text-sm"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Partners (comma-separated)</label>
            <input
              type="text"
              value={(editData.partners || []).join(', ')}
              onChange={(e) => setEditData({ ...editData, partners: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })}
              placeholder="e.g., Mike, Sarah"
              className="w-full px-2 py-1.5 rounded-lg border text-sm"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Techniques (comma-separated)</label>
            <input
              type="text"
              value={(editData.techniques || []).join(', ')}
              onChange={(e) => setEditData({ ...editData, techniques: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })}
              placeholder="e.g., armbar, triangle"
              className="w-full px-2 py-1.5 rounded-lg border text-sm"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>Notes</label>
            <textarea
              value={editData.notes || ''}
              onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
              rows={2}
              className="w-full px-2 py-1.5 rounded-lg border text-sm"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            />
          </div>
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
              onClick={() => { setExtracted(null); setEditData({}); }}
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
