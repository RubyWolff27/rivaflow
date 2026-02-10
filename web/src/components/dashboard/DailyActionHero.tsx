import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Activity, Sparkles, Heart, Waves, RefreshCw } from 'lucide-react';
import { getLocalDateString } from '../../utils/date';
import { suggestionsApi, readinessApi, whoopApi } from '../../api/client';
import { Card, PrimaryButton, CardSkeleton } from '../ui';

interface TriggeredRule {
  name: string;
  recommendation: string;
  explanation: string;
  priority: number;
}

interface SuggestionData {
  suggestion: string;
  triggered_rules: TriggeredRule[];
  readiness?: { composite_score?: number };
}

const RULE_LABELS: Record<string, string> = {
  high_stress_low_energy: 'Stress / Low Energy',
  high_soreness: 'High Soreness',
  hotspot_active: 'Injury Hotspot',
  consecutive_gi: 'Consecutive Gi',
  consecutive_nogi: 'Consecutive No-Gi',
  green_light: 'All Clear',
  stale_technique: 'Stale Technique',
  whoop_low_recovery: 'WHOOP Low Recovery',
  whoop_hrv_drop: 'HRV Drop',
  whoop_hrv_sustained_decline: 'HRV Declining',
  whoop_green_recovery: 'Peak Recovery',
  comp_fight_week: 'Fight Week',
  comp_taper_warning: 'Taper Period',
  comp_peak_phase: 'Peak Phase',
  comp_base_building: 'Base Building',
  recovery_mode_active: 'Recovery Mode',
  persistent_injuries: 'Injuries',
  rest_after_high_intensity: 'High Intensity',
  deload_week: 'Deload Week',
  session_frequency_low: 'Long Break',
  sleep_debt_high: 'Sleep Debt',
};

const sanitizeSuggestion = (text: string) =>
  text.replace(/\{[a-z_]+\}/gi, '').replace(/\s{2,}/g, ' ').trim();

