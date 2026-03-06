import { useState } from 'react';
import { X, UserPlus } from 'lucide-react';
import { sessionsApi } from '../../api/training';
import { useToast } from '../../contexts/ToastContext';

interface TagPartnersModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: number;
  partnerNames: string[];
  /** Only partners who are RivaFlow friends can be tagged */
  taggablePartners: Array<{ id: number; name: string }>;
}

export default function TagPartnersModal({
  isOpen,
  onClose,
  sessionId,
  partnerNames,
  taggablePartners,
}: TagPartnersModalProps) {
  const toast = useToast();
  const [selected, setSelected] = useState<Set<number>>(
    new Set(taggablePartners.map((p) => p.id))
  );
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleTag = async () => {
    if (selected.size === 0) {
      onClose();
      return;
    }
    setLoading(true);
    try {
      await sessionsApi.tagPartners(sessionId, Array.from(selected));
      toast.success(`Tagged ${selected.size} partner${selected.size > 1 ? 's' : ''}`);
      onClose();
    } catch {
      toast.error('Failed to tag partners');
    } finally {
      setLoading(false);
    }
  };

  const untaggable = partnerNames.filter(
    (name) => !taggablePartners.some((p) => p.name === name)
  );

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div
        className="relative w-full max-w-md rounded-t-2xl sm:rounded-2xl p-5 space-y-4"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-[var(--accent)]" />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Tag Your Partners
            </h3>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-[var(--surfaceElev)]">
            <X className="w-5 h-5 text-[var(--muted)]" />
          </button>
        </div>

        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Your rolling partners will be notified that you trained together.
        </p>

        {taggablePartners.length > 0 && (
          <div className="space-y-2">
            {taggablePartners.map((partner) => (
              <label
                key={partner.id}
                className="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors"
                style={{
                  backgroundColor: selected.has(partner.id)
                    ? 'rgba(59,130,246,0.08)'
                    : 'var(--surfaceElev)',
                  border: `1px solid ${selected.has(partner.id) ? 'var(--accent)' : 'var(--border)'}`,
                }}
              >
                <input
                  type="checkbox"
                  checked={selected.has(partner.id)}
                  onChange={() => toggle(partner.id)}
                  className="w-4 h-4 accent-[var(--accent)]"
                />
                <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {partner.name}
                </span>
              </label>
            ))}
          </div>
        )}

        {untaggable.length > 0 && (
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {untaggable.join(', ')} {untaggable.length === 1 ? "isn't" : "aren't"} on
            RivaFlow yet — invite them to connect!
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
            style={{
              backgroundColor: 'var(--surfaceElev)',
              color: 'var(--text)',
              border: '1px solid var(--border)',
            }}
          >
            Skip
          </button>
          <button
            onClick={handleTag}
            disabled={loading || selected.size === 0}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
            style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
          >
            {loading ? 'Tagging...' : `Tag ${selected.size} Partner${selected.size !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
