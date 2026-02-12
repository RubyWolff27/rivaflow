import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Activity, Sparkles, Heart, Waves, RefreshCw, Sun, Moon, ChevronDown, ChevronUp, CalendarCheck, Coffee, Briefcase, AlertTriangle, Plane, Flame } from 'lucide-react';
import { getLocalDateString } from '../../utils/date';
import { suggestionsApi, readinessApi, whoopApi, checkinsApi, streaksApi } from '../../api/client';
import { getErrorMessage } from '../../api/client';
import { Card, PrimaryButton, CardSkeleton } from '../ui';
import type { DayCheckins, StreakStatus } from '../../types';

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

/* ---------- Inline sub-components ---------- */

function MiddayPrompt({ onSubmitted, todayPlan }: { onSubmitted: () => void; todayPlan?: string }) {
  const [expanded, setExpanded] = useState(false);
  const [energy, setEnergy] = useState(3);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setSaving(true);
    setError('');
    try {
      await checkinsApi.createMidday({ energy_level: energy, midday_note: note || undefined });
      onSubmitted();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const energyLabels = ['', 'Very Low', 'Low', 'Moderate', 'Good', 'Great'];

  return (
    <div
      className="mt-3 rounded-xl overflow-hidden"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <div className="flex items-center gap-2">
          <Sun className="w-4 h-4" style={{ color: '#F59E0B' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Midday Energy Check
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          {/* Remind of today's plan */}
          {todayPlan && (
            <div
              className="flex items-center gap-2 p-2 rounded-lg text-xs"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <CalendarCheck className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--accent)' }} />
              <span style={{ color: 'var(--muted)' }}>Today's plan: <strong style={{ color: 'var(--text)' }}>{todayPlan}</strong> — still on?</span>
            </div>
          )}

          {/* Energy slider */}
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
              Energy Level: <span style={{ color: 'var(--text)' }}>{energy}/5 — {energyLabels[energy]}</span>
            </label>
            <input
              type="range" min={1} max={5} value={energy}
              onChange={(e) => setEnergy(Number(e.target.value))}
              className="w-full mt-1 accent-[var(--accent)]"
            />
          </div>

          {/* Optional note */}
          <input
            type="text"
            placeholder="Quick note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="w-full text-sm rounded-lg px-3 py-2"
            style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
          />

          {error && <p className="text-xs" style={{ color: 'var(--error)' }}>{error}</p>}

          <button
            onClick={submit}
            disabled={saving}
            className="w-full py-2 rounded-lg text-sm font-semibold transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#fff', opacity: saving ? 0.6 : 1 }}
          >
            {saving ? 'Saving...' : 'Save Midday Check-in'}
          </button>
        </div>
      )}
    </div>
  );
}

