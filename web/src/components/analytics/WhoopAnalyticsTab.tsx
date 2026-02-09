import { useState, useEffect } from 'react';
import { analyticsApi } from '../../api/client';
import { Heart, Activity, TrendingDown, TrendingUp, Moon, Zap, Shield, Brain } from 'lucide-react';
import { Card, CardSkeleton } from '../ui';

interface Props {
  days?: number;
}

const ZONE_COLORS: Record<string, string> = {
  green: '#10B981',
  yellow: '#F59E0B',
  red: '#EF4444',
};

export default function WhoopAnalyticsTab({ days = 90 }: Props) {
  const [perfCorr, setPerfCorr] = useState<any>(null);
  const [efficiency, setEfficiency] = useState<any>(null);
  const [cardio, setCardio] = useState<any>(null);
  const [sleepDebt, setSleepDebt] = useState<any>(null);
  const [readinessModel, setReadinessModel] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      setError(null);
      try {
        const [corrRes, effRes, cardioRes, debtRes, readyRes] = await Promise.all([
          analyticsApi.whoopPerformanceCorrelation({ days }).catch(() => ({ data: null })),
          analyticsApi.whoopEfficiency({ days }).catch(() => ({ data: null })),
          analyticsApi.whoopCardiovascular({ days }).catch(() => ({ data: null })),
          analyticsApi.whoopSleepDebt({ days }).catch(() => ({ data: null })),
          analyticsApi.whoopReadinessModel({ days }).catch(() => ({ data: null })),
        ]);
        if (!cancelled) {
          setPerfCorr(corrRes.data);
          setEfficiency(effRes.data);
          setCardio(cardioRes.data);
          setSleepDebt(debtRes.data);
          setReadinessModel(readyRes.data);
        }
      } catch {
        if (!cancelled) setError('Failed to load WHOOP analytics');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [days]);

  if (loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={3} />
        <CardSkeleton lines={3} />
        <CardSkeleton lines={3} />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <p className="text-center py-8 text-sm" style={{ color: 'var(--muted)' }}>{error}</p>
      </Card>
    );
  }

  const recoveryCorr = perfCorr?.recovery_correlation;
  const hrvPredictor = perfCorr?.hrv_predictor;
  const strainEff = efficiency?.strain_efficiency;
  const sleepAnalysis = efficiency?.sleep_analysis;

  return (
    <div className="space-y-6">
      {/* 1. Recovery vs Performance */}
      {recoveryCorr && recoveryCorr.scatter?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-5 h-5" style={{ color: '#EF4444' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Recovery vs Performance</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{recoveryCorr.insight}</p>

          {/* Zone comparison bars */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {(['green', 'yellow', 'red'] as const).map(zone => {
              const info = recoveryCorr.zones?.[zone];
              if (!info) return null;
              return (
                <div key={zone} className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)', borderLeft: `3px solid ${ZONE_COLORS[zone]}` }}>
                  <p className="text-xs font-medium uppercase" style={{ color: ZONE_COLORS[zone] }}>
                    {zone === 'green' ? '67-100%' : zone === 'yellow' ? '34-66%' : '0-33%'}
                  </p>
                  <p className="text-xl font-bold mt-1" style={{ color: 'var(--text)' }}>
                    {info.avg_sub_rate}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>sub ratio ({info.sessions} sessions)</p>
                </div>
              );
            })}
          </div>

          {recoveryCorr.r_value != null && (
            <p className="text-xs text-center" style={{ color: 'var(--muted)' }}>
              Correlation: r = {recoveryCorr.r_value} ({Math.abs(recoveryCorr.r_value) >= 0.3 ? 'significant' : 'weak'})
            </p>
          )}
        </Card>
      )}

      {/* 2. HRV Performance Predictor */}
      {hrvPredictor && hrvPredictor.scatter?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5" style={{ color: '#8B5CF6' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>HRV Performance Predictor</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{hrvPredictor.insight}</p>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>HRV &ge; {hrvPredictor.hrv_threshold}ms</p>
              <p className="text-2xl font-bold" style={{ color: '#10B981' }}>{hrvPredictor.quality_above}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>avg quality /100</p>
            </div>
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>HRV &lt; {hrvPredictor.hrv_threshold}ms</p>
              <p className="text-2xl font-bold" style={{ color: '#EF4444' }}>{hrvPredictor.quality_below}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>avg quality /100</p>
            </div>
          </div>
        </Card>
      )}

      {/* 3. Strain Efficiency */}
      {strainEff && strainEff.top_sessions?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5" style={{ color: '#F59E0B' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Strain Efficiency</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{strainEff.insight}</p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Overall Efficiency</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{strainEff.overall_efficiency}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>subs / strain</p>
            </div>
            {strainEff.by_class_type && Object.keys(strainEff.by_class_type).length > 0 && (
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                <p className="text-xs mb-2" style={{ color: 'var(--muted)' }}>By Class Type</p>
                {Object.entries(strainEff.by_class_type).map(([ct, eff]) => (
                  <div key={ct} className="flex justify-between text-sm">
                    <span style={{ color: 'var(--text)' }}>{ct}</span>
                    <span className="font-medium" style={{ color: 'var(--accent)' }}>{eff as number}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top sessions */}
          <p className="text-xs font-medium uppercase mb-2" style={{ color: 'var(--muted)' }}>Most Efficient Sessions</p>
          <div className="space-y-1">
            {strainEff.top_sessions.slice(0, 3).map((s: any) => (
              <div key={s.session_id} className="flex justify-between text-sm p-2 rounded" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                <span style={{ color: 'var(--muted)' }}>{new Date(s.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                <span style={{ color: 'var(--text)' }}>{s.submissions} subs / {Number(s.strain).toFixed(1)} strain = <span className="font-semibold" style={{ color: 'var(--accent)' }}>{s.efficiency}</span></span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 4. Sleep Quality Impact */}
      {sleepAnalysis && sleepAnalysis.scatter?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Moon className="w-5 h-5" style={{ color: '#60A5FA' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Sleep Quality Impact</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{sleepAnalysis.insight}</p>

          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Total Sleep</p>
              <p className="text-lg font-bold" style={{ color: 'var(--text)' }}>r = {sleepAnalysis.total_sleep_r}</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>REM Impact</p>
              <p className="text-lg font-bold" style={{ color: '#8B5CF6' }}>r = {sleepAnalysis.rem_r}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>opt: {sleepAnalysis.optimal_rem_pct}%</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Deep Sleep</p>
              <p className="text-lg font-bold" style={{ color: '#3B82F6' }}>r = {sleepAnalysis.sws_r}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>opt: {sleepAnalysis.optimal_sws_pct}%</p>
            </div>
          </div>
        </Card>
      )}

      {/* 5. Cardiovascular Adaptation */}
      {cardio && cardio.weekly_rhr?.length >= 2 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5" style={{ color: '#EF4444' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Cardiovascular Adaptation</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{cardio.insight}</p>

          {/* Current vs Baseline */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Current RHR</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{cardio.current_rhr}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>bpm</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Baseline</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--muted)' }}>{cardio.baseline_rhr}</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>bpm</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Trend</p>
              <div className="flex items-center justify-center gap-1 mt-1">
                {cardio.trend === 'improving' ? (
                  <TrendingDown className="w-5 h-5 text-green-500" />
                ) : cardio.trend === 'rising' ? (
                  <TrendingUp className="w-5 h-5 text-red-500" />
                ) : (
                  <Activity className="w-5 h-5 text-gray-400" />
                )}
                <span className="text-sm font-medium capitalize" style={{ color: cardio.trend === 'improving' ? '#10B981' : cardio.trend === 'rising' ? '#EF4444' : 'var(--muted)' }}>
                  {cardio.trend === 'improving' ? 'Improving' : cardio.trend === 'rising' ? 'Rising' : 'Stable'}
                </span>
              </div>
            </div>
          </div>

          {/* RHR Timeline */}
          <div className="space-y-1">
            {cardio.weekly_rhr.map((w: any) => {
              const maxRhr = Math.max(...cardio.weekly_rhr.map((x: any) => x.avg_rhr));
              const minRhr = Math.min(...cardio.weekly_rhr.map((x: any) => x.avg_rhr));
              const range = maxRhr - minRhr || 1;
              const pct = ((w.avg_rhr - minRhr) / range) * 60 + 20; // 20-80% width
              return (
                <div key={w.week} className="flex items-center gap-2">
                  <span className="text-xs w-16 text-right" style={{ color: 'var(--muted)' }}>{w.week.replace('Y', '').replace('-W', ' W')}</span>
                  <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: w.avg_rhr <= (minRhr + range * 0.33) ? '#10B981' : w.avg_rhr >= (maxRhr - range * 0.33) ? '#EF4444' : '#F59E0B' }} />
                  </div>
                  <span className="text-xs font-medium w-12" style={{ color: 'var(--text)' }}>{w.avg_rhr}</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 6. Sleep Debt Tracker */}
      {sleepDebt && sleepDebt.weekly?.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Moon className="w-5 h-5" style={{ color: '#A78BFA' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Sleep Debt Tracker</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{sleepDebt.insight}</p>

          <div className="space-y-2">
            {sleepDebt.weekly.map((w: any) => (
              <div key={w.week} className="flex items-center gap-3 p-2 rounded" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                <span className="text-xs w-16" style={{ color: 'var(--muted)' }}>{w.week.replace('Y', '').replace('-W', ' W')}</span>
                <div className="flex-1 grid grid-cols-3 gap-2 text-xs">
                  {w.avg_sleep_hrs != null && (
                    <div>
                      <span style={{ color: 'var(--muted)' }}>Sleep: </span>
                      <span className="font-medium" style={{ color: 'var(--text)' }}>{w.avg_sleep_hrs}h</span>
                    </div>
                  )}
                  {w.avg_debt_hrs != null && (
                    <div>
                      <span style={{ color: 'var(--muted)' }}>Debt: </span>
                      <span className="font-medium" style={{ color: w.avg_debt_hrs > 1 ? '#EF4444' : '#10B981' }}>{w.avg_debt_hrs}h</span>
                    </div>
                  )}
                  <div>
                    <span style={{ color: 'var(--muted)' }}>Training: </span>
                    <span className="font-medium" style={{ color: 'var(--text)' }}>{w.sessions}x ({w.training_hours}h)</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 7. Recovery Readiness Model */}
      {readinessModel && Object.values(readinessModel.zones || {}).some((z: any) => z.sessions > 0) && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5" style={{ color: '#10B981' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Recovery Readiness Model</h3>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>{readinessModel.insight}</p>

          <div className="space-y-3">
            {(['green', 'yellow', 'red'] as const).map(zone => {
              const info = readinessModel.zones?.[zone];
              if (!info || info.sessions === 0) return null;
              return (
                <div key={zone} className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', borderLeft: `4px solid ${ZONE_COLORS[zone]}` }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold capitalize" style={{ color: ZONE_COLORS[zone] }}>
                      {zone} Recovery ({zone === 'green' ? '67-100%' : zone === 'yellow' ? '34-66%' : '0-33%'})
                    </span>
                    <span className="text-xs" style={{ color: 'var(--muted)' }}>{info.sessions} sessions</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div>
                      <p style={{ color: 'var(--muted)' }}>Intensity</p>
                      <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{info.avg_intensity}/5</p>
                    </div>
                    <div>
                      <p style={{ color: 'var(--muted)' }}>Rolls</p>
                      <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{info.avg_rolls}</p>
                    </div>
                    <div>
                      <p style={{ color: 'var(--muted)' }}>Subs For</p>
                      <p className="font-semibold text-sm" style={{ color: '#10B981' }}>{info.avg_subs_for}</p>
                    </div>
                    <div>
                      <p style={{ color: 'var(--muted)' }}>Sub Ratio</p>
                      <p className="font-semibold text-sm" style={{ color: info.sub_rate >= 1 ? 'var(--accent)' : 'var(--text)' }}>{info.sub_rate}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Empty state */}
      {!recoveryCorr?.scatter?.length && !strainEff?.top_sessions?.length && !cardio?.weekly_rhr?.length && (
        <Card>
          <div className="text-center py-8">
            <Heart className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
            <h3 className="font-semibold mb-2" style={{ color: 'var(--text)' }}>No WHOOP Analytics Data</h3>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Connect your WHOOP and log sessions to see recovery correlations, strain efficiency, sleep impact, and more.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
