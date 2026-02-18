import { Link } from 'react-router-dom';
import { Heart, Trophy, Brain, Shield } from 'lucide-react';
import { Card } from '../ui';

const BELT_COLORS: Record<string, string> = {
  white: '#E5E7EB',
  blue: '#3B82F6',
  purple: '#8B5CF6',
  brown: '#92400E',
  black: '#1F2937',
};

const COMPETITION_RULESETS = [
  { id: 'none', label: 'No Preference' },
  { id: 'ibjjf', label: 'IBJJF' },
  { id: 'adcc', label: 'ADCC' },
  { id: 'sub_only', label: 'Sub Only' },
  { id: 'naga', label: 'NAGA' },
  { id: 'other', label: 'Other' },
];

const TRAINING_MODES = [
  { id: 'lifestyle', label: 'Lifestyle & Health', icon: Heart, desc: 'Training for enjoyment, fitness, and longevity' },
  { id: 'competition_prep', label: 'Competition Prep', icon: Trophy, desc: 'Peaking for a specific event' },
  { id: 'skill_development', label: 'Skill Development', icon: Brain, desc: 'Focused on technical growth' },
  { id: 'recovery', label: 'Recovery', icon: Shield, desc: 'Coming back from injury or overtraining' },
];

const COACHING_STYLES = [
  { id: 'balanced', label: 'Balanced' },
  { id: 'motivational', label: 'Motivational' },
  { id: 'analytical', label: 'Analytical' },
  { id: 'tough_love', label: 'Tough Love' },
  { id: 'technical', label: 'Technical' },
];

const FOCUS_AREAS = [
  'guard', 'passing', 'takedowns', 'leg_locks', 'back_attacks',
  'submissions', 'escapes', 'sweeps', 'pressure', 'wrestling',
];

const FOCUS_LABELS: Record<string, string> = {
  guard: 'Guard', passing: 'Passing', takedowns: 'Takedowns',
  leg_locks: 'Leg Locks', back_attacks: 'Back Attacks',
  submissions: 'Submissions', escapes: 'Escapes', sweeps: 'Sweeps',
  pressure: 'Pressure', wrestling: 'Wrestling',
};

const MOTIVATIONS = [
  { id: 'fitness', label: 'Fitness' },
  { id: 'competition', label: 'Competition' },
  { id: 'self_defense', label: 'Self-Defense' },
  { id: 'social', label: 'Social' },
  { id: 'mental_health', label: 'Mental Health' },
  { id: 'fun', label: 'Fun' },
];

export interface CoachSettingsFormProps {
  currentGrade: string;
  trainingMode: string;
  onTrainingModeChange: (mode: string) => void;
  compDate: string;
  onCompDateChange: (date: string) => void;
  compName: string;
  onCompNameChange: (name: string) => void;
  compDivision: string;
  onCompDivisionChange: (division: string) => void;
  compWeightClass: string;
  onCompWeightClassChange: (wc: string) => void;
  competitionRuleset: string;
  onCompetitionRulesetChange: (rs: string) => void;
  coachingStyle: string;
  onCoachingStyleChange: (style: string) => void;
  giNogiPreference: string;
  onGiNogiPreferenceChange: (pref: string) => void;
  giBiasPct: number;
  onGiBiasPctChange: (pct: number) => void;
  primaryPosition: string;
  onPrimaryPositionChange: (pos: string) => void;
  focusAreas: string[];
  onToggleFocusArea: (area: string) => void;
  weaknesses: string;
  onWeaknessesChange: (val: string) => void;
  trainingStartDate: string;
  onTrainingStartDateChange: (date: string) => void;
  yearsTraining: string;
  onYearsTrainingChange: (val: string) => void;
  competitionExp: string;
  onCompetitionExpChange: (val: string) => void;
  availableDays: string;
  onAvailableDaysChange: (val: string) => void;
  motivations: string[];
  onToggleMotivation: (m: string) => void;
  additionalContext: string;
  onAdditionalContextChange: (val: string) => void;
  daysUntilComp: number | null;
}

