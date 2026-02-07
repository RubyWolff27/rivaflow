import { useState, useEffect, useCallback } from 'react';
import { Plus, X, CheckCircle } from 'lucide-react';

const TEMPLATES: Record<string, string[]> = {
  competition: ['Weight check', 'Gi / No-Gi gear ready', 'IBJJF card / registration', 'Game plan reviewed', 'Mouth guard', 'Tape / knee pads'],
  seminar: ['Gi ready', 'Notebook / phone for notes', 'Camera for recording', 'Water bottle'],
  grading: ['Gi washed and ironed', 'Belt ready', 'Know the syllabus requirements', 'Rest the day before'],
  camp: ['Multiple gis / rashguards', 'Recovery gear', 'Accommodation sorted', 'Travel booked'],
  other: ['Gear packed', 'Registration confirmed'],
};

interface PrepChecklistProps {
  eventId: number;
  eventType: string;
}

interface CheckItem {
  text: string;
  checked: boolean;
}

export default function PrepChecklist({ eventId, eventType }: PrepChecklistProps) {
  const storageKey = `prep-checklist-${eventId}`;

  const [items, setItems] = useState<CheckItem[]>(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) return JSON.parse(stored);
    } catch { /* use template */ }
    const template = TEMPLATES[eventType] || TEMPLATES.other;
    return template.map(text => ({ text, checked: false }));
  });

  const [newItemText, setNewItemText] = useState('');

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(items));
    } catch { /* noop */ }
  }, [items, storageKey]);

  const toggleItem = useCallback((index: number) => {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, checked: !item.checked } : item));
  }, []);

  const addItem = useCallback(() => {
    const text = newItemText.trim();
    if (!text) return;
    setItems(prev => [...prev, { text, checked: false }]);
    setNewItemText('');
  }, [newItemText]);

  const removeItem = useCallback((index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  }, []);

  const completedCount = items.filter(i => i.checked).length;
  const totalCount = items.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
          Prep Checklist
        </p>
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          {completedCount}/{totalCount}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full rounded-full h-1.5 mb-3" style={{ backgroundColor: 'var(--border)' }}>
        <div
          className="h-1.5 rounded-full transition-all"
          style={{
            width: `${progress}%`,
            backgroundColor: progress === 100 ? 'var(--success)' : 'var(--accent)',
          }}
        />
      </div>

      {/* Items */}
      <div className="space-y-1">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-2 group">
            <button
              onClick={() => toggleItem(index)}
              className="p-0.5 shrink-0"
              aria-label={item.checked ? `Uncheck "${item.text}"` : `Check "${item.text}"`}
            >
              <CheckCircle
                className="w-4 h-4"
                style={{ color: item.checked ? 'var(--success)' : 'var(--border)' }}
              />
            </button>
            <span
              className="text-xs flex-1"
              style={{
                color: item.checked ? 'var(--muted)' : 'var(--text)',
                textDecoration: item.checked ? 'line-through' : 'none',
              }}
            >
              {item.text}
            </span>
            <button
              onClick={() => removeItem(index)}
              className="p-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              aria-label={`Remove "${item.text}"`}
              style={{ color: 'var(--muted)' }}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Add custom item */}
      <div className="flex items-center gap-2 mt-2">
        <input
          type="text"
          value={newItemText}
          onChange={(e) => setNewItemText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addItem()}
          className="flex-1 px-2 py-1 rounded text-xs"
          style={{
            backgroundColor: 'var(--surfaceElev)',
            color: 'var(--text)',
            border: '1px solid var(--border)',
          }}
          placeholder="Add custom item..."
        />
        <button
          onClick={addItem}
          disabled={!newItemText.trim()}
          className="p-1 rounded transition-colors disabled:opacity-30"
          style={{ color: 'var(--accent)' }}
          aria-label="Add item"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
