import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface ReadinessData {
  check_date: string;
  sleep: number;
  stress: number;
  soreness: number;
  energy: number;
  hotspot_note: string;
  weight_kg: string;
}

interface CompactReadinessProps {
  data: ReadinessData;
  onChange: (data: ReadinessData) => void;
  compositeScore: number;
  onSkip: () => void;
  alreadyLogged: boolean;
}

const SLIDER_LABELS: Record<string, [string, string]> = {
  sleep: ['Poor', 'Great'],
  stress: ['Low', 'High'],
  soreness: ['None', 'Severe'],
  energy: ['Low', 'High'],
};

export default function CompactReadiness({
  data,
  onChange,
  compositeScore,
  onSkip,
  alreadyLogged,
}: CompactReadinessProps) {
  const [editing, setEditing] = useState(false);
  const [showExtras, setShowExtras] = useState(false);

  if (alreadyLogged && !editing) {
    return (
      <div className="flex items-center justify-between text-sm rounded-lg px-3 py-2" style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: '#16a34a' }}>
        <span>Readiness: {compositeScore}/20</span>
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="font-medium underline"
          style={{ color: 'var(--accent)' }}
        >
          Edit
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        {(['sleep', 'stress', 'soreness', 'energy'] as const).map((metric) => (
          <div key={metric}>
            <div className="flex justify-between text-xs mb-0.5">
              <span className="capitalize text-[var(--muted)]">{metric}</span>
              <span className="font-semibold">{data[metric]}/5</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={data[metric]}
              onChange={(e) => onChange({ ...data, [metric]: parseInt(e.target.value) })}
              className="w-full h-1.5 bg-[var(--surfaceElev)] rounded-lg appearance-none cursor-pointer"
              aria-label={metric}
            />
            <div className="flex justify-between text-[10px] text-[var(--muted)] -mt-0.5">
              <span>{SLIDER_LABELS[metric][0]}</span>
              <span>{SLIDER_LABELS[metric][1]}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="text-[var(--muted)]">
          Score: <span className="font-bold text-[var(--accent)]">{compositeScore}/20</span>
        </span>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowExtras(!showExtras)}
            className="text-xs text-[var(--muted)] hover:text-[var(--text)] flex items-center gap-0.5"
          >
            {data.hotspot_note || data.weight_kg ? 'Hotspot/Weight' : 'Hotspot? Weight?'}
            {showExtras ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {!alreadyLogged && (
            <button
              type="button"
              onClick={onSkip}
              className="text-xs text-[var(--muted)] hover:opacity-80 underline"
            >
              Skip
            </button>
          )}
        </div>
      </div>

      {showExtras && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-[var(--muted)]">Hotspot</label>
            <input
              type="text"
              className="input text-sm"
              value={data.hotspot_note}
              onChange={(e) => onChange({ ...data, hotspot_note: e.target.value })}
              placeholder="e.g., left shoulder"
            />
          </div>
          <div>
            <label className="text-xs text-[var(--muted)]">Weight (kg)</label>
            <input
              type="number"
              inputMode="decimal"
              className="input text-sm"
              value={data.weight_kg}
              onChange={(e) => onChange({ ...data, weight_kg: e.target.value })}
              placeholder="e.g., 75.5"
              step="0.1"
              min="30"
              max="300"
            />
          </div>
        </div>
      )}
    </div>
  );
}
