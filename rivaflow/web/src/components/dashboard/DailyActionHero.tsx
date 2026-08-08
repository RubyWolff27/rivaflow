import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Activity, Sparkles } from 'lucide-react';
import { getLocalDateString } from '../../utils/date';
import { logger } from '../../utils/logger';
import { suggestionsApi, readinessApi, checkinsApi, sessionsApi, goalsApi, gymsApi, profileApi } from '../../api/client';
import { Card, PrimaryButton, CardSkeleton } from '../ui';
import SmartPlanBanner from './SmartPlanBanner';
import MorningPrompt from './MorningPrompt';
import MiddayPrompt from './MiddayPrompt';
import EveningPrompt from './EveningPrompt';
import CheckinBadges from './CheckinBadges';
import type { DayCheckins, Session, WeeklyGoalProgress, GymClass } from '../../types';

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
  whoop_low_recovery: 'Low Readiness',
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
  monotony_high: 'Flat Load Week',
};

const sanitizeSuggestion = (text: string) =>
  text.replace(/\{[a-z_]+\}/gi, '').replace(/\s{2,}/g, ' ').trim();

/** Readiness composite score thresholds (0-20 scale) */
const READINESS_HIGH_THRESHOLD = 16;
const READINESS_MODERATE_THRESHOLD = 12;

