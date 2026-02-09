interface StrainEfficiencyChartProps {
  overallEfficiency: number;
  byClassType: Record<string, number>;
  byGym: Record<string, number>;
  topSessions: { session_id: number; date: string; strain: number; submissions: number; efficiency: number }[];
}

export default function StrainEfficiencyChart({ overallEfficiency, byClassType, byGym, topSessions }: StrainEfficiencyChartProps) {
  const classEntries = Object.entries(byClassType).sort((a, b) => b[1] - a[1]);
  const gymEntries = Object.entries(byGym).sort((a, b) => b[1] - a[1]);

  if (classEntries.length === 0 && gymEntries.length === 0) return null;

  const maxEff = Math.max(
    ...classEntries.map(([, v]) => v),
    ...gymEntries.map(([, v]) => v),
    overallEfficiency,
    0.01,
  );

  return (
    <div className="space-y-4">
      {/* Overall */}
      <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <p className="text-xs text-[var(--muted)] mb-1">Overall Efficiency</p>
        <p className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>{overallEfficiency}</p>
        <p className="text-xs text-[var(--muted)]">subs / strain</p>
      </div>

      {/* By class type */}
      {classEntries.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>By Class Type</p>
          <div className="space-y-2">
            {classEntries.map(([ct, eff]) => (
              <div key={ct}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs capitalize" style={{ color: 'var(--text)' }}>{ct}</span>
                  <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>{eff}</span>
                </div>
                <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                  <div className="h-2 rounded-full" style={{ width: `${(eff / maxEff) * 100}%`, backgroundColor: 'var(--accent)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* By gym */}
      {gymEntries.length > 1 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>By Gym</p>
          <div className="space-y-2">
            {gymEntries.slice(0, 5).map(([gym, eff]) => (
              <div key={gym}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs" style={{ color: 'var(--text)' }}>{gym}</span>
                  <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>{eff}</span>
                </div>
                <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                  <div className="h-2 rounded-full" style={{ width: `${(eff / maxEff) * 100}%`, backgroundColor: '#8B5CF6' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top sessions */}
      {topSessions.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>Most Efficient Sessions</p>
          <div className="space-y-1">
            {topSessions.slice(0, 3).map(s => (
              <div key={s.session_id} className="flex items-center justify-between text-xs p-2 rounded" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                <span style={{ color: 'var(--text)' }}>{new Date(s.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                <span style={{ color: 'var(--muted)' }}>{s.submissions} subs / {s.strain} strain = {s.efficiency}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
