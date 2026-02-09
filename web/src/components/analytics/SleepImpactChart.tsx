interface SleepImpactChartProps {
  remR: number;
  swsR: number;
  totalSleepR: number;
  optimalRemPct: number;
  optimalSwsPct: number;
}

export default function SleepImpactChart({ remR, swsR, totalSleepR, optimalRemPct, optimalSwsPct }: SleepImpactChartProps) {
  const correlations = [
    { label: 'Total Sleep', value: totalSleepR, color: '#60A5FA' },
    { label: 'REM Sleep', value: remR, color: '#8B5CF6' },
    { label: 'Deep Sleep (SWS)', value: swsR, color: '#3B82F6' },
  ];

  const maxR = Math.max(...correlations.map(c => Math.abs(c.value)), 0.01);

  return (
    <div className="space-y-4">
      {/* Correlation bars */}
      <div className="space-y-3">
        {correlations.map(c => {
          const isPositive = c.value >= 0;
          const barWidth = (Math.abs(c.value) / maxR) * 100;
          return (
            <div key={c.label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs" style={{ color: 'var(--text)' }}>{c.label}</span>
                <span className="text-xs font-medium" style={{
                  color: Math.abs(c.value) >= 0.3 ? c.color : 'var(--muted)',
                }}>
                  r = {c.value}
                </span>
              </div>
              <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${barWidth}%`,
                    backgroundColor: isPositive ? c.color : '#EF4444',
                    opacity: Math.abs(c.value) >= 0.2 ? 1 : 0.4,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Optimal targets */}
      <div className="grid grid-cols-2 gap-3">
        {optimalRemPct > 0 && (
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <p className="text-xs text-[var(--muted)] mb-1">Optimal REM</p>
            <p className="text-xl font-bold" style={{ color: '#8B5CF6' }}>{optimalRemPct}%</p>
          </div>
        )}
        {optimalSwsPct > 0 && (
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <p className="text-xs text-[var(--muted)] mb-1">Optimal Deep</p>
            <p className="text-xl font-bold" style={{ color: '#3B82F6' }}>{optimalSwsPct}%</p>
          </div>
        )}
      </div>

      <p className="text-xs" style={{ color: 'var(--muted)' }}>
        Correlation strength: |r| {'>'} 0.3 = strong, |r| {'>'} 0.2 = moderate, |r| {'<'} 0.2 = weak
      </p>
    </div>
  );
}
