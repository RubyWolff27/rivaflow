import { useState, useEffect } from 'react';
import { Brain, Activity, Battery, Star, Bed, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { analyticsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Card, CardSkeleton, EmptyState } from '../ui';
import ACWRChart from './ACWRChart';
import CorrelationScatter from './CorrelationScatter';
import TechniqueQuadrant from './TechniqueQuadrant';
import QualityTrend from './QualityTrend';
import RiskGauge from './RiskGauge';

interface InsightsTabProps {
  dateRange: { start: string; end: string };
}

interface InsightsSummary {
  acwr?: number;
  acwr_zone?: string;
  risk_score?: number;
  risk_level?: string;
  game_breadth?: number;
  avg_session_quality?: number;
  top_insight?: string;
  [key: string]: unknown;
}

interface ACWRPoint {
  date: string;
  acwr: number;
  zone: string;
  acute: number;
  chronic: number;
  daily_load: number;
}

interface TrainingLoadData {
  acwr_series?: ACWRPoint[];
  current_acwr?: number;
  current_zone?: string;
  insight?: string;
  [key: string]: unknown;
}

interface ReadinessCorrData {
  data_points?: number;
  scatter?: Array<{ date: string; readiness: number; sub_rate: number; intensity: number }>;
  r_value?: number;
  optimal_zone?: string;
  insight?: string;
  [key: string]: unknown;
}

interface InsightTechnique {
  id: number;
  name: string;
  category: string;
  submissions: number;
  training_count: number;
  quadrant: string;
}

interface TechniqueEffData {
  techniques?: InsightTechnique[];
  game_breadth?: number;
  money_moves?: InsightTechnique[];
  insight?: string;
  [key: string]: unknown;
}

interface InsightScoredSession {
  session_id: number;
  date: string;
  quality: number;
  breakdown: { intensity: number; submissions: number; techniques: number; volume: number };
  class_type: string;
  gym: string;
}

interface InsightWeeklyTrend {
  week: string;
  avg_quality: number;
  sessions: number;
}

interface SessionQualityData {
  sessions?: InsightScoredSession[];
  avg_quality?: number;
  top_sessions?: InsightScoredSession[];
  weekly_trend?: InsightWeeklyTrend[];
  insight?: string;
  [key: string]: unknown;
}

interface InsightFactor {
  score: number;
  max: number;
}

interface RiskData {
  risk_score?: number;
  level?: string;
  factors?: Record<string, InsightFactor>;
  recommendations?: string[];
  [key: string]: unknown;
}

interface RecoveryRestEntry {
  rest_days: number;
  avg_sub_rate: number;
  sessions: number;
}

interface RecoveryData {
  data_points?: number;
  sleep_correlation?: number;
  optimal_rest_days?: number;
  rest_analysis?: RecoveryRestEntry[];
  insight?: string;
  [key: string]: unknown;
}

interface CheckinTrendsData {
  energy_trend?: Array<{ date: string; value: number }>;
  quality_trend?: Array<{ date: string; value: number }>;
  rest_days?: number;
  training_days?: number;
  avg_energy?: number | null;
  avg_quality?: number | null;
  energy_slope?: number | null;
  quality_slope?: number | null;
}

export default function InsightsTab({ dateRange }: InsightsTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [trainingLoad, setTrainingLoad] = useState<TrainingLoadData | null>(null);
  const [readinessCorr, setReadinessCorr] = useState<ReadinessCorrData | null>(null);
  const [techniqueEff, setTechniqueEff] = useState<TechniqueEffData | null>(null);
  const [sessionQuality, setSessionQuality] = useState<SessionQualityData | null>(null);
  const [riskData, setRiskData] = useState<RiskData | null>(null);
  const [recoveryData, setRecoveryData] = useState<RecoveryData | null>(null);
  const [checkinTrends, setCheckinTrends] = useState<CheckinTrendsData | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = dateRange.start && dateRange.end
          ? { start_date: dateRange.start, end_date: dateRange.end }
          : undefined;

        const [summaryRes, loadRes, corrRes, techRes, qualRes, riskRes, recRes, checkinRes] = await Promise.all([
          analyticsApi.insightsSummary().catch(() => ({ data: null })),
          analyticsApi.trainingLoad().catch(() => ({ data: null })),
          analyticsApi.readinessCorrelation(params).catch(() => ({ data: null })),
          analyticsApi.techniqueEffectiveness(params).catch(() => ({ data: null })),
          analyticsApi.sessionQuality(params).catch(() => ({ data: null })),
          analyticsApi.overtTrainingRisk().catch(() => ({ data: null })),
          analyticsApi.recoveryInsights().catch(() => ({ data: null })),
          analyticsApi.checkinTrends({ days: 30 }).catch(() => ({ data: null })),
        ]);

        if (!cancelled) {
          setSummary(summaryRes.data);
          setTrainingLoad(loadRes.data);
          setReadinessCorr(corrRes.data);
          setTechniqueEff(techRes.data);
          setSessionQuality(qualRes.data);
          setRiskData(riskRes.data);
          setRecoveryData(recRes.data);
          setCheckinTrends(checkinRes.data);
        }
      } catch (err) {
        if (!cancelled) {
          logger.error('Error loading insights:', err);
          setError('Failed to load insights. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [dateRange]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
        </div>
        <CardSkeleton lines={4} />
        <CardSkeleton lines={4} />
        <CardSkeleton lines={4} />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <EmptyState icon={Activity} title="Error Loading Data" description={error} />
      </Card>
    );
  }

  if (!summary && !trainingLoad && !riskData) {
    return (
      <Card>
        <EmptyState
          icon={Brain}
          title="No Insights Available"
          description="Log more training sessions with readiness check-ins, techniques, and rolls to unlock deep insights."
          actionLabel="Log Session"
          actionPath="/log"
        />
      </Card>
    );
  }

  const zoneColors: Record<string, string> = {
    sweet_spot: '#22C55E',
    caution: '#EAB308',
    danger: '#EF4444',
    undertrained: '#3B82F6',
  };

  const riskColors: Record<string, string> = {
    green: '#22C55E',
    yellow: '#EAB308',
    red: '#EF4444',
  };

  return (
    <div className="space-y-6">
      {/* Summary Tiles */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>ACWR</p>
            <p className="text-2xl font-bold" style={{ color: (summary.acwr_zone && zoneColors[summary.acwr_zone]) || 'var(--text)' }}>
              {summary.acwr}
            </p>
            <p className="text-xs capitalize mt-1" style={{ color: 'var(--muted)' }}>{summary.acwr_zone?.replace('_', ' ')}</p>
          </div>

          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>Risk</p>
            <p className="text-2xl font-bold" style={{ color: (summary.risk_level && riskColors[summary.risk_level]) || 'var(--text)' }}>
              {summary.risk_score}
            </p>
            <p className="text-xs capitalize mt-1" style={{ color: 'var(--muted)' }}>{summary.risk_level}</p>
          </div>

          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>Game Breadth</p>
            <p className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>
              {summary.game_breadth}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>/ 100</p>
          </div>

          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>Quality</p>
            <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
              {summary.avg_session_quality}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>avg / 100</p>
          </div>
        </div>
      )}

      {/* Top Insight Banner */}
      {summary?.top_insight && (
        <div className="p-4 rounded-[14px] flex items-center gap-3" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--accent)' }}>
          <Brain className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--accent)' }} />
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{summary.top_insight}</p>
        </div>
      )}

      {/* Check-in Trends */}
      {checkinTrends && (checkinTrends.training_days ?? 0) + (checkinTrends.rest_days ?? 0) > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Check-in Pulse</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Battery className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
                <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Energy</p>
              </div>
              <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {checkinTrends.avg_energy != null ? checkinTrends.avg_energy.toFixed(1) : '—'}
              </p>
              <div className="flex items-center gap-1 mt-1">
                {checkinTrends.energy_slope != null && checkinTrends.energy_slope > 0.05 && <TrendingUp className="w-3 h-3 text-green-500" />}
                {checkinTrends.energy_slope != null && checkinTrends.energy_slope < -0.05 && <TrendingDown className="w-3 h-3 text-red-400" />}
                {checkinTrends.energy_slope != null && Math.abs(checkinTrends.energy_slope) <= 0.05 && <Minus className="w-3 h-3" style={{ color: 'var(--muted)' }} />}
                <p className="text-xs" style={{ color: 'var(--muted)' }}>/ 5</p>
              </div>
            </div>

            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Star className="w-3.5 h-3.5" style={{ color: '#EAB308' }} />
                <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Quality</p>
              </div>
              <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {checkinTrends.avg_quality != null ? checkinTrends.avg_quality.toFixed(1) : '—'}
              </p>
              <div className="flex items-center gap-1 mt-1">
                {checkinTrends.quality_slope != null && checkinTrends.quality_slope > 0.05 && <TrendingUp className="w-3 h-3 text-green-500" />}
                {checkinTrends.quality_slope != null && checkinTrends.quality_slope < -0.05 && <TrendingDown className="w-3 h-3 text-red-400" />}
                {checkinTrends.quality_slope != null && Math.abs(checkinTrends.quality_slope) <= 0.05 && <Minus className="w-3 h-3" style={{ color: 'var(--muted)' }} />}
                <p className="text-xs" style={{ color: 'var(--muted)' }}>/ 5</p>
              </div>
            </div>

            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Activity className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
                <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Training</p>
              </div>
              <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {checkinTrends.training_days ?? 0}
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>days (30d)</p>
            </div>

            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Bed className="w-3.5 h-3.5" style={{ color: '#8B5CF6' }} />
                <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Rest</p>
              </div>
              <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {checkinTrends.rest_days ?? 0}
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>days (30d)</p>
            </div>
          </div>
        </Card>
      )}

      {/* Training Load Management */}
      {trainingLoad && trainingLoad.acwr_series && trainingLoad.acwr_series.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Training Load Management</h3>
          <ACWRChart
            data={trainingLoad.acwr_series!}
            currentAcwr={trainingLoad.current_acwr!}
            currentZone={trainingLoad.current_zone!}
            insight={trainingLoad.insight!}
          />
        </Card>
      )}

      {/* Readiness × Performance */}
      {readinessCorr && (readinessCorr.data_points ?? 0) >= 3 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Readiness × Performance</h3>
          <CorrelationScatter
            scatter={readinessCorr.scatter!}
            rValue={readinessCorr.r_value!}
            optimalZone={readinessCorr.optimal_zone!}
            insight={readinessCorr.insight!}
          />
        </Card>
      )}

      {/* Technique Effectiveness */}
      {techniqueEff && techniqueEff.techniques && techniqueEff.techniques.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Technique Effectiveness</h3>
          <TechniqueQuadrant
            techniques={techniqueEff.techniques!}
            gameBreadth={techniqueEff.game_breadth!}
            moneyMoves={techniqueEff.money_moves!}
            insight={techniqueEff.insight!}
          />
        </Card>
      )}

      {/* Session Quality */}
      {sessionQuality && sessionQuality.sessions && sessionQuality.sessions.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Session Quality</h3>
          <QualityTrend
            sessions={sessionQuality.sessions!}
            avgQuality={sessionQuality.avg_quality!}
            topSessions={sessionQuality.top_sessions!}
            weeklyTrend={sessionQuality.weekly_trend!}
            insight={sessionQuality.insight!}
          />
        </Card>
      )}

      {/* Two-column: Risk + Recovery */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Overtraining Risk */}
        {riskData && (
          <Card>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Overtraining Risk</h3>
            <RiskGauge
              riskScore={riskData.risk_score!}
              level={riskData.level!}
              factors={riskData.factors!}
              recommendations={riskData.recommendations!}
            />
          </Card>
        )}

        {/* Recovery Insights */}
        {recoveryData && (
          <Card>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Recovery</h3>
            <div className="space-y-4">
              {/* Sleep Correlation */}
              {(recoveryData.data_points ?? 0) >= 3 && (
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                    Sleep → Performance
                  </p>
                  <p className="text-xl font-bold" style={{ color: Math.abs(recoveryData.sleep_correlation ?? 0) >= 0.3 ? 'var(--accent)' : 'var(--text)' }}>
                    r = {recoveryData.sleep_correlation}
                  </p>
                </div>
              )}

              {/* Optimal Rest Days */}
              {(recoveryData.optimal_rest_days ?? 0) > 0 && (
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                    Optimal Rest
                  </p>
                  <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                    {recoveryData.optimal_rest_days} day{(recoveryData.optimal_rest_days ?? 0) > 1 ? 's' : ''}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>between sessions</p>
                </div>
              )}

              {/* Rest Day Analysis */}
              {recoveryData.rest_analysis && recoveryData.rest_analysis.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>Sub Rate by Rest Days</p>
                  <div className="space-y-1">
                    {recoveryData.rest_analysis.map((r) => (
                      <div key={r.rest_days} className="flex items-center justify-between text-xs">
                        <span style={{ color: 'var(--text)' }}>{r.rest_days} day{r.rest_days !== 1 ? 's' : ''}</span>
                        <span style={{ color: r.rest_days === recoveryData.optimal_rest_days ? 'var(--accent)' : 'var(--muted)' }}>
                          {r.avg_sub_rate} ({r.sessions} sessions)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-sm" style={{ color: 'var(--muted)' }}>{recoveryData.insight}</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
