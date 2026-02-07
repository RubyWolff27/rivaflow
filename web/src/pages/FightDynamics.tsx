import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/client';
import { Swords, Shield, TrendingUp, TrendingDown, Minus, AlertTriangle, Target, Lightbulb, BarChart3 } from 'lucide-react';

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

type ViewMode = 'weekly' | 'monthly';

export default function FightDynamics() {
  const [view, setView] = useState<ViewMode>('weekly');
  const [heatmapData, setHeatmapData] = useState<HeatmapPeriod[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [view]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [heatmapRes, insightsRes] = await Promise.all([
        analyticsApi.fightDynamicsHeatmap({ view }),
        analyticsApi.fightDynamicsInsights(),
      ]);
      setHeatmapData(heatmapRes.data ?? []);
      setInsights(insightsRes.data ?? null);
    } catch (err) {
      console.error('Error loading fight dynamics:', err);
      setError('Failed to load fight dynamics data.');
    } finally {
      setLoading(false);
    }
  };

  // Calculate max values for color intensity scaling
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

  const getSuccessRate = (successful: number, attempted: number) => {
    if (attempted === 0) return null;
    return Math.round((successful / attempted) * 100);
  };

  const hasAnyData = heatmapData.some(p => p.attacks_attempted > 0 || p.defenses_attempted > 0);

  const TrendIcon = ({ trend }: { trend: TrendData }) => {
    if (trend.volume_change === 'increasing') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend.volume_change === 'decreasing') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4" style={{ color: 'var(--muted)' }} />;
  };

  const RateIcon = ({ direction }: { direction: string }) => {
    if (direction === 'improving') return <TrendingUp className="w-3.5 h-3.5 text-green-500" />;
    if (direction === 'declining') return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
    return <Minus className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'var(--accent)', opacity: 0.9 }}>
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: 'var(--text)' }}>Fight Dynamics</h1>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Attack vs Defence heatmap</p>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }}>
          {(['weekly', 'monthly'] as ViewMode[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className="px-4 py-1.5 text-xs font-medium transition-colors"
              style={{
                backgroundColor: view === v ? 'var(--accent)' : 'var(--surface)',
                color: view === v ? '#FFFFFF' : 'var(--muted)',
              }}
            >
              {v === 'weekly' ? '8 Weeks' : '6 Months'}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-xl p-4 text-sm text-red-400" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {/* Skeleton heatmap */}
          <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="h-5 w-32 rounded mb-6" style={{ backgroundColor: 'var(--border)' }} />
            <div className="space-y-4">
              {[0, 1].map(row => (
                <div key={row} className="flex gap-2">
                  <div className="w-20 h-16 rounded" style={{ backgroundColor: 'var(--border)' }} />
                  {Array.from({ length: view === 'weekly' ? 8 : 6 }).map((_, i) => (
                    <div key={i} className="flex-1 h-16 rounded" style={{ backgroundColor: 'var(--border)' }} />
                  ))}
                </div>
              ))}
            </div>
          </div>
          {/* Skeleton insights */}
          <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="h-5 w-24 rounded mb-4" style={{ backgroundColor: 'var(--border)' }} />
            <div className="grid grid-cols-2 gap-4">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="h-20 rounded" style={{ backgroundColor: 'var(--border)' }} />
              ))}
            </div>
          </div>
        </div>
      ) : !hasAnyData ? (
        /* Empty state */
        <div
          className="rounded-xl p-8 text-center"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex justify-center gap-3 mb-4">
            <Swords className="w-8 h-8" style={{ color: 'var(--accent)' }} />
            <Shield className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
            No Fight Dynamics Data Yet
          </h2>
          <p className="text-sm max-w-md mx-auto" style={{ color: 'var(--muted)' }}>
            Start tracking your attacks and defences during sparring sessions.
            Open the "Fight Dynamics" section when logging a session to record your attack and defence counts.
          </p>
        </div>
      ) : (
        <>
          {/* Heatmap Card */}
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

          {/* Summary Stats */}
          {insights?.has_sufficient_data && insights.recent_period && (
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
          )}

          {/* Insights Panel */}
          {insights && (
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
          )}
        </>
      )}
    </div>
  );
}