function MorningPrompt({ onNavigate }: { onNavigate: () => void }) {
  return (
    <div
      className="mt-3 rounded-xl overflow-hidden"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          <Sun className="w-4 h-4" style={{ color: '#F59E0B' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Morning Check-in
          </span>
        </div>
        <button
          onClick={onNavigate}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          Check in
        </button>
      </div>
      <p className="px-3 pb-3 text-xs" style={{ color: 'var(--muted)' }}>
        Log how you're feeling to get personalized training guidance
      </p>
    </div>
  );
}

const REST_TYPES = [
  { id: 'recovery', label: 'Recovery', icon: Coffee, color: '#10B981' },
  { id: 'life', label: 'Life', icon: Briefcase, color: '#3B82F6' },
  { id: 'injury', label: 'Injury', icon: AlertTriangle, color: '#EF4444' },
  { id: 'travel', label: 'Travel', icon: Plane, color: '#8B5CF6' },
];

function EveningPrompt({ onSubmitted }: { onSubmitted: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [didNotTrain, setDidNotTrain] = useState(false);
  const [quality, setQuality] = useState(3);
  const [recoveryNote, setRecoveryNote] = useState('');
  const [tomorrow, setTomorrow] = useState('');
  const [restType, setRestType] = useState<string | null>(null);
  const [restNote, setRestNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setSaving(true);
    setError('');
    try {
      await checkinsApi.createEvening({
        did_not_train: didNotTrain,
        rest_type: didNotTrain ? (restType || undefined) : undefined,
        rest_note: didNotTrain ? (restNote || undefined) : undefined,
        training_quality: didNotTrain ? undefined : quality,
        recovery_note: recoveryNote || undefined,
        tomorrow_intention: tomorrow || undefined,
      });
      onSubmitted();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const qualityLabels = ['', 'Poor', 'Below Avg', 'Average', 'Good', 'Excellent'];

  return (
    <div
      className="mt-3 rounded-xl overflow-hidden"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <div className="flex items-center gap-2">
          <Moon className="w-4 h-4" style={{ color: '#8B5CF6' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Evening Reflection
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          {/* Train / Rest toggle */}
          <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }}>
            <button
              onClick={() => setDidNotTrain(false)}
              className="flex-1 py-2 text-sm font-semibold transition-colors"
              style={{
                backgroundColor: !didNotTrain ? 'var(--accent)' : 'var(--surface)',
                color: !didNotTrain ? '#fff' : 'var(--muted)',
              }}
            >
              I trained
            </button>
            <button
              onClick={() => setDidNotTrain(true)}
              className="flex-1 py-2 text-sm font-semibold transition-colors"
              style={{
                backgroundColor: didNotTrain ? 'var(--surfaceElev)' : 'var(--surface)',
                color: didNotTrain ? 'var(--text)' : 'var(--muted)',
                borderLeft: '1px solid var(--border)',
              }}
            >
              Rest day
            </button>
          </div>

          {!didNotTrain ? (
            <>
              {/* Training quality slider */}
              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                  Training Quality: <span style={{ color: 'var(--text)' }}>{quality}/5 — {qualityLabels[quality]}</span>
                </label>
                <input
                  type="range" min={1} max={5} value={quality}
                  onChange={(e) => setQuality(Number(e.target.value))}
                  className="w-full mt-1 accent-[var(--accent)]"
                />
              </div>

              {/* Recovery note */}
              <textarea
                placeholder="How does your body feel? Any notes on recovery..."
                value={recoveryNote}
                onChange={(e) => setRecoveryNote(e.target.value)}
                rows={2}
                className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />
            </>
          ) : (
            <>
              {/* Rest type picker */}
              <div>
                <label className="text-xs font-medium mb-2 block" style={{ color: 'var(--muted)' }}>
                  Why no training?
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {REST_TYPES.map((rt) => {
                    const Icon = rt.icon;
                    const selected = restType === rt.id;
                    return (
                      <button
                        key={rt.id}
                        onClick={() => setRestType(selected ? null : rt.id)}
                        className="flex flex-col items-center gap-1 py-2 rounded-lg text-xs font-medium transition-all"
                        style={{
                          backgroundColor: selected ? 'var(--surfaceElev)' : 'var(--surface)',
                          border: selected ? `1px solid ${rt.color}` : '1px solid var(--border)',
                          color: selected ? rt.color : 'var(--muted)',
                        }}
                      >
                        <Icon className="w-4 h-4" />
                        {rt.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Rest note */}
              <input
                type="text"
                placeholder="Quick note (optional)"
                value={restNote}
                onChange={(e) => setRestNote(e.target.value)}
                className="w-full text-sm rounded-lg px-3 py-2"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />

              {/* Recovery note (still useful on rest days) */}
              <textarea
                placeholder="How does your body feel?"
                value={recoveryNote}
                onChange={(e) => setRecoveryNote(e.target.value)}
                rows={2}
                className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />
            </>
          )}

          {/* Tomorrow's plan */}
          <input
            type="text"
            placeholder="Tomorrow's plan (e.g. 5km jog, BJJ Gi at 17:30)"
            value={tomorrow}
            onChange={(e) => setTomorrow(e.target.value)}
            className="w-full text-sm rounded-lg px-3 py-2"
            style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
          />

          {error && <p className="text-xs" style={{ color: 'var(--error)' }}>{error}</p>}

          <button
            onClick={submit}
            disabled={saving}
            className="w-full py-2 rounded-lg text-sm font-semibold transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#fff', opacity: saving ? 0.6 : 1 }}
          >
            {saving ? 'Saving...' : 'Save Evening Reflection'}
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------- Yesterday's Plan Banner ---------- */

function TodayPlanBanner({ intention, onLog }: { intention: string; onLog: () => void }) {
  return (
    <div
      className="flex items-center gap-3 p-3 rounded-xl mb-4"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
        style={{ backgroundColor: 'var(--warning-bg)' }}
      >
        <CalendarCheck className="w-4 h-4" style={{ color: 'var(--warning)' }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Your plan today</p>
        <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>{intention}</p>
      </div>
      <button
        onClick={onLog}
        className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
        style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
      >
        Log it
      </button>
    </div>
  );
}

/* ---------- Main component ---------- */

export default function DailyActionHero() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedIn, setHasCheckedIn] = useState(false);
  const [dayCheckins, setDayCheckins] = useState<DayCheckins | null>(null);
  const [todayPlan, setTodayPlan] = useState<string | undefined>(undefined);
  const [whoopRecovery, setWhoopRecovery] = useState<{
    recovery_score: number | null;
    hrv_ms: number | null;
    resting_hr: number | null;
  } | null>(null);
  const [whoopSyncing, setWhoopSyncing] = useState(false);
  const [streaks, setStreaks] = useState<StreakStatus | null>(null);

  const loadCheckins = async () => {
    try {
      const res = await checkinsApi.getToday();
      setDayCheckins(res.data);
      setHasCheckedIn(res.data.checked_in);
    } catch { /* best-effort */ }
  };

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      // Load suggestion, readiness, WHOOP, checkins, and yesterday in parallel
      const results = await Promise.allSettled([
        suggestionsApi.getToday(),
        readinessApi.getByDate(getLocalDateString()),
        whoopApi.getLatestRecovery(),
        checkinsApi.getToday(),
        checkinsApi.getYesterday(),
        streaksApi.getStatus(),
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

      // Day checkins
      if (results[3].status === 'fulfilled' && results[3].value.data) {
        setDayCheckins(results[3].value.data);
        if (results[3].value.data.checked_in) {
          setHasCheckedIn(true);
        }
      }

      // Yesterday's plan (Wave B)
      if (results[4].status === 'fulfilled' && results[4].value.data) {
        const y = results[4].value.data;
        // Check evening first, then other slots for tomorrow_intention
        const intention = y.evening?.tomorrow_intention
          || y.midday?.tomorrow_intention
          || y.morning?.tomorrow_intention;
        if (intention) {
          setTodayPlan(intention);
        }
      }

      // Streaks (Wave E)
      if (results[5].status === 'fulfilled' && results[5].value.data) {
        setStreaks(results[5].value.data);
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

  // Show prompts for unfilled slots (all accessible regardless of time)
  const hasMorning = dayCheckins?.morning != null;
  const hasMidday = dayCheckins?.midday != null;
  const hasEvening = dayCheckins?.evening != null;
  const showMorning = !hasMorning;
  const showMidday = !hasMidday;
  const showEvening = !hasEvening;

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

      {/* Yesterday's plan banner */}
      {todayPlan && (
        <TodayPlanBanner
          intention={todayPlan}
          onLog={() => navigate('/log')}
        />
      )}

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

      {/* Streak display (Wave E) */}
      {streaks && streaks.checkin.current_streak > 0 && (
        <div
          className="flex items-center justify-between mt-3 p-3 rounded-lg"
          style={{ backgroundColor: 'var(--surfaceElev)' }}
        >
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-500" />
            <span className="text-xl font-bold text-orange-600">
              {streaks.checkin.current_streak}
            </span>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>day streak</span>
          </div>
          {streaks.checkin.longest_streak > streaks.checkin.current_streak && (
            <span className="text-xs text-orange-500">
              {streaks.checkin.longest_streak - streaks.checkin.current_streak <= 3
                ? `${streaks.checkin.longest_streak - streaks.checkin.current_streak} more to beat your best!`
                : `Best: ${streaks.checkin.longest_streak}`}
            </span>
          )}
          {streaks.checkin.current_streak >= streaks.checkin.longest_streak && streaks.checkin.current_streak >= 3 && (
            <span className="text-xs font-medium text-orange-500">
              Personal best!
            </span>
          )}
        </div>
      )}

      {/* Morning prompt */}
      {showMorning && <MorningPrompt onNavigate={() => navigate('/readiness')} />}

      {/* Midday prompt */}
      {showMidday && <MiddayPrompt onSubmitted={loadCheckins} todayPlan={todayPlan} />}

      {/* Evening prompt */}
      {showEvening && <EveningPrompt onSubmitted={loadCheckins} />}

      {/* Completed slot badges */}
      {(hasMorning || hasMidday || hasEvening || dayCheckins?.evening?.checkin_type === 'rest') && (
        <div className="flex flex-wrap gap-2 mt-3">
          {hasMorning && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
            >
              Morning logged
            </span>
          )}
          {hasMidday && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
            >
              Midday logged
            </span>
          )}
          {hasEvening && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
            >
              Evening logged
            </span>
          )}
          {dayCheckins?.evening?.checkin_type === 'rest' && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
            >
              Rest day
            </span>
          )}
        </div>
      )}
    </Card>
  );
}
