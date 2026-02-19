/** Full score breakdown card for session detail page. */
import { useState } from 'react';
import { RefreshCw, Info } from 'lucide-react';
import type { SessionScoreBreakdown } from '../../types';

interface Props {
  score: number | null | undefined;
  breakdown: SessionScoreBreakdown | null | undefined;
  onRecalculate?: () => void;
  recalculating?: boolean;
}

const TIER_COLORS: [number, string][] = [
  [85, 'var(--accent)'],
  [70, '#F59E0B'],
  [50, '#10B981'],
  [30, '#3B82F6'],
  [0, 'var(--muted)'],
];

function tierColor(score: number): string {
  for (const [threshold, color] of TIER_COLORS) {
    if (score >= threshold) return color;
  }
  return 'var(--muted)';
}

const PILLAR_LABELS: Record<string, string> = {
  effort: 'Effort',
  engagement: 'Engagement',
  effectiveness: 'Effectiveness',
  readiness_alignment: 'Readiness Alignment',
  biometric_validation: 'Biometric Validation',
  consistency: 'Consistency',
};

export default function SessionScoreCard({ score, breakdown, onRecalculate, recalculating }: Props) {
  const [showInfo, setShowInfo] = useState(false);

  if (score == null || !breakdown) return null;

  const color = tierColor(score);
  const pillars = breakdown.pillars ?? {};

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-lg">Performance Score</h3>
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="p-0.5 rounded-full hover:opacity-80"
            style={{ color: 'var(--muted)' }}
            aria-label="Score explanation"
          >
            <Info className="w-4 h-4" />
          </button>
        </div>
        {onRecalculate && (
          <button
            onClick={onRecalculate}
            disabled={recalculating}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded border border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)] transition-colors disabled:opacity-40"
          >
            <RefreshCw className={`w-3 h-3 ${recalculating ? 'animate-spin' : ''}`} />
            Recalculate
          </button>
        )}
      </div>

      {/* Score info panel */}
      {showInfo && (
        <div className="text-xs mb-4 p-3 rounded-lg space-y-1" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}>
          <p><strong style={{ color: 'var(--text)' }}>Tiers:</strong> Peak (85+), Excellent (70–84), Strong (50–69), Solid (30–49), Light (&lt;30)</p>
          <p><strong style={{ color: 'var(--text)' }}>Pillars:</strong> Effort (duration + intensity), Engagement (rolls + partners), Effectiveness (subs + techniques), Readiness Alignment, Biometric Validation (WHOOP), Consistency (streak bonus)</p>
        </div>
      )}

      {/* Score gauge + label */}
      <div className="flex items-center gap-5 mb-5">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold shrink-0"
          style={{ border: `3px solid ${color}`, color }}
        >
          {Math.round(score)}
        </div>
        <div>
          <p className="text-lg font-semibold" style={{ color }}>{breakdown.label}</p>
          <p className="text-xs text-[var(--muted)]">
            {breakdown.rubric === 'bjj' ? 'BJJ' : breakdown.rubric === 'competition' ? 'Competition' : 'Supplementary'} rubric
            {breakdown.data_completeness < 1 && (
              <> &middot; {Math.round(breakdown.data_completeness * 100)}% data</>
            )}
          </p>
        </div>
      </div>

      {/* Pillar bars */}
      <div className="space-y-3">
        {Object.entries(pillars).map(([key, pillar]) => (
          <div key={key}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-[var(--text)]">{PILLAR_LABELS[key] ?? key}</span>
              <span className="text-[var(--muted)]">
                {pillar.score.toFixed(1)} / {pillar.max}
              </span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(100, pillar.pct)}%`,
                  backgroundColor: tierColor(pillar.pct),
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
