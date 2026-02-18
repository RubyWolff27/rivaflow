import { Swords, Shield, Target, TrendingUp, TrendingDown, Minus, Lightbulb, AlertTriangle } from 'lucide-react';

interface TrendData {
  volume_change: 'increasing' | 'decreasing' | 'stable';
  volume_change_pct: number;
  rate_direction: 'improving' | 'declining' | 'stable';
  rate_change_pct: number;
}

interface InsightsData {
  has_sufficient_data: boolean;
  message?: string;
  sessions_with_data?: number;
  sessions_needed?: number;
  recent_period?: {
    start: string;
    end: string;
    session_count: number;
    attacks_attempted: number;
    attacks_successful: number;
    defenses_attempted: number;
    defenses_successful: number;
  };
  previous_period?: {
    start: string;
    end: string;
    session_count: number;
    attacks_attempted: number;
    attacks_successful: number;
    defenses_attempted: number;
    defenses_successful: number;
  };
  offensive_trend?: TrendData;
  defensive_trend?: TrendData;
  attack_success_rate?: number;
  defense_success_rate?: number;
  imbalance_detection?: {
    detected: boolean;
    type: string;
    description: string;
    attack_ratio?: number;
    defense_ratio?: number;
  };
  suggested_focus?: {
    primary_focus: { area: string; priority: string; message: string } | null;
    all_suggestions: { area: string; priority: string; message: string }[];
  };
}

function TrendIcon({ trend }: { trend: TrendData }) {
  if (trend.volume_change === 'increasing') return <TrendingUp className="w-4 h-4 text-green-500" />;
  if (trend.volume_change === 'decreasing') return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Minus className="w-4 h-4" style={{ color: 'var(--muted)' }} />;
}

function RateIcon({ direction }: { direction: string }) {
  if (direction === 'improving') return <TrendingUp className="w-3.5 h-3.5 text-green-500" />;
  if (direction === 'declining') return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
  return <Minus className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />;
}

interface SummaryStatsProps {
  insights: InsightsData;
}

