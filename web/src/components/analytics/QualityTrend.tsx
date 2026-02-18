import { formatClassType } from '../../constants/activity';
import { formatCount } from '../../utils/text';

interface ScoredSession {
  session_id: number;
  date: string;
  quality: number;
  breakdown: {
    intensity: number;
    submissions: number;
    techniques: number;
    volume: number;
  };
  class_type: string;
  gym: string;
}

interface WeeklyTrend {
  week: string;
  avg_quality: number;
  sessions: number;
}

interface QualityTrendProps {
  sessions: ScoredSession[];
  avgQuality: number;
  topSessions: ScoredSession[];
  weeklyTrend: WeeklyTrend[];
  insight: string;
}

export default function QualityTrend({ avgQuality, topSessions, weeklyTrend, insight }: QualityTrendProps) {
  if (!weeklyTrend || weeklyTrend.length === 0) {
    return (
      <p className="text-sm py-4" style={{ color: 'var(--muted)' }}>
        No session quality data yet.
      </p>
    );
  }

  const maxQ = Math.max(100, ...weeklyTrend.map(w => w.avg_quality));
  const barWidth = Math.max(20, Math.min(40, 500 / weeklyTrend.length));

  return (
    <div>
      {/* Avg Quality Badge */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className="text-2xl font-bold px-4 py-2 rounded-[14px]"
          style={{
            color: avgQuality >= 70 ? '#22C55E' : avgQuality >= 40 ? '#EAB308' : 'var(--text)',
            backgroundColor: 'var(--surfaceElev)',
            border: '1px solid var(--border)',
          }}
        >
          {avgQuality}
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>Avg Session Quality</p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>out of 100</p>
        </div>
      </div>

      {/* Weekly Bar Chart */}
      <div className="overflow-x-auto">
        <div className="flex items-end gap-1" style={{ height: '120px', minWidth: 'max-content' }}>
          {weeklyTrend.map((w, i) => {
            const barH = (w.avg_quality / maxQ) * 100;
            const color = w.avg_quality >= 70 ? 'var(--accent)' : w.avg_quality >= 40 ? '#EAB308' : 'var(--border)';
            return (
              <div key={i} className="flex flex-col items-center" style={{ width: `${barWidth}px` }}>
                <div
                  className="w-full rounded-t-md transition-all"
                  style={{ height: `${barH}%`, backgroundColor: color, minHeight: '4px' }}
                  title={`${w.week}: ${w.avg_quality}/100 (${formatCount(w.sessions, 'session')})`}
                />
              </div>
            );
          })}
        </div>
        <div className="flex gap-1 mt-1">
          {weeklyTrend.map((w, i) => (
            <div key={i} className="text-center" style={{ width: `${barWidth}px` }}>
              <span className="text-[9px]" style={{ color: 'var(--muted)' }}>
                {w.week.replace(/^\d{4}-/, '')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Sessions */}
      {topSessions && topSessions.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>Best Sessions</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {topSessions.map((s, i) => (
              <div
                key={s.session_id}
                className="p-3 rounded-lg"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold" style={{ color: 'var(--accent)' }}>#{i + 1}</span>
                  <span className="text-xs" style={{ color: 'var(--text)' }}>{s.date}</span>
                </div>
                <p className="text-lg font-bold" style={{ color: 'var(--text)' }}>{s.quality}/100</p>
                <p className="text-[10px]" style={{ color: 'var(--muted)' }}>{formatClassType(s.class_type)} @ {s.gym}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-sm mt-3" style={{ color: 'var(--muted)' }}>{insight}</p>
    </div>
  );
}
