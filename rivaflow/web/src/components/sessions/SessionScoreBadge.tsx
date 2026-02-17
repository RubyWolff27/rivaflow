import { memo } from 'react';

/** Compact circular badge showing session score (0-100), color-coded by tier. */
interface Props {
  score: number | null | undefined;
  size?: 'sm' | 'md';
}

const TIER_COLORS: [number, string][] = [
  [85, 'var(--accent)'],    // Peak
  [70, '#F59E0B'],          // Excellent — amber
  [50, '#10B981'],          // Strong — green
  [30, '#3B82F6'],          // Solid — blue
  [0, 'var(--muted)'],      // Light — gray
];

function tierColor(score: number): string {
  for (const [threshold, color] of TIER_COLORS) {
    if (score >= threshold) return color;
  }
  return 'var(--muted)';
}

const SessionScoreBadge = memo(function SessionScoreBadge({ score, size = 'sm' }: Props) {
  if (score == null) return null;

  const color = tierColor(score);
  const dim = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm';

  return (
    <div
      className={`${dim} rounded-full flex items-center justify-center font-bold shrink-0`}
      style={{
        border: `2px solid ${color}`,
        color,
      }}
      title={`Session score: ${Math.round(score)}`}
    >
      {Math.round(score)}
    </div>
  );
});

export default SessionScoreBadge;
