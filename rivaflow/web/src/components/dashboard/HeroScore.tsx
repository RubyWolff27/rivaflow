import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Flame, Info } from 'lucide-react';
import { Card, PrimaryButton } from '../ui';
import type { WeeklyGoalProgress, StreakStatus } from '../../types';

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

interface HeroScoreProps {
  readinessScore: number | null;
  hasCheckedIn: boolean;
  suggestion: SuggestionData | null;
  weeklyGoals: WeeklyGoalProgress | null;
  streaks: StreakStatus | null;
}

const READINESS_HIGH_THRESHOLD = 16;
const READINESS_MODERATE_THRESHOLD = 12;

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

function ScoreGauge({
  value,
  max,
  size,
  strokeWidth,
  color,
  pulsing,
  children,
}: {
  value: number | null;
  max: number;
  size: number;
  strokeWidth: number;
  color: string;
  pulsing?: boolean;
  children: React.ReactNode;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = value != null ? Math.min(value / max, 1) : 0;
  const dashOffset = circumference * (1 - progress);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className={`score-ring ${pulsing ? 'animate-pulse' : ''}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  );
}

export default function HeroScore({
  readinessScore,
  hasCheckedIn,
  suggestion,
  weeklyGoals,
  streaks,
}: HeroScoreProps) {
  const navigate = useNavigate();
  const [showReadinessInfo, setShowReadinessInfo] = useState(false);
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const score = readinessScore ?? 0;

  // Determine label + colors (exact logic from DailyActionHero)
  let label: string;
  let labelBg: string;
  let labelColor: string;

  if (!hasCheckedIn) {
    label = 'Check In';
    labelBg = 'var(--surfaceElev)';
    labelColor = 'var(--accent)';
  } else if (score >= READINESS_HIGH_THRESHOLD) {
    label = 'Train Hard';
    labelBg = 'var(--success-bg)';
    labelColor = 'var(--success)';
  } else if (score >= READINESS_MODERATE_THRESHOLD) {
    label = 'Light Session';
    labelBg = 'var(--warning-bg)';
    labelColor = 'var(--warning)';
  } else {
    label = 'Rest Day';
    labelBg = 'var(--danger-bg)';
    labelColor = 'var(--danger)';
  }

  // Center gauge: readiness or pulsing check-in prompt
  let centerValue: number | null = null;
  let centerMax = 20;
  let centerLabel = 'Check In';
  let centerColor = 'var(--accent)';
  let centerPulsing = false;

  if (hasCheckedIn && readinessScore != null) {
    centerValue = readinessScore;
    centerMax = 20;
    centerLabel = `${readinessScore}/20`;
    centerColor =
      readinessScore >= READINESS_HIGH_THRESHOLD
        ? '#10B981'
        : readinessScore >= READINESS_MODERATE_THRESHOLD
          ? '#F59E0B'
          : '#EF4444';
  } else {
    centerPulsing = true;
  }

  // Left gauge: check-in streak
  const streakCount = streaks?.checkin.current_streak ?? 0;
  const leftValue = streakCount;
  const leftMax = Math.max(streakCount, 1);
  const leftColor = streakCount > 0 ? 'var(--accent)' : 'var(--border)';
  const leftLabel = '';
  const leftSublabel = 'Streak';
  const leftIcon: React.ReactNode = (
    <div className="flex items-center gap-0.5">
      <Flame className="w-3 h-3" style={{ color: 'var(--accent)' }} />
      <span className="text-xs font-bold" style={{ color: 'var(--text)' }}>
        {streakCount}
      </span>
    </div>
  );

  // Right gauge: BJJ sessions (fall back to total sessions)
  const bjjActual = weeklyGoals?.actual?.bjj_sessions ?? 0;
  const bjjTarget = weeklyGoals?.targets?.bjj_sessions ?? 0;
  const totalActual = weeklyGoals?.actual?.sessions ?? 0;
  const totalTarget = weeklyGoals?.targets?.sessions ?? 0;

  // Use BJJ-specific if target exists, otherwise fall back to total
  const useBjj = bjjTarget > 0;
  const rightActual = useBjj ? bjjActual : totalActual;
  const rightTarget = useBjj ? bjjTarget : (totalTarget > 0 ? totalTarget : 4);
  const rightComplete = rightTarget > 0 && rightActual >= rightTarget;
  const rightColor = rightComplete ? 'var(--success)' : 'var(--accent)';
  const rightSublabel = useBjj ? 'BJJ' : 'Sessions';

  return (
    <Card variant="hero">
      {/* Triple gauge row */}
      <div className="flex items-center justify-center gap-3 sm:gap-6">
        {/* Left ring: WHOOP or Streak */}
        <div className="flex flex-col items-center gap-1">
          <ScoreGauge
            value={leftValue}
            max={leftMax}
            size={56}
            strokeWidth={4}
            color={leftColor}
          >
            {leftIcon || (
              <span className="text-[11px] font-bold" style={{ color: 'var(--text)' }}>
                {leftLabel}
              </span>
            )}
          </ScoreGauge>
          <span className="text-[10px] font-medium" style={{ color: 'var(--muted)' }}>
            {leftSublabel}
          </span>
        </div>

        {/* Center ring: Readiness (dominant) */}
        <div
          className="flex flex-col items-center gap-1 cursor-pointer"
          onClick={() => navigate('/readiness')}
        >
          <ScoreGauge
            value={centerValue}
            max={centerMax}
            size={120}
            strokeWidth={8}
            color={centerColor}
            pulsing={centerPulsing}
          >
            <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
              {centerLabel}
            </span>
          </ScoreGauge>
          <span className="flex items-center gap-1 text-[10px] font-medium" style={{ color: 'var(--muted)' }}>
            Check-in
            <button
              onClick={(e) => { e.stopPropagation(); setShowReadinessInfo(!showReadinessInfo); }}
              className="p-0.5 rounded-full hover:opacity-80"
              aria-label="What is the check-in score?"
            >
              <Info className="w-3 h-3" />
            </button>
          </span>
        </div>

        {/* Right ring: BJJ Sessions */}
        <div className="flex flex-col items-center gap-1">
          <ScoreGauge
            value={rightActual}
            max={rightTarget}
            size={56}
            strokeWidth={4}
            color={rightColor}
          >
            <span className="text-[11px] font-bold" style={{ color: 'var(--text)' }}>
              {rightActual}/{rightTarget}
            </span>
          </ScoreGauge>
          <span className="text-[10px] font-medium" style={{ color: 'var(--muted)' }}>
            {rightSublabel}
          </span>
        </div>
      </div>

      {/* Readiness info tooltip */}
      {showReadinessInfo && (
        <p className="text-xs text-center mt-2 px-4 py-2 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}>
          Check-in (0–20) is how you FEEL — stress, energy, soreness, sleep. The Readiness verdict on the Health tab is measured from your body (HRV, RHR, sleep).
        </p>
      )}

      {/* Label badge + suggestion */}
      <div className="text-center mt-3">
        <span
          className="inline-block text-sm font-bold uppercase tracking-wide px-2.5 py-1 rounded-md"
          style={{ backgroundColor: labelBg, color: labelColor }}
        >
          {label}
        </span>

        {suggestion?.suggestion ? (
          <p className="text-sm font-medium mt-1.5 line-clamp-2 mx-auto max-w-md" style={{ color: 'var(--text)' }}>
            {sanitizeSuggestion(suggestion.suggestion)}
          </p>
        ) : !hasCheckedIn ? (
          <p className="text-sm mt-1.5" style={{ color: 'var(--muted)' }}>
            Check in for personalized training guidance
          </p>
        ) : (
          <p className="text-sm mt-1.5" style={{ color: 'var(--muted)' }}>
            Based on your check-in score of {score}/20
          </p>
        )}

        {/* Triggered rule chips */}
        {suggestion?.triggered_rules?.length ? (
          <div className="flex flex-wrap justify-center items-center gap-1.5 mt-2">
            {suggestion.triggered_rules.slice(0, 3).map((rule, i) => (
              <button
                key={i}
                className="text-xs px-2 py-0.5 rounded-full transition-colors"
                style={{
                  backgroundColor: expandedRule === rule.name ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: expandedRule === rule.name ? '#FFFFFF' : 'var(--muted)',
                  border: expandedRule === rule.name ? 'none' : '1px solid var(--border)',
                }}
                onClick={() => setExpandedRule(expandedRule === rule.name ? null : rule.name)}
              >
                {RULE_LABELS[rule.name] || rule.name.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        ) : null}

        {/* Expanded rule recommendation */}
        {expandedRule && suggestion?.triggered_rules?.find(r => r.name === expandedRule) && (
          <p className="text-xs mt-2 px-3 py-2 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}>
            {suggestion!.triggered_rules!.find(r => r.name === expandedRule)!.recommendation}
          </p>
        )}
      </div>

      {/* Not checked in prompt */}
      {!hasCheckedIn && (
        <button
          onClick={() => navigate('/readiness')}
          className="w-full mt-3 py-2.5 rounded-lg text-sm font-semibold transition-colors"
          style={{
            backgroundColor: 'var(--surfaceElev)',
            color: 'var(--accent)',
            border: '1px solid var(--border)',
          }}
        >
          <Activity className="w-4 h-4 inline mr-1.5 -mt-0.5" />
          Daily Check-in
        </button>
      )}

      {/* Log Session CTA */}
      <div className="flex justify-center mt-3">
        <PrimaryButton
          onClick={() => navigate('/log')}
          className="w-3/4 sm:w-2/3 py-3 text-sm font-bold"
        >
          + Log Session
        </PrimaryButton>
      </div>
    </Card>
  );
}
