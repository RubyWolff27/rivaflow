import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Info, Moon } from 'lucide-react';
import { Card, PrimaryButton } from '../ui';
import type { PhysiologySnapshot } from '../../hooks/useDashboardData';

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
  physiology: PhysiologySnapshot | null;
}

const READINESS_HIGH_THRESHOLD = 16;
const READINESS_MODERATE_THRESHOLD = 12;

/** One decision per state (DES-F2/F3) — vocabulary from the physiology spine. */
const STATE_VERDICTS: Record<string, { label: string; bg: string; color: string }> = {
  Prime: { label: 'Train Hard', bg: 'var(--success-bg)', color: 'var(--success)' },
  Balanced: { label: 'Train as Planned', bg: 'var(--success-bg)', color: 'var(--success)' },
  Strained: { label: 'Technical Day', bg: 'var(--warning-bg)', color: 'var(--warning)' },
  Rundown: { label: 'Recovery Day', bg: 'var(--danger-bg)', color: 'var(--danger)' },
  Rest: { label: 'Rest Day', bg: 'var(--surfaceElev)', color: 'var(--muted)' },
  Building: { label: 'Building Baseline', bg: 'var(--surfaceElev)', color: 'var(--muted)' },
};

const BAND_COLORS: Record<string, string> = {
  green: '#10B981',
  yellow: '#F59E0B',
  red: '#EF4444',
};

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
  physiology,
}: HeroScoreProps) {
  const navigate = useNavigate();
  const [showReadinessInfo, setShowReadinessInfo] = useState(false);
  const [expandedRule, setExpandedRule] = useState<string | null>(null);

  const verdict = physiology?.readiness;
  const hubScore = verdict?.score ?? null;
  const state = verdict?.state ?? null;
  const debt = physiology?.sleep_debt;

  // ONE ring, ONE scale (DES-F3): the hub verdict 0-100. Fallback when the hub
  // is quiet: the /20 check-in (clearly labeled Check-in, never "Readiness").
  let centerValue: number | null = null;
  let centerMax = 100;
  let centerLabel = 'Check In';
  let centerSub = 'Readiness';
  let centerColor = 'var(--accent)';
  let centerPulsing = false;

  if (hubScore != null) {
    centerValue = hubScore;
    centerLabel = String(hubScore);
    centerSub = 'Readiness';
    centerColor = BAND_COLORS[verdict?.band ?? ''] ?? 'var(--accent)';
  } else if (hasCheckedIn && readinessScore != null) {
    centerValue = readinessScore;
    centerMax = 20;
    centerLabel = `${readinessScore}/20`;
    centerSub = 'Check-in';
    centerColor =
      readinessScore >= READINESS_HIGH_THRESHOLD
        ? '#10B981'
        : readinessScore >= READINESS_MODERATE_THRESHOLD
          ? '#F59E0B'
          : '#EF4444';
  } else {
    centerPulsing = true;
    centerSub = 'Check-in';
  }

  // The one decision.
  const stateVerdict = state ? STATE_VERDICTS[state] : null;
  const label = stateVerdict?.label
    ?? (hasCheckedIn
      ? (readinessScore ?? 0) >= READINESS_HIGH_THRESHOLD
        ? 'Train Hard'
        : (readinessScore ?? 0) >= READINESS_MODERATE_THRESHOLD
          ? 'Light Session'
          : 'Rest Day'
      : 'Check In');
  const labelBg = stateVerdict?.bg
    ?? (hasCheckedIn ? 'var(--warning-bg)' : 'var(--surfaceElev)');
  const labelColor = stateVerdict?.color
    ?? (hasCheckedIn ? 'var(--warning)' : 'var(--accent)');

  const debtLine =
    debt?.available && (debt.debt_hours ?? 0) > 0.5
      ? `Sleep debt ${debt.debt_hours}h${debt.tonight_recommended_hours != null ? ` — aim ${debt.tonight_recommended_hours}h tonight` : ''}`
      : null;

  return (
    <Card variant="hero">
      {/* One ring (DES-F2): the decision owns the hero */}
      <div className="flex flex-col items-center">
        <div
          className="flex flex-col items-center gap-1 cursor-pointer"
          onClick={() => navigate(hubScore != null ? '/health' : '/readiness')}
        >
          <ScoreGauge
            value={centerValue}
            max={centerMax}
            size={130}
            strokeWidth={9}
            color={centerColor}
            pulsing={centerPulsing}
          >
            <span className="text-3xl font-bold" style={{ color: 'var(--text)' }}>
              {centerLabel}
            </span>
          </ScoreGauge>
          <span className="flex items-center gap-1 text-[11px] font-medium" style={{ color: 'var(--muted)' }}>
            {centerSub}
            <button
              onClick={(e) => { e.stopPropagation(); setShowReadinessInfo(!showReadinessInfo); }}
              className="p-0.5 rounded-full hover:opacity-80"
              aria-label="What is readiness?"
            >
              <Info className="w-3 h-3" />
            </button>
          </span>
        </div>
        {verdict?.headline && (
          <p className="text-xs mt-1 text-center max-w-md" style={{ color: 'var(--muted)' }}>
            {verdict.headline}
          </p>
        )}
        {debtLine && (
          <p className="flex items-center gap-1 text-xs mt-1" style={{ color: 'var(--warning)' }}>
            <Moon className="w-3 h-3" />
            {debtLine}
          </p>
        )}
      </div>

      {/* Readiness info tooltip */}
      {showReadinessInfo && (
        <p className="text-xs text-center mt-2 px-4 py-2 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}>
          Readiness (0–100) is measured from your body — HRV, resting HR and sleep vs your own baselines. The 0–20 Check-in is how you FEEL; both feed today's advice.
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
        ) : !hasCheckedIn && hubScore == null ? (
          <p className="text-sm mt-1.5" style={{ color: 'var(--muted)' }}>
            Check in for personalized training guidance
          </p>
        ) : null}

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

      {/* Symptom check-in — secondary, never called readiness (DES-F3) */}
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
          How do you feel? Daily check-in
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