export function SummaryStats({ insights }: SummaryStatsProps) {
  if (!insights.has_sufficient_data || !insights.recent_period) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {/* Attack Rate */}
      <div
        className="rounded-xl p-4 text-center"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-center gap-1 mb-1">
          <Swords className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Attack Rate</span>
        </div>
        <div className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>
          {insights.attack_success_rate?.toFixed(1)}%
        </div>
        {insights.offensive_trend && (
          <div className="flex items-center justify-center gap-1 mt-1">
            <RateIcon direction={insights.offensive_trend.rate_direction} />
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {insights.offensive_trend.rate_change_pct > 0 ? '+' : ''}{insights.offensive_trend.rate_change_pct}%
            </span>
          </div>
        )}
      </div>

      {/* Defence Rate */}
      <div
        className="rounded-xl p-4 text-center"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-center gap-1 mb-1">
          <Shield className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Defence Rate</span>
        </div>
        <div className="text-2xl font-bold text-blue-500">
          {insights.defense_success_rate?.toFixed(1)}%
        </div>
        {insights.defensive_trend && (
          <div className="flex items-center justify-center gap-1 mt-1">
            <RateIcon direction={insights.defensive_trend.rate_direction} />
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {insights.defensive_trend.rate_change_pct > 0 ? '+' : ''}{insights.defensive_trend.rate_change_pct}%
            </span>
          </div>
        )}
      </div>

      {/* Attack Volume */}
      <div
        className="rounded-xl p-4 text-center"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-center gap-1 mb-1">
          <Target className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Attacks (4wk)</span>
        </div>
        <div className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
          {insights.recent_period.attacks_attempted}
        </div>
        {insights.offensive_trend && (
          <div className="flex items-center justify-center gap-1 mt-1">
            <TrendIcon trend={insights.offensive_trend} />
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {insights.offensive_trend.volume_change}
            </span>
          </div>
        )}
      </div>

      {/* Defence Volume */}
      <div
        className="rounded-xl p-4 text-center"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-center gap-1 mb-1">
          <Shield className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Defences (4wk)</span>
        </div>
        <div className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
          {insights.recent_period.defenses_attempted}
        </div>
        {insights.defensive_trend && (
          <div className="flex items-center justify-center gap-1 mt-1">
            <TrendIcon trend={insights.defensive_trend} />
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {insights.defensive_trend.volume_change}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

interface MatchupCardProps {
  insights: InsightsData;
}

export default function MatchupCard({ insights }: MatchupCardProps) {
  return (
    <div
      className="rounded-xl p-5"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5" style={{ color: 'var(--accent)' }} />
        <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Insights</h2>
      </div>

      {!insights.has_sufficient_data ? (
        <div className="text-center py-4">
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {insights.message}
          </p>
          <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
            Sessions with data: {insights.sessions_with_data ?? 0} / {insights.sessions_needed ?? 3}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Imbalance Detection */}
          {insights.imbalance_detection && (
            <div
              className="flex items-start gap-3 rounded-lg p-3"
              style={{
                backgroundColor: insights.imbalance_detection.detected
                  ? 'rgba(251, 191, 36, 0.1)'
                  : 'rgba(74, 222, 128, 0.1)',
                border: `1px solid ${insights.imbalance_detection.detected ? 'rgba(251, 191, 36, 0.3)' : 'rgba(74, 222, 128, 0.3)'}`,
              }}
            >
              {insights.imbalance_detection.detected ? (
                <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              ) : (
                <Target className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              )}
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {insights.imbalance_detection.detected ? 'Imbalance Detected' : 'Balanced Training'}
                </p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                  {insights.imbalance_detection.description}
                </p>
                {insights.imbalance_detection.attack_ratio != null && (
                  <div className="flex items-center gap-3 mt-2">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
                      <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                        Attack {insights.imbalance_detection.attack_ratio}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-blue-500" />
                      <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                        Defence {insights.imbalance_detection.defense_ratio}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Suggested Focus */}
          {insights.suggested_focus?.all_suggestions?.map((suggestion, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 rounded-lg p-3"
              style={{
                backgroundColor: suggestion.priority === 'high'
                  ? 'rgba(255, 77, 45, 0.08)'
                  : suggestion.priority === 'medium'
                  ? 'rgba(59, 130, 246, 0.08)'
                  : 'rgba(74, 222, 128, 0.08)',
                border: `1px solid ${
                  suggestion.priority === 'high'
                    ? 'rgba(255, 77, 45, 0.2)'
                    : suggestion.priority === 'medium'
                    ? 'rgba(59, 130, 246, 0.2)'
                    : 'rgba(74, 222, 128, 0.2)'
                }`,
              }}
            >
              <Lightbulb
                className="w-4 h-4 mt-0.5 flex-shrink-0"
                style={{
                  color: suggestion.priority === 'high'
                    ? 'var(--accent)'
                    : suggestion.priority === 'medium'
                    ? '#3b82f6'
                    : '#4ade80',
                }}
              />
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                    {suggestion.area.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </p>
                  <span
                    className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded"
                    style={{
                      backgroundColor: suggestion.priority === 'high'
                        ? 'rgba(255, 77, 45, 0.2)'
                        : suggestion.priority === 'medium'
                        ? 'rgba(59, 130, 246, 0.2)'
                        : 'rgba(74, 222, 128, 0.2)',
                      color: suggestion.priority === 'high'
                        ? 'var(--accent)'
                        : suggestion.priority === 'medium'
                        ? '#3b82f6'
                        : '#4ade80',
                    }}
                  >
                    {suggestion.priority}
                  </span>
                </div>
                <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                  {suggestion.message}
                </p>
              </div>
            </div>
          ))}

          {/* Period Comparison */}
          {insights.recent_period && insights.previous_period && (
            <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
              <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--muted)' }}>
                4-Week Comparison
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg p-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-[10px] font-medium mb-1" style={{ color: 'var(--muted)' }}>Recent (4 weeks)</p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span style={{ color: 'var(--accent)' }}>ATK</span>
                      <span style={{ color: 'var(--text)' }}>{insights.recent_period.attacks_successful}/{insights.recent_period.attacks_attempted}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-blue-500">DEF</span>
                      <span style={{ color: 'var(--text)' }}>{insights.recent_period.defenses_successful}/{insights.recent_period.defenses_attempted}</span>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg p-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-[10px] font-medium mb-1" style={{ color: 'var(--muted)' }}>Previous (4 weeks)</p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span style={{ color: 'var(--accent)' }}>ATK</span>
                      <span style={{ color: 'var(--text)' }}>{insights.previous_period.attacks_successful}/{insights.previous_period.attacks_attempted}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-blue-500">DEF</span>
                      <span style={{ color: 'var(--text)' }}>{insights.previous_period.defenses_successful}/{insights.previous_period.defenses_attempted}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export type { InsightsData, TrendData };
