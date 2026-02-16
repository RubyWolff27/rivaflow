import { useNavigate } from 'react-router-dom';
import { Activity, RefreshCw, Waves, Heart } from 'lucide-react';
import { Card, PrimaryButton } from '../ui';

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

interface WhoopRecovery {
  recovery_score: number | null;
  hrv_ms: number | null;
  resting_hr: number | null;
}

interface HeroScoreProps {
  readinessScore: number | null;
  whoopRecovery: WhoopRecovery | null;
  hasCheckedIn: boolean;
  suggestion: SuggestionData | null;
  whoopSyncing: boolean;
  onSyncWhoop: () => void;
}

const READINESS_HIGH_THRESHOLD = 16;
const READINESS_MODERATE_THRESHOLD = 12;
const WHOOP_RECOVERY_HIGH = 67;
const WHOOP_RECOVERY_MODERATE = 34;

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

// SVG circular gauge
function ScoreGauge({
  value,
  max,
  label,
  color,
  pulsing,
}: {
  value: number | null;
  max: number;
  label: string;
  color: string;
  pulsing?: boolean;
}) {
  const size = 120;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = value != null ? Math.min(value / max, 1) : 0;
  const dashOffset = circumference * (1 - progress);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
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
        <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
          {label}
        </span>
      </div>
    </div>
  );
}

