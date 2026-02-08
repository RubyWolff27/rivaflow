import { useState, useEffect } from 'react';
import { Brain, Activity } from 'lucide-react';
import { analyticsApi } from '../../api/client';
import { Card, CardSkeleton, EmptyState } from '../ui';
import ACWRChart from './ACWRChart';
import CorrelationScatter from './CorrelationScatter';
import TechniqueQuadrant from './TechniqueQuadrant';
import QualityTrend from './QualityTrend';
import RiskGauge from './RiskGauge';

interface InsightsTabProps {
  dateRange: { start: string; end: string };
}

export default function InsightsTab({ dateRange }: InsightsTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [trainingLoad, setTrainingLoad] = useState<any>(null);
  const [readinessCorr, setReadinessCorr] = useState<any>(null);
  const [techniqueEff, setTechniqueEff] = useState<any>(null);
  const [sessionQuality, setSessionQuality] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [recoveryData, setRecoveryData] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = dateRange.start && dateRange.end
          ? { start_date: dateRange.start, end_date: dateRange.end }
          : undefined;

        const [summaryRes, loadRes, corrRes, techRes, qualRes, riskRes, recRes] = await Promise.all([
          analyticsApi.insightsSummary().catch(() => ({ data: null })),
          analyticsApi.trainingLoad().catch(() => ({ data: null })),
          analyticsApi.readinessCorrelation(params).catch(() => ({ data: null })),
          analyticsApi.techniqueEffectiveness(params).catch(() => ({ data: null })),
          analyticsApi.sessionQuality(params).catch(() => ({ data: null })),
          analyticsApi.overtTrainingRisk().catch(() => ({ data: null })),
          analyticsApi.recoveryInsights().catch(() => ({ data: null })),
        ]);

        if (!cancelled) {
          setSummary(summaryRes.data);
          setTrainingLoad(loadRes.data);
          setReadinessCorr(corrRes.data);
          setTechniqueEff(techRes.data);
          setSessionQuality(qualRes.data);
          setRiskData(riskRes.data);
          setRecoveryData(recRes.data);
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Error loading insights:', err);
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
            <p className="text-2xl font-bold" style={{ color: zoneColors[summary.acwr_zone] || 'var(--text)' }}>
              {summary.acwr}
            </p>
            <p className="text-xs capitalize mt-1" style={{ color: 'var(--muted)' }}>{summary.acwr_zone?.replace('_', ' ')}</p>
          </div>

          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>Risk</p>
            <p className="text-2xl font-bold" style={{ color: riskColors[summary.risk_level] || 'var(--text)' }}>
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

      {/* Training Load Management */}
      {trainingLoad && trainingLoad.acwr_series && trainingLoad.acwr_series.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Training Load Management</h3>
          <ACWRChart
            data={trainingLoad.acwr_series}
            currentAcwr={trainingLoad.current_acwr}
            currentZone={trainingLoad.current_zone}
            insight={trainingLoad.insight}
          />
        </Card>
      )}

      {/* Readiness × Performance */}
      {readinessCorr && readinessCorr.data_points >= 3 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Readiness × Performance</h3>
          <CorrelationScatter
            scatter={readinessCorr.scatter}
            rValue={readinessCorr.r_value}
            optimalZone={readinessCorr.optimal_zone}
            insight={readinessCorr.insight}
          />
        </Card>
      )}

      {/* Technique Effectiveness */}
      {techniqueEff && techniqueEff.techniques && techniqueEff.techniques.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Technique Effectiveness</h3>
          <TechniqueQuadrant
            techniques={techniqueEff.techniques}
            gameBreadth={techniqueEff.game_breadth}
            moneyMoves={techniqueEff.money_moves}
            insight={techniqueEff.insight}
          />
        </Card>
      )}

      {/* Session Quality */}
      {sessionQuality && sessionQuality.sessions && sessionQuality.sessions.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Session Quality</h3>
          <QualityTrend
            sessions={sessionQuality.sessions}
            avgQuality={sessionQuality.avg_quality}
            topSessions={sessionQuality.top_sessions}
            weeklyTrend={sessionQuality.weekly_trend}
            insight={sessionQuality.insight}
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
              riskScore={riskData.risk_score}
              level={riskData.level}
              factors={riskData.factors}
              recommendations={riskData.recommendations}
            />
          </Card>
        )}

        {/* Recovery Insights */}
        {recoveryData && (
          <Card>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>Recovery</h3>
            <div className="space-y-4">
              {/* Sleep Correlation */}
              {recoveryData.data_points >= 3 && (
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                    Sleep → Performance
                  </p>
                  <p className="text-xl font-bold" style={{ color: Math.abs(recoveryData.sleep_correlation) >= 0.3 ? 'var(--accent)' : 'var(--text)' }}>
                    r = {recoveryData.sleep_correlation}
                  </p>
                </div>
              )}

              {/* Optimal Rest Days */}
              {recoveryData.optimal_rest_days > 0 && (
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                    Optimal Rest
                  </p>
                  <p className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                    {recoveryData.optimal_rest_days} day{recoveryData.optimal_rest_days > 1 ? 's' : ''}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>between sessions</p>
                </div>
              )}

              {/* Rest Day Analysis */}
              {recoveryData.rest_analysis && recoveryData.rest_analysis.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>Sub Rate by Rest Days</p>
                  <div className="space-y-1">
                    {recoveryData.rest_analysis.map((r: any) => (
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
