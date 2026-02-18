import { Swords, Shield } from 'lucide-react';

interface HeatmapPeriod {
  period_start: string;
  period_end: string;
  period_label: string;
  attacks_attempted: number;
  attacks_successful: number;
  defenses_attempted: number;
  defenses_successful: number;
  session_count: number;
}

type ViewMode = 'weekly' | 'monthly';

interface DynamicsChartProps {
  heatmapData: HeatmapPeriod[];
  view: ViewMode;
}

function getSuccessRate(successful: number, attempted: number): number | null {
  if (attempted === 0) return null;
  return Math.round((successful / attempted) * 100);
}

export default function DynamicsChart({ heatmapData, view }: DynamicsChartProps) {
  const maxAttackVolume = Math.max(...heatmapData.map(p => p.attacks_attempted), 1);
  const maxDefenseVolume = Math.max(...heatmapData.map(p => p.defenses_attempted), 1);

  const getAttackOpacity = (attempted: number) => {
    if (attempted === 0) return 0.05;
    return 0.15 + (attempted / maxAttackVolume) * 0.85;
  };

  const getDefenseOpacity = (attempted: number) => {
    if (attempted === 0) return 0.05;
    return 0.15 + (attempted / maxDefenseVolume) * 0.85;
  };

  return (
    <div
      className="rounded-xl p-5"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>
        {view === 'weekly' ? 'Last 8 Weeks' : 'Last 6 Months'}
      </h2>

      {/* Period labels row */}
      <div className="flex gap-1.5 mb-2 ml-20">
        {heatmapData.map((period, i) => (
          <div
            key={i}
            className="flex-1 text-center"
          >
            <span className="text-[10px] leading-tight block" style={{ color: 'var(--muted)' }}>
              {view === 'weekly'
                ? period.period_label.split(' - ')[0]
                : period.period_label}
            </span>
          </div>
        ))}
      </div>

      {/* Attack row */}
      <div className="flex gap-1.5 mb-1.5 items-center">
        <div className="w-20 flex items-center gap-1.5 flex-shrink-0">
          <Swords className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--accent)' }}>Attack</span>
        </div>
        {heatmapData.map((period, i) => {
          const rate = getSuccessRate(period.attacks_successful, period.attacks_attempted);
          const opacity = getAttackOpacity(period.attacks_attempted);
          return (
            <div
              key={i}
              className="flex-1 rounded-lg flex flex-col items-center justify-center relative group cursor-default"
              style={{
                backgroundColor: period.attacks_attempted > 0
                  ? `rgba(255, 77, 45, ${opacity})`
                  : 'var(--surfaceElev)',
                minHeight: '56px',
                border: period.attacks_attempted > 0 ? '1px solid rgba(255, 77, 45, 0.3)' : '1px solid var(--border)',
              }}
            >
              {period.attacks_attempted > 0 ? (
                <>
                  <span className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                    {period.attacks_attempted}
                  </span>
                  <span className="text-[10px]" style={{ color: rate !== null && rate >= 50 ? '#4ade80' : rate !== null ? '#f87171' : 'var(--muted)' }}>
                    {rate !== null ? `${rate}%` : ''}
                  </span>
                </>
              ) : (
                <span className="text-[10px]" style={{ color: 'var(--muted)' }}>-</span>
              )}

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                <div
                  className="rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg"
                  style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)', color: 'var(--text)' }}
                >
                  <div className="font-medium mb-1">{period.period_label}</div>
                  <div>Attempted: {period.attacks_attempted}</div>
                  <div>Successful: {period.attacks_successful}</div>
                  {rate !== null && <div>Success rate: {rate}%</div>}
                  <div style={{ color: 'var(--muted)' }}>{period.session_count} session{period.session_count !== 1 ? 's' : ''}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Defence row */}
      <div className="flex gap-1.5 items-center">
        <div className="w-20 flex items-center gap-1.5 flex-shrink-0">
          <Shield className="w-4 h-4 text-blue-500" />
          <span className="text-xs font-medium text-blue-500">Defence</span>
        </div>
        {heatmapData.map((period, i) => {
          const rate = getSuccessRate(period.defenses_successful, period.defenses_attempted);
          const opacity = getDefenseOpacity(period.defenses_attempted);
          return (
            <div
              key={i}
              className="flex-1 rounded-lg flex flex-col items-center justify-center relative group cursor-default"
              style={{
                backgroundColor: period.defenses_attempted > 0
                  ? `rgba(59, 130, 246, ${opacity})`
                  : 'var(--surfaceElev)',
                minHeight: '56px',
                border: period.defenses_attempted > 0 ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid var(--border)',
              }}
            >
              {period.defenses_attempted > 0 ? (
                <>
                  <span className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                    {period.defenses_attempted}
                  </span>
                  <span className="text-[10px]" style={{ color: rate !== null && rate >= 50 ? '#4ade80' : rate !== null ? '#f87171' : 'var(--muted)' }}>
                    {rate !== null ? `${rate}%` : ''}
                  </span>
                </>
              ) : (
                <span className="text-[10px]" style={{ color: 'var(--muted)' }}>-</span>
              )}

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                <div
                  className="rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg"
                  style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)', color: 'var(--text)' }}
                >
                  <div className="font-medium mb-1">{period.period_label}</div>
                  <div>Attempted: {period.defenses_attempted}</div>
                  <div>Successful: {period.defenses_successful}</div>
                  {rate !== null && <div>Success rate: {rate}%</div>}
                  <div style={{ color: 'var(--muted)' }}>{period.session_count} session{period.session_count !== 1 ? 's' : ''}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2">
          <span className="text-[10px]" style={{ color: 'var(--muted)' }}>Low volume</span>
          <div className="flex gap-0.5">
            {[0.15, 0.35, 0.55, 0.75, 1].map((o, i) => (
              <div key={i} className="w-4 h-3 rounded-sm" style={{ backgroundColor: `rgba(255, 77, 45, ${o})` }} />
            ))}
          </div>
          <span className="text-[10px]" style={{ color: 'var(--muted)' }}>High volume</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-green-500">50%+ = good</span>
          <span className="text-[10px] text-red-400">&lt;50% = needs work</span>
        </div>
      </div>
    </div>
  );
}

export type { HeatmapPeriod, ViewMode };