export default function DailyActionHero() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedIn, setHasCheckedIn] = useState(false);
  const [whoopRecovery, setWhoopRecovery] = useState<{
    recovery_score: number | null;
    hrv_ms: number | null;
    resting_hr: number | null;
  } | null>(null);
  const [whoopSyncing, setWhoopSyncing] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      // Load suggestion, readiness, and WHOOP in parallel
      const results = await Promise.allSettled([
        suggestionsApi.getToday(),
        readinessApi.getByDate(getLocalDateString()),
        whoopApi.getLatestRecovery(),
      ]);

      if (controller.signal.aborted) return;

      // Suggestion
      if (results[0].status === 'fulfilled' && results[0].value.data) {
        setSuggestion(results[0].value.data);
        if (results[0].value.data.readiness?.composite_score != null) {
          setReadinessScore(results[0].value.data.readiness.composite_score);
          setHasCheckedIn(true);
        }
      }

      // Readiness (fallback if suggestion didn't include it)
      if (results[1].status === 'fulfilled' && results[1].value.data) {
        setReadinessScore(results[1].value.data.composite_score);
        setHasCheckedIn(true);
      }

      // WHOOP
      if (results[2].status === 'fulfilled' && results[2].value.data?.recovery_score != null) {
        setWhoopRecovery(results[2].value.data);
      }

      setLoading(false);
    };
    load();
    return () => { controller.abort(); };
  }, []);

  if (loading) return <CardSkeleton lines={3} />;

  // Determine recommendation level
  const score = readinessScore ?? 0;
  let label: string;
  let labelBg: string;
  let labelColor: string;
  let iconBg: string;

  if (!hasCheckedIn && !whoopRecovery) {
    label = 'Check In';
    labelBg = 'var(--surfaceElev)';
    labelColor = 'var(--accent)';
    iconBg = 'var(--surfaceElev)';
  } else if (score >= 16 || (whoopRecovery && whoopRecovery.recovery_score !== null && whoopRecovery.recovery_score >= 67 && !hasCheckedIn)) {
    label = 'Train Hard';
    labelBg = 'var(--success-bg)';
    labelColor = 'var(--success)';
    iconBg = 'var(--success-bg)';
  } else if (score >= 12 || (whoopRecovery && whoopRecovery.recovery_score !== null && whoopRecovery.recovery_score >= 34 && !hasCheckedIn)) {
    label = 'Light Session';
    labelBg = 'var(--warning-bg)';
    labelColor = 'var(--warning)';
    iconBg = 'var(--warning-bg)';
  } else {
    label = 'Rest Day';
    labelBg = 'var(--danger-bg)';
    labelColor = 'var(--danger)';
    iconBg = 'var(--danger-bg)';
  }

  const whoopColor = whoopRecovery?.recovery_score != null
    ? whoopRecovery.recovery_score >= 67 ? '#10B981'
      : whoopRecovery.recovery_score >= 34 ? '#F59E0B'
      : '#EF4444'
    : undefined;

  const readinessColor = readinessScore != null
    ? readinessScore >= 16 ? '#10B981'
      : readinessScore >= 12 ? '#F59E0B'
      : '#EF4444'
    : undefined;

  return (
    <Card className="p-5">
      {/* Header row: "Today" + Log Session button */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
          Today
        </h2>
        <PrimaryButton onClick={() => navigate('/log')} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Log Session
        </PrimaryButton>
      </div>

      {/* Main recommendation */}
      {!hasCheckedIn && !whoopRecovery ? (
        // No data yet — prompt check-in
        <div className="mb-4">
          <div className="flex items-center gap-3 mb-2">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
              style={{ backgroundColor: iconBg }}
            >
              <Activity className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            </div>
            <div>
              <h3 className="text-lg font-bold" style={{ color: 'var(--text)' }}>
                How are you feeling?
              </h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Check in for personalized training guidance
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/readiness')}
            className="w-full mt-2 py-2.5 rounded-lg text-sm font-semibold transition-colors"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--accent)', border: '1px solid var(--border)' }}
          >
            Daily Check-in
          </button>
        </div>
      ) : (
        // Has data — show recommendation
        <div className="mb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: iconBg }}
            >
              <Sparkles className="w-6 h-6" style={{ color: labelColor }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span
                  className="text-sm font-bold uppercase tracking-wide px-2.5 py-1 rounded-md"
                  style={{ backgroundColor: labelBg, color: labelColor }}
                >
                  {label}
                </span>
              </div>
              {suggestion?.suggestion ? (
                <p className="text-sm mt-1 line-clamp-2" style={{ color: 'var(--muted)' }}>
                  {sanitizeSuggestion(suggestion.suggestion)}
                </p>
              ) : (
                <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
                  Based on your readiness score of {score}/20
                </p>
              )}
            </div>
          </div>

          {/* Triggered rules */}
          {suggestion?.triggered_rules && suggestion.triggered_rules.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {suggestion.triggered_rules.slice(0, 3).map((rule, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)', border: '1px solid var(--border)' }}
                >
                  {RULE_LABELS[rule.name] || rule.name.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recovery indicators row */}
      {(hasCheckedIn || whoopRecovery) && (
        <Link to="/readiness">
          <div
            className="flex items-center gap-3 p-3 rounded-lg transition-colors hover:opacity-90"
            style={{ backgroundColor: 'var(--surfaceElev)' }}
          >
            {/* Readiness pill */}
            {hasCheckedIn && readinessScore != null && (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Activity className="w-4 h-4 shrink-0" style={{ color: readinessColor }} />
                <div>
                  <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Readiness</p>
                  <p className="text-lg font-bold leading-tight" style={{ color: readinessColor }}>
                    {readinessScore}<span className="text-xs font-normal" style={{ color: 'var(--muted)' }}>/20</span>
                  </p>
                </div>
              </div>
            )}

            {/* Divider */}
            {hasCheckedIn && readinessScore != null && whoopRecovery && (
              <div className="w-px h-8" style={{ backgroundColor: 'var(--border)' }} />
            )}

            {/* WHOOP pill */}
            {whoopRecovery && whoopRecovery.recovery_score != null && (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className="w-5 h-5 rounded-full bg-black flex items-center justify-center shrink-0">
                  <span className="text-white font-bold text-[10px]">W</span>
                </div>
                <div>
                  <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Recovery</p>
                  <p className="text-lg font-bold leading-tight" style={{ color: whoopColor }}>
                    {Math.round(whoopRecovery.recovery_score)}%
                  </p>
                </div>
              </div>
            )}

            {/* Supporting metrics */}
            {whoopRecovery && (
              <div className="hidden sm:flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
                {whoopRecovery.hrv_ms != null && (
                  <div className="text-center">
                    <Waves className="w-3 h-3 mx-auto mb-0.5" style={{ color: 'var(--accent)' }} />
                    <p className="font-semibold" style={{ color: 'var(--text)' }}>{Math.round(whoopRecovery.hrv_ms)}</p>
                    <p>HRV</p>
                  </div>
                )}
                {whoopRecovery.resting_hr != null && (
                  <div className="text-center">
                    <Heart className="w-3 h-3 mx-auto mb-0.5" style={{ color: 'var(--accent)' }} />
                    <p className="font-semibold" style={{ color: 'var(--text)' }}>{Math.round(whoopRecovery.resting_hr)}</p>
                    <p>RHR</p>
                  </div>
                )}
              </div>
            )}

            {/* WHOOP sync button */}
            {whoopRecovery && (
              <button
                onClick={async (e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setWhoopSyncing(true);
                  try {
                    await whoopApi.sync();
                    const res = await whoopApi.getLatestRecovery();
                    if (res.data?.recovery_score != null) setWhoopRecovery(res.data);
                  } catch { /* best-effort */ }
                  setWhoopSyncing(false);
                }}
                disabled={whoopSyncing}
                className="p-1.5 rounded-md hover:opacity-80 shrink-0"
                style={{ color: 'var(--muted)' }}
                title="Sync WHOOP"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${whoopSyncing ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </Link>
      )}
    </Card>
  );
}
