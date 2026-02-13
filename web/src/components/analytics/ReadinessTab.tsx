import { useState, useEffect } from 'react';
import { Activity, Heart, Waves, FlaskConical } from 'lucide-react';
import { analyticsApi } from '../../api/client';
import { Card, MetricTile, MetricTileSkeleton, CardSkeleton, EmptyState } from '../ui';
import ReadinessTrendChart from './ReadinessTrendChart';
import RecoveryPerformanceChart from './RecoveryPerformanceChart';
import StrainEfficiencyChart from './StrainEfficiencyChart';
import HRVPredictorChart from './HRVPredictorChart';
import SleepImpactChart from './SleepImpactChart';
import CardiovascularDriftChart from './CardiovascularDriftChart';

interface ReadinessTabProps {
  dateRange: { start: string; end: string };
  selectedTypes: string[];
}

interface ReadinessData {
  trends?: Array<{
    check_date?: string;
    date?: string;
    composite_score?: number;
    [key: string]: unknown;
  }>;
  summary?: {
    avg_composite_score?: number;
    best_day?: string;
    worst_day?: string;
    days_logged?: number;
    [key: string]: unknown;
  };
  component_averages?: {
    sleep?: number;
    stress?: number;
    soreness?: number;
    energy?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface WhoopTrendEntry { date: string; [key: string]: any; }

interface ZoneDistEntry {
  date: string;
  total_mins: number;
  zone_1_pct: number;
  zone_2_pct: number;
  zone_3_pct: number;
  zone_4_pct: number;
  zone_5_pct: number;
  zone_1_mins: number;
  zone_2_mins: number;
  zone_3_mins: number;
  zone_4_mins: number;
  zone_5_mins: number;
}

interface ZoneAverages {
  zone_1_avg_pct?: number;
  zone_2_avg_pct?: number;
  zone_3_avg_pct?: number;
  zone_4_avg_pct?: number;
  zone_5_avg_pct?: number;
  workouts?: number;
}

interface WhoopTrendData {
  hrv_trend?: WhoopTrendEntry[];
  rhr_trend?: WhoopTrendEntry[];
  recovery_over_time?: Array<{ date: string; recovery_score: number | null; sleep_performance: number | null }>;
  sleep_breakdown?: Array<{ date: string; light_pct: number; sws_pct: number; rem_pct: number; awake_pct: number }>;
  zone_distribution?: ZoneDistEntry[];
  zone_averages?: ZoneAverages;
  summary?: {
    avg_hrv?: number;
    avg_rhr?: number;
    avg_recovery?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface PerfScienceCorrelation {
  recovery_correlation?: {
    scatter?: Array<{ date: string; recovery_score: number; sub_rate: number }>;
    zones?: Record<string, { avg_sub_rate: number; sessions: number }>;
    r_value?: number;
    insight?: string;
    [key: string]: unknown;
  };
  hrv_predictor?: {
    scatter?: Array<{ date: string; hrv_ms: number; quality: number }>;
    r_value?: number;
    hrv_threshold?: number;
    quality_above?: number;
    quality_below?: number;
    insight?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface PerfScienceEfficiency {
  strain_efficiency?: {
    overall_efficiency?: number;
    by_class_type?: Record<string, number>;
    by_gym?: Record<string, number>;
    top_sessions?: Array<{ session_id: number; date: string; strain: number; submissions: number; efficiency: number }>;
    insight?: string;
    [key: string]: unknown;
  };
  sleep_analysis?: {
    rem_r?: number;
    sws_r?: number;
    total_sleep_r?: number;
    optimal_rem_pct?: number;
    optimal_sws_pct?: number;
    insight?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface PerfScienceCardiovascular {
  weekly_rhr?: Array<{ week: string; avg_rhr: number; data_points: number }>;
  slope?: number;
  trend?: string;
  current_rhr?: number | null;
  baseline_rhr?: number | null;
  insight?: string;
  [key: string]: unknown;
}

interface PerfScienceData {
  correlation: PerfScienceCorrelation | null;
  efficiency: PerfScienceEfficiency | null;
  cardiovascular: PerfScienceCardiovascular | null;
}

export default function ReadinessTab({ dateRange, selectedTypes }: ReadinessTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ReadinessData | null>(null);
  const [whoopData, setWhoopData] = useState<WhoopTrendData | null>(null);
  const [perfScience, setPerfScience] = useState<PerfScienceData | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!dateRange.start || !dateRange.end) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          start_date: dateRange.start,
          end_date: dateRange.end,
          types: selectedTypes.length > 0 ? selectedTypes : undefined,
        };
        const [readinessRes, whoopRes] = await Promise.allSettled([
          analyticsApi.readinessTrends(params),
          analyticsApi.whoopAnalytics(params),
        ]);
        if (!cancelled) {
          if (readinessRes.status === 'fulfilled') setData(readinessRes.value.data ?? null);
          if (whoopRes.status === 'fulfilled') setWhoopData(whoopRes.value.data ?? null);

          // Load performance science data (non-blocking)
          Promise.allSettled([
            analyticsApi.whoopPerformanceCorrelation(),
            analyticsApi.whoopEfficiency(),
            analyticsApi.whoopCardiovascular(),
          ]).then(([corrRes, effRes, cardioRes]) => {
            if (!cancelled) {
              setPerfScience({
                correlation: corrRes.status === 'fulfilled' ? corrRes.value.data : null,
                efficiency: effRes.status === 'fulfilled' ? effRes.value.data : null,
                cardiovascular: cardioRes.status === 'fulfilled' ? cardioRes.value.data : null,
              });
            }
          });
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Error loading readiness trends:', err);
          setError('Failed to load readiness data. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [dateRange, selectedTypes]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
        </div>
        <CardSkeleton lines={4} />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <EmptyState
          icon={Activity}
          title="Error Loading Data"
          description={error}
        />
      </Card>
    );
  }

  const trends = data?.trends || [];
  const summary = data?.summary || {};
  const componentAverages = data?.component_averages || {};

  // Transform trend data for chart
  const chartData = trends.map((t: any) => ({
    date: t.check_date || t.date,
    score: t.composite_score ?? 0,
  }));

  const avgScore = summary.avg_composite_score != null
    ? Number(summary.avg_composite_score).toFixed(1)
    : '0';
  const bestDay = summary.best_day ?? '-';
  const worstDay = summary.worst_day ?? '-';
  const daysLogged = summary.days_logged ?? trends.length;

  return (
    <div className="space-y-6">
      {/* Readiness data or empty state */}
      {trends.length === 0 ? (
        <Card>
          <EmptyState
            icon={Activity}
            title="No Readiness Data"
            description="Start logging your daily readiness checks to see trends, averages, and insights about your recovery."
            actionLabel="Check In Now"
            actionPath="/readiness"
          />
        </Card>
      ) : (
        <>
          {/* Metric tiles */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <MetricTile label="Avg Score" value={avgScore} chipLabel="/20" />
            <MetricTile label="Days Logged" value={daysLogged} chipLabel="Total" />
            <MetricTile label="Best Day" value={bestDay} chipLabel="Score" />
            <MetricTile label="Worst Day" value={worstDay} chipLabel="Score" />
          </div>

          {/* Trend chart */}
          <Card>
            <div className="mb-4">
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Readiness Trend</h3>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                Green zone (16-20) = Ready to train hard, Yellow (12-15) = Light session, Red (&lt;12) = Rest
              </p>
            </div>
            <ReadinessTrendChart data={chartData} />
          </Card>

          {/* Component averages */}
          {(componentAverages.sleep != null || componentAverages.stress != null) && (
            <Card>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text)' }}>Component Breakdown</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: 'Sleep', value: componentAverages.sleep, max: 5, good: 'higher' },
                  { label: 'Stress', value: componentAverages.stress, max: 5, good: 'lower' },
                  { label: 'Soreness', value: componentAverages.soreness, max: 5, good: 'lower' },
                  { label: 'Energy', value: componentAverages.energy, max: 5, good: 'higher' },
                ].map((comp) => (
                  <div key={comp.label} className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                      {comp.label}
                    </p>
                    <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                      {comp.value != null ? Number(comp.value).toFixed(1) : '-'}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--muted)' }}>/ {comp.max}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {/* WHOOP Trends */}
      {whoopData && ((whoopData.hrv_trend?.length ?? 0) > 0 || (whoopData.recovery_over_time?.length ?? 0) > 0) && (
        <>
          {/* WHOOP Summary Tiles */}
          {whoopData.summary && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {whoopData.summary.avg_hrv != null && (
                <MetricTile label="Avg HRV" value={Number(whoopData.summary.avg_hrv).toFixed(0)} chipLabel="ms" />
              )}
              {whoopData.summary.avg_rhr != null && (
                <MetricTile label="Avg RHR" value={Number(whoopData.summary.avg_rhr).toFixed(0)} chipLabel="bpm" />
              )}
              {whoopData.summary.avg_recovery != null && (
                <MetricTile label="Avg Recovery" value={Number(whoopData.summary.avg_recovery).toFixed(0)} chipLabel="%" />
              )}
            </div>
          )}

          {/* HRV Trend */}
          {whoopData.hrv_trend && whoopData.hrv_trend.length > 0 && (
            <Card>
              <div className="mb-4">
                <div className="flex items-center gap-2">
                  <Waves className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>HRV Trend</h3>
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Heart rate variability (ms) with 7-day moving average</p>
              </div>
              <WhoopLineChart
                data={whoopData.hrv_trend}
                valueKey="hrv_ms"
                avgKey="7day_avg"
                color="#8B5CF6"
                avgColor="#C4B5FD"
                unit="ms"
              />
            </Card>
          )}

          {/* RHR Trend */}
          {whoopData.rhr_trend && whoopData.rhr_trend.length > 0 && (
            <Card>
              <div className="mb-4">
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4" style={{ color: '#EF4444' }} />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Resting Heart Rate</h3>
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>RHR (bpm) with 7-day moving average</p>
              </div>
              <WhoopLineChart
                data={whoopData.rhr_trend!}
                valueKey="resting_hr"
                avgKey="7day_avg"
                color="#EF4444"
                avgColor="#FCA5A5"
                unit="bpm"
              />
            </Card>
          )}

          {/* Recovery Score Trend */}
          {whoopData.recovery_over_time && whoopData.recovery_over_time.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Recovery Score</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                  Daily WHOOP recovery percentage — Green (&ge;67%), Yellow (34-66%), Red (&lt;34%)
                </p>
              </div>
              <RecoveryBarChart data={whoopData.recovery_over_time} />
            </Card>
          )}

          {/* Sleep Composition */}
          {whoopData.sleep_breakdown && whoopData.sleep_breakdown.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Sleep Composition</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Sleep stage breakdown over time</p>
              </div>
              <SleepStackedChart data={whoopData.sleep_breakdown} />
            </Card>
          )}

          {/* Heart Rate Zone Distribution */}
          {whoopData.zone_distribution && whoopData.zone_distribution.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Heart Rate Zones</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Time spent in each HR zone per workout</p>
              </div>
              {/* Zone averages summary */}
              {whoopData.zone_averages && whoopData.zone_averages.workouts && (
                <div className="grid grid-cols-5 gap-2 mb-4">
                  {[
                    { label: 'Zone 1', key: 'zone_1_avg_pct' as const, color: '#9CA3AF' },
                    { label: 'Zone 2', key: 'zone_2_avg_pct' as const, color: '#3B82F6' },
                    { label: 'Zone 3', key: 'zone_3_avg_pct' as const, color: '#10B981' },
                    { label: 'Zone 4', key: 'zone_4_avg_pct' as const, color: '#F59E0B' },
                    { label: 'Zone 5', key: 'zone_5_avg_pct' as const, color: '#EF4444' },
                  ].map(z => (
                    <div key={z.label} className="text-center">
                      <div className="w-full h-2 rounded-full mb-1" style={{ backgroundColor: `${z.color}30` }}>
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${whoopData.zone_averages![z.key] ?? 0}%`, backgroundColor: z.color }}
                        />
                      </div>
                      <p className="text-[10px] font-medium" style={{ color: z.color }}>{z.label}</p>
                      <p className="text-xs font-semibold" style={{ color: 'var(--text)' }}>
                        {whoopData.zone_averages![z.key] != null ? `${whoopData.zone_averages![z.key]}%` : '-'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              <ZoneDistChart data={whoopData.zone_distribution} />
            </Card>
          )}
        </>
      )}

      {/* Performance Science Section */}
      {perfScience && (perfScience.correlation || perfScience.efficiency || perfScience.cardiovascular) && (
        <>
          <div className="pt-2">
            <div className="flex items-center gap-2 mb-1">
              <FlaskConical className="w-5 h-5" style={{ color: 'var(--accent)' }} />
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Performance Science</h3>
            </div>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>WHOOP biometrics correlated with your BJJ performance</p>
          </div>

          {/* Recovery × Performance */}
          {perfScience.correlation?.recovery_correlation?.scatter && perfScience.correlation.recovery_correlation.scatter.length > 0 && (
            <Card>
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>Recovery × Performance</h3>
              <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>How does your WHOOP recovery score predict rolling performance?</p>
              <RecoveryPerformanceChart
                scatter={perfScience.correlation.recovery_correlation.scatter}
                zones={perfScience.correlation.recovery_correlation.zones!}
                rValue={perfScience.correlation.recovery_correlation.r_value!}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{perfScience.correlation.recovery_correlation.insight}</p>
            </Card>
          )}

          {/* HRV Predictor */}
          {perfScience.correlation?.hrv_predictor?.scatter && perfScience.correlation.hrv_predictor.scatter.length > 0 && (
            <Card>
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>HRV Performance Predictor</h3>
              <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Your personal HRV threshold for optimal training quality</p>
              <HRVPredictorChart
                scatter={perfScience.correlation.hrv_predictor.scatter}
                rValue={perfScience.correlation.hrv_predictor.r_value!}
                hrvThreshold={perfScience.correlation.hrv_predictor.hrv_threshold!}
                qualityAbove={perfScience.correlation.hrv_predictor.quality_above!}
                qualityBelow={perfScience.correlation.hrv_predictor.quality_below!}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{perfScience.correlation.hrv_predictor.insight}</p>
            </Card>
          )}

          {/* Strain Efficiency */}
          {(perfScience.efficiency?.strain_efficiency?.overall_efficiency ?? 0) > 0 && (
            <Card>
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>Strain Efficiency</h3>
              <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Submissions per unit of WHOOP strain</p>
              <StrainEfficiencyChart
                overallEfficiency={perfScience.efficiency!.strain_efficiency!.overall_efficiency!}
                byClassType={perfScience.efficiency!.strain_efficiency!.by_class_type!}
                byGym={perfScience.efficiency!.strain_efficiency!.by_gym!}
                topSessions={perfScience.efficiency!.strain_efficiency!.top_sessions!}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{perfScience.efficiency!.strain_efficiency!.insight}</p>
            </Card>
          )}

          {/* Sleep Impact */}
          {perfScience.efficiency?.sleep_analysis && (
            perfScience.efficiency.sleep_analysis.rem_r !== 0 ||
            perfScience.efficiency.sleep_analysis.sws_r !== 0 ||
            perfScience.efficiency.sleep_analysis.total_sleep_r !== 0
          ) && (
            <Card>
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>Sleep Impact</h3>
              <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Which sleep stages matter most for your performance?</p>
              <SleepImpactChart
                remR={perfScience.efficiency!.sleep_analysis!.rem_r!}
                swsR={perfScience.efficiency!.sleep_analysis!.sws_r!}
                totalSleepR={perfScience.efficiency!.sleep_analysis!.total_sleep_r!}
                optimalRemPct={perfScience.efficiency!.sleep_analysis!.optimal_rem_pct!}
                optimalSwsPct={perfScience.efficiency!.sleep_analysis!.optimal_sws_pct!}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{perfScience.efficiency!.sleep_analysis!.insight}</p>
            </Card>
          )}

          {/* Cardiovascular Drift */}
          {perfScience.cardiovascular?.weekly_rhr && perfScience.cardiovascular.weekly_rhr.length >= 2 && (
            <Card>
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text)' }}>Cardiovascular Drift</h3>
              <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Resting heart rate trend — a key fitness and fatigue indicator</p>
              <CardiovascularDriftChart
                weeklyRhr={perfScience.cardiovascular.weekly_rhr}
                slope={perfScience.cardiovascular.slope!}
                trend={perfScience.cardiovascular.trend!}
                currentRhr={perfScience.cardiovascular.current_rhr ?? null}
                baselineRhr={perfScience.cardiovascular.baseline_rhr ?? null}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{perfScience.cardiovascular.insight}</p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

/* ---- WHOOP Chart Components ---- */

function WhoopLineChart({ data, valueKey, avgKey, color, avgColor, unit }: {
  data: { date: string; [key: string]: any }[];
  valueKey: string;
  avgKey: string;
  color: string;
  avgColor: string;
  unit: string;
}) {
  if (data.length === 0) return null;

  const width = 600;
  const height = 180;
  const pad = { top: 15, right: 20, bottom: 30, left: 45 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const values = data.map((d) => d[valueKey]).filter((v: any) => v != null) as number[];
  if (values.length === 0) return null;

  const minV = Math.floor(Math.min(...values) * 0.9);
  const maxV = Math.ceil(Math.max(...values) * 1.1);
  const range = maxV - minV || 1;

  const xScale = (i: number) => pad.left + (i / Math.max(data.length - 1, 1)) * plotW;
  const yScale = (v: number) => pad.top + plotH - ((v - minV) / range) * plotH;

  const buildPath = (key: string) =>
    data
      .map((d, i) => (d[key] != null ? `${i === 0 || data[i - 1]?.[key] == null ? 'M' : 'L'} ${xScale(i)} ${yScale(d[key])}` : ''))
      .filter(Boolean)
      .join(' ');

  const labelIndices = data.length <= 3
    ? data.map((_, i) => i)
    : [0, Math.floor(data.length / 2), data.length - 1];

  const gridValues = (() => {
    const step = Math.max(Math.round(range / 4), 1);
    const vals: number[] = [];
    for (let v = minV; v <= maxV; v += step) vals.push(v);
    return vals;
  })();

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 180 }}>
      {gridValues.map((v) => (
        <g key={v}>
          <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
          <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}</text>
        </g>
      ))}
      {/* 7-day avg line */}
      <path d={buildPath(avgKey)} fill="none" stroke={avgColor} strokeWidth={2} strokeDasharray="4 3" />
      {/* Main line */}
      <path d={buildPath(valueKey)} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      {/* Points */}
      {data.map((d, i) =>
        d[valueKey] != null ? (
          <circle key={i} cx={xScale(i)} cy={yScale(d[valueKey])} r={2.5} fill={color}>
            <title>{d.date}: {Number(d[valueKey]).toFixed(0)} {unit}</title>
          </circle>
        ) : null
      )}
      {/* X labels */}
      {labelIndices.map((i) => (
        <text key={i} x={xScale(i)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
          {new Date(data[i].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </text>
      ))}
    </svg>
  );
}

function RecoveryBarChart({ data }: { data: { date: string; recovery_score: number | null; sleep_performance: number | null }[] }) {
  if (data.length === 0) return null;

  const width = 600;
  const height = 180;
  const pad = { top: 15, right: 20, bottom: 30, left: 45 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const barW = Math.max(2, Math.min(12, plotW / data.length - 2));

  const yScale = (v: number) => pad.top + plotH - (v / 100) * plotH;

  const getBarColor = (score: number | null) => {
    if (score == null) return 'var(--border)';
    if (score >= 67) return '#10B981';
    if (score >= 34) return '#F59E0B';
    return '#EF4444';
  };

  const labelIndices = data.length <= 5
    ? data.map((_, i) => i)
    : [0, Math.floor(data.length / 4), Math.floor(data.length / 2), Math.floor(data.length * 3 / 4), data.length - 1];

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 180 }}>
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={v}>
          <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
          <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}%</text>
        </g>
      ))}
      {/* Zone bands */}
      <rect x={pad.left} y={yScale(100)} width={plotW} height={yScale(67) - yScale(100)} fill="rgba(16, 185, 129, 0.06)" />
      <rect x={pad.left} y={yScale(67)} width={plotW} height={yScale(34) - yScale(67)} fill="rgba(245, 158, 11, 0.06)" />
      <rect x={pad.left} y={yScale(34)} width={plotW} height={yScale(0) - yScale(34)} fill="rgba(239, 68, 68, 0.06)" />
      {/* Bars */}
      {data.map((d, i) => {
        const x = pad.left + (i / Math.max(data.length - 1, 1)) * plotW - barW / 2;
        const score = d.recovery_score ?? 0;
        return (
          <rect
            key={i}
            x={x}
            y={yScale(score)}
            width={barW}
            height={Math.max(0, yScale(0) - yScale(score))}
            fill={getBarColor(d.recovery_score)}
            rx={1}
          >
            <title>{d.date}: {d.recovery_score != null ? Math.round(d.recovery_score) + '%' : 'N/A'}</title>
          </rect>
        );
      })}
      {/* X labels */}
      {labelIndices.map((i) => (
        <text key={i} x={pad.left + (i / Math.max(data.length - 1, 1)) * plotW} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
          {new Date(data[i].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </text>
      ))}
    </svg>
  );
}

function SleepStackedChart({ data }: { data: { date: string; light_pct: number; sws_pct: number; rem_pct: number; awake_pct: number }[] }) {
  if (data.length === 0) return null;

  const width = 600;
  const height = 180;
  const pad = { top: 15, right: 20, bottom: 30, left: 45 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const barW = Math.max(2, Math.min(12, plotW / data.length - 2));

  const stages = [
    { key: 'rem_pct' as const, color: '#8B5CF6', label: 'REM' },
    { key: 'sws_pct' as const, color: '#3B82F6', label: 'Deep' },
    { key: 'light_pct' as const, color: '#60A5FA', label: 'Light' },
    { key: 'awake_pct' as const, color: '#D1D5DB', label: 'Awake' },
  ];

  const yScale = (v: number) => pad.top + plotH - (v / 100) * plotH;

  const labelIndices = data.length <= 5
    ? data.map((_, i) => i)
    : [0, Math.floor(data.length / 2), data.length - 1];

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 180 }}>
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={v}>
          <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
          <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}%</text>
        </g>
      ))}
      {/* Stacked bars */}
      {data.map((d, i) => {
        const x = pad.left + (i / Math.max(data.length - 1, 1)) * plotW - barW / 2;
        let cumY = 0;
        return (
          <g key={i}>
            {stages.map((stage) => {
              const pct = d[stage.key] ?? 0;
              const y0 = cumY;
              cumY += pct;
              return (
                <rect
                  key={stage.key}
                  x={x}
                  y={yScale(cumY)}
                  width={barW}
                  height={Math.max(0, yScale(y0) - yScale(cumY))}
                  fill={stage.color}
                  rx={0}
                >
                  <title>{d.date}: {stage.label} {pct.toFixed(0)}%</title>
                </rect>
              );
            })}
          </g>
        );
      })}
      {/* X labels */}
      {labelIndices.map((i) => (
        <text key={i} x={pad.left + (i / Math.max(data.length - 1, 1)) * plotW} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
          {new Date(data[i].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </text>
      ))}
      {/* Legend */}
      {stages.map((stage, i) => (
        <g key={stage.key} transform={`translate(${pad.left + i * 70}, ${pad.top - 10})`}>
          <rect width={8} height={8} fill={stage.color} rx={1} />
          <text x={12} y={8} fontSize={9} fill="var(--muted)">{stage.label}</text>
        </g>
      ))}
    </svg>
  );
}

function ZoneDistChart({ data }: { data: ZoneDistEntry[] }) {
  if (data.length === 0) return null;

  const width = 600;
  const height = 180;
  const pad = { top: 15, right: 20, bottom: 30, left: 45 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const barW = Math.max(2, Math.min(12, plotW / data.length - 2));

  const zones = [
    { key: 'zone_5_pct' as const, color: '#EF4444', label: 'Z5' },
    { key: 'zone_4_pct' as const, color: '#F59E0B', label: 'Z4' },
    { key: 'zone_3_pct' as const, color: '#10B981', label: 'Z3' },
    { key: 'zone_2_pct' as const, color: '#3B82F6', label: 'Z2' },
    { key: 'zone_1_pct' as const, color: '#9CA3AF', label: 'Z1' },
  ];

  const yScale = (v: number) => pad.top + plotH - (v / 100) * plotH;

  const labelIndices = data.length <= 5
    ? data.map((_, i) => i)
    : [0, Math.floor(data.length / 2), data.length - 1];

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 180 }}>
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={v}>
          <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
          <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}%</text>
        </g>
      ))}
      {data.map((d, i) => {
        const x = pad.left + (i / Math.max(data.length - 1, 1)) * plotW - barW / 2;
        let cumY = 0;
        return (
          <g key={i}>
            {zones.map((zone) => {
              const pct = d[zone.key] ?? 0;
              const y0 = cumY;
              cumY += pct;
              return (
                <rect
                  key={zone.key}
                  x={x}
                  y={yScale(cumY)}
                  width={barW}
                  height={Math.max(0, yScale(y0) - yScale(cumY))}
                  fill={zone.color}
                  rx={0}
                >
                  <title>{d.date}: {zone.label} {pct.toFixed(0)}%</title>
                </rect>
              );
            })}
          </g>
        );
      })}
      {labelIndices.map((i) => (
        <text key={i} x={pad.left + (i / Math.max(data.length - 1, 1)) * plotW} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
          {new Date(data[i].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </text>
      ))}
      {zones.map((zone, i) => (
        <g key={zone.key} transform={`translate(${pad.left + i * 50}, ${pad.top - 10})`}>
          <rect width={8} height={8} fill={zone.color} rx={1} />
          <text x={12} y={8} fontSize={9} fill="var(--muted)">{zone.label}</text>
        </g>
      ))}
    </svg>
  );
}