export default function HeroScore({
  readinessScore,
  whoopRecovery,
  hasCheckedIn,
  suggestion,
  whoopSyncing,
  onSyncWhoop,
}: HeroScoreProps) {
  const navigate = useNavigate();
  const score = readinessScore ?? 0;

  // Determine label + colors (exact logic from DailyActionHero)
  let label: string;
  let labelBg: string;
  let labelColor: string;

  if (!hasCheckedIn && !whoopRecovery) {
    label = 'Check In';
    labelBg = 'var(--surfaceElev)';
    labelColor = 'var(--accent)';
  } else if (
    score >= READINESS_HIGH_THRESHOLD ||
    (whoopRecovery &&
      whoopRecovery.recovery_score !== null &&
      whoopRecovery.recovery_score >= WHOOP_RECOVERY_HIGH &&
      !hasCheckedIn)
  ) {
    label = 'Train Hard';
    labelBg = 'var(--success-bg)';
    labelColor = 'var(--success)';
  } else if (
    score >= READINESS_MODERATE_THRESHOLD ||
    (whoopRecovery &&
      whoopRecovery.recovery_score !== null &&
      whoopRecovery.recovery_score >= WHOOP_RECOVERY_MODERATE &&
      !hasCheckedIn)
  ) {
    label = 'Light Session';
    labelBg = 'var(--warning-bg)';
    labelColor = 'var(--warning)';
  } else {
    label = 'Rest Day';
    labelBg = 'var(--danger-bg)';
    labelColor = 'var(--danger)';
  }

  // Gauge display logic
  let gaugeValue: number | null = null;
  let gaugeMax = 20;
  let gaugeLabel = 'Check In';
  let gaugeColor = 'var(--accent)';
  let pulsing = false;

  if (hasCheckedIn && readinessScore != null) {
    gaugeValue = readinessScore;
    gaugeMax = 20;
    gaugeLabel = `${readinessScore}/20`;
    gaugeColor =
      readinessScore >= READINESS_HIGH_THRESHOLD
        ? '#10B981'
        : readinessScore >= READINESS_MODERATE_THRESHOLD
          ? '#F59E0B'
          : '#EF4444';
  } else if (whoopRecovery && whoopRecovery.recovery_score != null) {
    gaugeValue = whoopRecovery.recovery_score;
    gaugeMax = 100;
    gaugeLabel = `${Math.round(whoopRecovery.recovery_score)}%`;
    gaugeColor =
      whoopRecovery.recovery_score >= WHOOP_RECOVERY_HIGH
        ? '#10B981'
        : whoopRecovery.recovery_score >= WHOOP_RECOVERY_MODERATE
          ? '#F59E0B'
          : '#EF4444';
  } else {
    pulsing = true;
  }

  return (
    <Card variant="hero">
      <div className="flex items-center gap-5">
        {/* Circular gauge */}
        <div
          className="shrink-0 cursor-pointer"
          onClick={() => navigate('/readiness')}
        >
          <ScoreGauge
            value={gaugeValue}
            max={gaugeMax}
            label={gaugeLabel}
            color={gaugeColor}
            pulsing={pulsing}
          />
        </div>

        {/* Right side: label + suggestion */}
        <div className="flex-1 min-w-0">
          <span
            className="inline-block text-sm font-bold uppercase tracking-wide px-2.5 py-1 rounded-md mb-2"
            style={{ backgroundColor: labelBg, color: labelColor }}
          >
            {label}
          </span>

          {suggestion?.suggestion ? (
            <p
              className="text-sm line-clamp-2"
              style={{ color: 'var(--muted)' }}
            >
              {sanitizeSuggestion(suggestion.suggestion)}
            </p>
          ) : !hasCheckedIn && !whoopRecovery ? (
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Check in for personalized training guidance
            </p>
          ) : (
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Based on your readiness score of {score}/20
            </p>
          )}

          {/* Triggered rule chips */}
          {suggestion?.triggered_rules &&
            suggestion.triggered_rules.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {suggestion.triggered_rules.slice(0, 3).map((rule, i) => (
                  <span
                    key={i}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: 'var(--surfaceElev)',
                      color: 'var(--muted)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    {RULE_LABELS[rule.name] || rule.name.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
        </div>
      </div>

      {/* WHOOP recovery secondary stats */}
      {whoopRecovery && (hasCheckedIn || whoopRecovery.recovery_score != null) && (
        <div
          className="flex items-center gap-4 mt-4 p-2.5 rounded-lg"
          style={{ backgroundColor: 'var(--surfaceElev)' }}
        >
          {/* WHOOP badge (only show if readiness is primary) */}
          {hasCheckedIn && readinessScore != null && whoopRecovery.recovery_score != null && (
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-black flex items-center justify-center shrink-0">
                <span className="text-white font-bold text-[10px]">W</span>
              </div>
              <span
                className="text-sm font-semibold"
                style={{
                  color:
                    whoopRecovery.recovery_score >= WHOOP_RECOVERY_HIGH
                      ? '#10B981'
                      : whoopRecovery.recovery_score >= WHOOP_RECOVERY_MODERATE
                        ? '#F59E0B'
                        : '#EF4444',
                }}
              >
                {Math.round(whoopRecovery.recovery_score)}%
              </span>
            </div>
          )}

          {/* HRV + RHR (desktop only) */}
          <div className="hidden sm:flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
            {whoopRecovery.hrv_ms != null && (
              <div className="flex items-center gap-1">
                <Waves className="w-3 h-3" style={{ color: 'var(--accent)' }} />
                <span className="font-semibold" style={{ color: 'var(--text)' }}>
                  {Math.round(whoopRecovery.hrv_ms)}
                </span>
                <span>HRV</span>
              </div>
            )}
            {whoopRecovery.resting_hr != null && (
              <div className="flex items-center gap-1">
                <Heart className="w-3 h-3" style={{ color: 'var(--accent)' }} />
                <span className="font-semibold" style={{ color: 'var(--text)' }}>
                  {Math.round(whoopRecovery.resting_hr)}
                </span>
                <span>RHR</span>
              </div>
            )}
          </div>

          <div className="flex-1" />

          <button
            onClick={onSyncWhoop}
            disabled={whoopSyncing}
            className="p-1.5 rounded-md hover:opacity-80 shrink-0"
            style={{ color: 'var(--muted)' }}
            title="Sync WHOOP"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${whoopSyncing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      )}

      {/* Not checked in prompt */}
      {!hasCheckedIn && !whoopRecovery && (
        <button
          onClick={() => navigate('/readiness')}
          className="w-full mt-4 py-2.5 rounded-lg text-sm font-semibold transition-colors"
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

      {/* Full-width Log Session CTA */}
      <PrimaryButton
        onClick={() => navigate('/log')}
        className="w-full mt-4 py-4 text-base font-bold"
      >
        + Log Session
      </PrimaryButton>
    </Card>
  );
}