export default function CoachSettingsForm({
  currentGrade,
  trainingMode,
  onTrainingModeChange,
  compDate,
  onCompDateChange,
  compName,
  onCompNameChange,
  compDivision,
  onCompDivisionChange,
  compWeightClass,
  onCompWeightClassChange,
  competitionRuleset,
  onCompetitionRulesetChange,
  coachingStyle,
  onCoachingStyleChange,
  giNogiPreference,
  onGiNogiPreferenceChange,
  giBiasPct,
  onGiBiasPctChange,
  primaryPosition,
  onPrimaryPositionChange,
  focusAreas,
  onToggleFocusArea,
  weaknesses,
  onWeaknessesChange,
  trainingStartDate,
  onTrainingStartDateChange,
  yearsTraining,
  onYearsTrainingChange,
  competitionExp,
  onCompetitionExpChange,
  availableDays,
  onAvailableDaysChange,
  motivations,
  onToggleMotivation,
  additionalContext,
  onAdditionalContextChange,
  daysUntilComp,
}: CoachSettingsFormProps) {
  return (
    <>
      {/* 1. Your Belt (read-only from Profile) */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Your Belt</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Grapple adapts its coaching depth and terminology to your level</p>
        {currentGrade ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-3 rounded-sm"
                style={{
                  backgroundColor: BELT_COLORS[currentGrade.toLowerCase().split(' ')[0]] || '#9CA3AF',
                  border: currentGrade.toLowerCase().startsWith('white') ? '1px solid var(--border)' : 'none',
                }}
              />
              <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{currentGrade}</span>
            </div>
            <Link to="/profile" className="text-xs hover:underline" style={{ color: 'var(--accent)' }}>
              Update in Profile
            </Link>
          </div>
        ) : (
          <Link to="/profile" className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>Set your belt in Profile to personalise coaching</span>
            <span className="text-xs font-medium" style={{ color: 'var(--accent)' }}>Set up</span>
          </Link>
        )}
      </Card>

      {/* 2. Training Mode */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Training Mode</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {TRAINING_MODES.map(mode => {
            const Icon = mode.icon;
            const selected = trainingMode === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => onTrainingModeChange(mode.id)}
                className="flex items-start gap-3 p-3 rounded-xl text-left transition-all"
                style={{
                  backgroundColor: selected ? 'var(--accent)' + '15' : 'var(--surfaceElev)',
                  border: selected ? '2px solid var(--accent)' : '2px solid transparent',
                }}
              >
                <Icon className="w-5 h-5 mt-0.5 shrink-0" style={{ color: selected ? 'var(--accent)' : 'var(--muted)' }} />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{mode.label}</p>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>{mode.desc}</p>
                </div>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Competition Details (conditional) */}
      {trainingMode === 'competition_prep' && (
        <Card className="p-5">
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Competition Details
            {daysUntilComp != null && daysUntilComp > 0 && (
              <span className="ml-2 text-xs font-bold px-2 py-0.5 rounded" style={{ backgroundColor: daysUntilComp <= 14 ? 'var(--danger-bg)' : 'var(--warning-bg)', color: daysUntilComp <= 14 ? 'var(--danger)' : 'var(--warning)' }}>
                {daysUntilComp} days
              </span>
            )}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Competition Name</label>
              <input className="input w-full text-sm" placeholder="e.g. IBJJF Sydney Open" value={compName} onChange={e => onCompNameChange(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Date</label>
              <input type="date" className="input w-full text-sm" value={compDate} onChange={e => onCompDateChange(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Division</label>
              <select className="input w-full text-sm" value={compDivision} onChange={e => onCompDivisionChange(e.target.value)}>
                <option value="">Select...</option>
                <option value="gi">Gi</option>
                <option value="no-gi">No-Gi</option>
                <option value="both">Both</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Weight Class</label>
              <input className="input w-full text-sm" placeholder="e.g. Medium Heavy" value={compWeightClass} onChange={e => onCompWeightClassChange(e.target.value)} />
            </div>
          </div>
        </Card>
      )}

      {/* Competition Ruleset */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Competition Ruleset</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Grapple adjusts strategy advice based on the rules you compete under</p>
        <div className="flex flex-wrap gap-2">
          {COMPETITION_RULESETS.map(rs => (
            <button
              key={rs.id}
              onClick={() => onCompetitionRulesetChange(rs.id)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
              style={{
                backgroundColor: competitionRuleset === rs.id ? 'var(--accent)' : 'var(--surfaceElev)',
                color: competitionRuleset === rs.id ? '#fff' : 'var(--text)',
              }}
            >
              {rs.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Coaching Style */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Coaching Style</h2>
        <div className="flex flex-wrap gap-2">
          {COACHING_STYLES.map(style => (
            <button
              key={style.id}
              onClick={() => onCoachingStyleChange(style.id)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
              style={{
                backgroundColor: coachingStyle === style.id ? 'var(--accent)' : 'var(--surfaceElev)',
                color: coachingStyle === style.id ? '#fff' : 'var(--text)',
              }}
            >
              {style.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Gi / No-Gi Preference */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Gi / No-Gi Preference</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Grapple skews technique recommendations based on your preference</p>
        <div className="flex gap-2 mb-3">
          {[
            { id: 'gi_only', label: 'Gi Only' },
            { id: 'both', label: 'Both' },
            { id: 'nogi_only', label: 'No-Gi Only' },
          ].map((opt) => (
            <button
              key={opt.id}
              onClick={() => onGiNogiPreferenceChange(opt.id)}
              className="flex-1 py-2 rounded-lg text-xs font-medium transition-all"
              style={{
                backgroundColor: giNogiPreference === opt.id ? 'var(--accent)' : 'var(--surfaceElev)',
                color: giNogiPreference === opt.id ? '#fff' : 'var(--text)',
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {giNogiPreference === 'both' && (
          <div>
            <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--muted)' }}>
              <span>No-Gi</span>
              <span>{giBiasPct}% Gi / {100 - giBiasPct}% No-Gi</span>
              <span>Gi</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={giBiasPct}
              onChange={(e) => onGiBiasPctChange(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        )}
      </Card>

      {/* Your Game */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Your Game</h2>

        <div className="mb-4">
          <label className="text-xs font-medium block mb-2" style={{ color: 'var(--muted)' }}>Primary Position</label>
          <div className="flex gap-2">
            {['top', 'bottom', 'both'].map(pos => (
              <button
                key={pos}
                onClick={() => onPrimaryPositionChange(pos)}
                className="flex-1 py-2 rounded-lg text-xs font-medium transition-all"
                style={{
                  backgroundColor: primaryPosition === pos ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: primaryPosition === pos ? '#fff' : 'var(--text)',
                }}
              >
                {pos.charAt(0).toUpperCase() + pos.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="text-xs font-medium block mb-2" style={{ color: 'var(--muted)' }}>Focus Areas</label>
          <div className="flex flex-wrap gap-2">
            {FOCUS_AREAS.map(area => (
              <button
                key={area}
                onClick={() => onToggleFocusArea(area)}
                className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                style={{
                  backgroundColor: focusAreas.includes(area) ? 'var(--accent)' + '20' : 'var(--surfaceElev)',
                  color: focusAreas.includes(area) ? 'var(--accent)' : 'var(--text)',
                  border: focusAreas.includes(area) ? '1px solid var(--accent)' : '1px solid transparent',
                }}
              >
                {FOCUS_LABELS[area]}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>What do you want to improve?</label>
          <textarea
            className="input w-full text-sm"
            rows={2}
            placeholder="e.g. my guard retention under pressure, staying calm in bottom side control..."
            value={weaknesses}
            onChange={e => onWeaknessesChange(e.target.value)}
          />
        </div>
      </Card>

      {/* Training Background */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Training Background</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Fill in one or both — if you took breaks, add your active mat time separately</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>When did you start?</label>
            <input
              type="date"
              className="input w-full text-sm"
              value={trainingStartDate}
              onChange={e => onTrainingStartDateChange(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Active mat time (years)</label>
            <input
              type="number"
              className="input w-full text-sm"
              placeholder="e.g. 3.5 — leave blank to auto-calculate"
              step="0.5"
              min="0"
              value={yearsTraining}
              onChange={e => onYearsTrainingChange(e.target.value)}
            />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Comp Experience</label>
            <select className="input w-full text-sm" value={competitionExp} onChange={e => onCompetitionExpChange(e.target.value)}>
              <option value="none">None</option>
              <option value="beginner">Beginner (1-3)</option>
              <option value="regular">Regular (4-10)</option>
              <option value="active">Active (10+)</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Days / Week</label>
            <input
              type="number"
              className="input w-full text-sm"
              min="1"
              max="7"
              value={availableDays}
              onChange={e => onAvailableDaysChange(e.target.value)}
            />
          </div>
        </div>
      </Card>

      {/* Why You Train */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Why Do You Train?</h2>
        <div className="flex flex-wrap gap-2">
          {MOTIVATIONS.map(m => (
            <button
              key={m.id}
              onClick={() => onToggleMotivation(m.id)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
              style={{
                backgroundColor: motivations.includes(m.id) ? 'var(--accent)' + '20' : 'var(--surfaceElev)',
                color: motivations.includes(m.id) ? 'var(--accent)' : 'var(--text)',
                border: motivations.includes(m.id) ? '1px solid var(--accent)' : '1px solid transparent',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Anything Else */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Anything Else?</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Tell Grapple anything else about you or your training</p>
        <textarea
          className="input w-full text-sm"
          rows={3}
          placeholder="e.g. I have a desk job and sit 8 hours a day, I'm left-handed, I recently switched gyms..."
          value={additionalContext}
          onChange={e => onAdditionalContextChange(e.target.value)}
        />
      </Card>
    </>
  );
}
