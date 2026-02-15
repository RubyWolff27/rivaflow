import { ArrowRight } from 'lucide-react';

interface ReadinessData {
  check_date: string;
  sleep: number;
  stress: number;
  soreness: number;
  energy: number;
  hotspot_note: string;
  weight_kg: string;
}

interface ReadinessStepProps {
  data: ReadinessData;
  onChange: (data: ReadinessData) => void;
  compositeScore: number;
  onNext: () => void;
  onSkip: () => void;
}

export default function ReadinessStep({ data, onChange, compositeScore, onNext, onSkip }: ReadinessStepProps) {
  return (
    <div className="card space-y-6">
      <p className="text-[var(--muted)]">
        Let's check your readiness before logging today's session.
      </p>

      {(['sleep', 'stress', 'soreness', 'energy'] as const).map((metric) => (
        <div key={metric}>
          <label className="label capitalize flex justify-between">
            <span>{metric}</span>
            <span className="font-bold">{data[metric]}/5</span>
          </label>
          <input
            type="range"
            min="1"
            max="5"
            value={data[metric]}
            onChange={(e) => onChange({ ...data, [metric]: parseInt(e.target.value) })}
            className="w-full h-2 bg-[var(--surfaceElev)] rounded-lg appearance-none cursor-pointer"
            aria-label={metric}
            aria-valuetext={`${metric}: ${data[metric]} out of 5`}
          />
          <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
            <span>{metric === 'sleep' ? 'Poor' : metric === 'soreness' ? 'None' : 'Low'}</span>
            <span>{metric === 'sleep' ? 'Great' : metric === 'soreness' ? 'Severe' : 'High'}</span>
          </div>
        </div>
      ))}

      <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
        <p className="text-sm text-[var(--muted)] mb-1">Readiness Score</p>
        <p className="text-3xl font-bold text-[var(--accent)]">{compositeScore}/20</p>
      </div>

      <div>
        <label className="label">Any Injuries or Hotspots? (optional)</label>
        <input
          type="text"
          className="input"
          value={data.hotspot_note}
          onChange={(e) => onChange({ ...data, hotspot_note: e.target.value })}
          placeholder="e.g., left shoulder, right knee"
        />
      </div>

      <div>
        <label className="label">Weight (kg) (optional)</label>
        <input
          type="number"
          inputMode="decimal"
          className="input"
          value={data.weight_kg}
          onChange={(e) => onChange({ ...data, weight_kg: e.target.value })}
          placeholder="e.g., 75.5"
          step="0.1"
          min="30"
          max="300"
        />
      </div>

      <button onClick={onNext} className="btn-primary w-full flex items-center justify-center gap-2">
        Continue to Session Details
        <ArrowRight className="w-4 h-4" />
      </button>

      <div className="text-center mt-3">
        <button
          type="button"
          onClick={onSkip}
          className="text-xs text-[var(--muted)] hover:opacity-80 underline"
        >
          Skip readiness check
        </button>
      </div>
    </div>
  );
}