export default function DailyActionHero() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedIn, setHasCheckedIn] = useState(false);
  const [dayCheckins, setDayCheckins] = useState<DayCheckins | null>(null);
  const [todayPlan, setTodayPlan] = useState<string | undefined>(undefined);
  const [todaySessions, setTodaySessions] = useState<Session[]>([]);
  const [todaysClasses, setTodaysClasses] = useState<GymClass[]>([]);
  const [weeklyGoals, setWeeklyGoals] = useState<WeeklyGoalProgress | null>(null);

  const loadCheckins = async () => {
    try {
      const res = await checkinsApi.getToday();
      setDayCheckins(res.data);
      setHasCheckedIn(res.data.checked_in);
    } catch (err) { logger.debug('Load checkins best-effort failed', err); }
  };

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      const today = getLocalDateString();
      const results = await Promise.allSettled([
        suggestionsApi.getToday(),
        readinessApi.getByDate(today),
        checkinsApi.getToday(),
        checkinsApi.getYesterday(),
        sessionsApi.getByRange(today, today),
        goalsApi.getCurrentWeek(),
        profileApi.get().then(res =>
          res.data.primary_gym_id
            ? gymsApi.getTodaysClasses(res.data.primary_gym_id)
            : { data: { classes: [] as GymClass[] } }
        ),
      ]);

      if (controller.signal.aborted) return;

      if (results[0].status === 'fulfilled' && results[0].value.data) {
        setSuggestion(results[0].value.data);
        if (results[0].value.data.readiness?.composite_score != null) {
          setReadinessScore(results[0].value.data.readiness.composite_score);
          setHasCheckedIn(true);
        }
      }

      if (results[1].status === 'fulfilled' && results[1].value.data) {
        setReadinessScore(results[1].value.data.composite_score);
        setHasCheckedIn(true);
      }

      if (results[2].status === 'fulfilled' && results[2].value.data) {
        setDayCheckins(results[2].value.data);
        if (results[2].value.data.checked_in) {
          setHasCheckedIn(true);
        }
      }

      if (results[3].status === 'fulfilled' && results[3].value.data) {
        const y = results[3].value.data;
        const intention = y.evening?.tomorrow_intention
          || y.midday?.tomorrow_intention
          || y.morning?.tomorrow_intention;
        if (intention) {
          setTodayPlan(intention);
        }
      }

      if (results[4].status === 'fulfilled' && results[4].value.data) {
        const sessions = results[4].value.data;
        if (Array.isArray(sessions)) {
          setTodaySessions(sessions);
        }
      }

      if (results[5].status === 'fulfilled' && results[5].value.data) {
        setWeeklyGoals(results[5].value.data);
      }

      if (results[6].status === 'fulfilled' && results[6].value.data) {
        const classData = results[6].value.data;
        if (classData.classes && Array.isArray(classData.classes)) {
          setTodaysClasses(classData.classes);
        }
      }

      setLoading(false);
    };
    load();
    return () => { controller.abort(); };
  }, []);

  if (loading) return <CardSkeleton lines={3} />;

  const score = readinessScore ?? 0;
  let label: string;
  let labelBg: string;
  let labelColor: string;
  let iconBg: string;

  if (!hasCheckedIn) {
    label = 'Check In';
    labelBg = 'var(--surfaceElev)';
    labelColor = 'var(--accent)';
    iconBg = 'var(--surfaceElev)';
  } else if (score >= READINESS_HIGH_THRESHOLD) {
    label = 'Train Hard';
    labelBg = 'var(--success-bg)';
    labelColor = 'var(--success)';
    iconBg = 'var(--success-bg)';
  } else if (score >= READINESS_MODERATE_THRESHOLD) {
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

  const readinessColor = readinessScore != null
    ? readinessScore >= READINESS_HIGH_THRESHOLD ? '#10B981'
      : readinessScore >= READINESS_MODERATE_THRESHOLD ? '#F59E0B'
      : '#EF4444'
    : undefined;

  const statsBorderColor = readinessColor || 'var(--border)';

  const hasMorning = dayCheckins?.morning != null;
  const hasMidday = dayCheckins?.midday != null;
  const hasEvening = dayCheckins?.evening != null;
  const showMorning = !hasMorning;
  const showMidday = !hasMidday;
  const showEvening = !hasEvening;

  return (
    <Card variant="hero">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
          Today
        </h2>
        <PrimaryButton onClick={() => navigate('/log')} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Log Session
        </PrimaryButton>
      </div>

      {!bannerDismissed && (
        <SmartPlanBanner
          intention={todayPlan}
          todaySessions={todaySessions}
          todaysClasses={todaysClasses}
          weeklyGoals={weeklyGoals}
          onLog={() => navigate('/log')}
          onDismiss={() => setBannerDismissed(true)}
        />
      )}

      {!hasCheckedIn ? (
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
        <div className="mb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: iconBg }}
            >
              <Sparkles className="w-6 h-6" style={{ color: labelColor }} />
            </div>
            <div className="flex-1 min-w-0">
              {todaySessions.length > 0 && (
                <p className="text-[11px] font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                  For your next session
                </p>
              )}
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
                  Based on your check-in score of {score}/20
                </p>
              )}
            </div>
          </div>

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

      {hasCheckedIn && (
        <Link to="/readiness">
          <div
            className="flex items-center gap-3 p-3 rounded-lg transition-colors hover:opacity-90"
            style={{ backgroundColor: 'var(--surfaceElev)', borderLeft: `3px solid ${statsBorderColor}` }}
          >
            {hasCheckedIn && readinessScore != null && (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Activity className="w-4 h-4 shrink-0" style={{ color: readinessColor }} />
                <div>
                  <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Check-in</p>
                  <p className="text-lg font-bold leading-tight" style={{ color: readinessColor }}>
                    {readinessScore}<span className="text-xs font-normal" style={{ color: 'var(--muted)' }}>/20</span>
                  </p>
                </div>
              </div>
            )}

          </div>
        </Link>
      )}

      {showMorning && <MorningPrompt onNavigate={() => navigate('/readiness')} />}
      {showMidday && <MiddayPrompt onSubmitted={loadCheckins} todayPlan={todayPlan} />}
      {showEvening && <EveningPrompt onSubmitted={loadCheckins} />}

      {(hasMorning || hasMidday || hasEvening) && (
        <CheckinBadges dayCheckins={dayCheckins} onUpdated={loadCheckins} />
      )}
    </Card>
  );
}
