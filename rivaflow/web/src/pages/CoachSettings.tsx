import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Trophy, Heart, Brain, Shield, Plus, X } from 'lucide-react';
import { Card, PrimaryButton } from '../components/ui';
import { coachPreferencesApi } from '../api/client';
import { useToast } from '../contexts/ToastContext';

interface Injury {
  area: string;
  side: string;
  severity: string;
  notes: string;
}

const BELT_LEVELS = [
  { id: 'white', label: 'White', color: '#E5E7EB' },
  { id: 'blue', label: 'Blue', color: '#3B82F6' },
  { id: 'purple', label: 'Purple', color: '#8B5CF6' },
  { id: 'brown', label: 'Brown', color: '#92400E' },
  { id: 'black', label: 'Black', color: '#1F2937' },
];

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

const INJURY_AREAS = [
  'knee', 'shoulder', 'back', 'neck', 'elbow', 'wrist',
  'ankle', 'hip', 'ribs', 'fingers', 'other',
];

const INJURY_SIDES = ['left', 'right', 'both', 'n/a'];
const INJURY_SEVERITIES = ['mild', 'moderate', 'severe'];

export default function CoachSettings() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [beltLevel, setBeltLevel] = useState('white');
  const [competitionRuleset, setCompetitionRuleset] = useState('none');
  const [trainingMode, setTrainingMode] = useState('lifestyle');
  const [compDate, setCompDate] = useState('');
  const [compName, setCompName] = useState('');
  const [compDivision, setCompDivision] = useState('');
  const [compWeightClass, setCompWeightClass] = useState('');
  const [coachingStyle, setCoachingStyle] = useState('balanced');
  const [primaryPosition, setPrimaryPosition] = useState('both');
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [weaknesses, setWeaknesses] = useState('');
  const [injuries, setInjuries] = useState<Injury[]>([]);
  const [yearsTraining, setYearsTraining] = useState('');
  const [competitionExp, setCompetitionExp] = useState('none');
  const [availableDays, setAvailableDays] = useState('4');
  const [motivations, setMotivations] = useState<string[]>([]);
  const [additionalContext, setAdditionalContext] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await coachPreferencesApi.get();
        const d = res.data;
        if (d) {
          setBeltLevel(d.belt_level || 'white');
          setCompetitionRuleset(d.competition_ruleset || 'none');
          setTrainingMode(d.training_mode || 'lifestyle');
          setCompDate(d.comp_date || '');
          setCompName(d.comp_name || '');
          setCompDivision(d.comp_division || '');
          setCompWeightClass(d.comp_weight_class || '');
          setCoachingStyle(d.coaching_style || 'balanced');
          setPrimaryPosition(d.primary_position || 'both');
          setFocusAreas(d.focus_areas || []);
          setWeaknesses(d.weaknesses || '');
          setInjuries(d.injuries || []);
          setYearsTraining(d.years_training != null ? String(d.years_training) : '');
          setCompetitionExp(d.competition_experience || 'none');
          setAvailableDays(d.available_days_per_week != null ? String(d.available_days_per_week) : '4');
          setMotivations(d.motivations || []);
          setAdditionalContext(d.additional_context || '');
        }
      } catch {
        // First time — use defaults
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const toggleFocusArea = (area: string) => {
    setFocusAreas(prev =>
      prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
    );
  };

  const toggleMotivation = (m: string) => {
    setMotivations(prev =>
      prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m]
    );
  };

  const addInjury = () => {
    setInjuries(prev => [...prev, { area: 'knee', side: 'n/a', severity: 'moderate', notes: '' }]);
  };

  const removeInjury = (index: number) => {
    setInjuries(prev => prev.filter((_, i) => i !== index));
  };

  const updateInjury = (index: number, field: keyof Injury, value: string) => {
    setInjuries(prev => prev.map((inj, i) => i === index ? { ...inj, [field]: value } : inj));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await coachPreferencesApi.update({
        belt_level: beltLevel,
        competition_ruleset: competitionRuleset,
        training_mode: trainingMode,
        comp_date: trainingMode === 'competition_prep' ? compDate || null : null,
        comp_name: trainingMode === 'competition_prep' ? compName || null : null,
        comp_division: trainingMode === 'competition_prep' ? compDivision || null : null,
        comp_weight_class: trainingMode === 'competition_prep' ? compWeightClass || null : null,
        coaching_style: coachingStyle,
        primary_position: primaryPosition,
        focus_areas: focusAreas,
        weaknesses: weaknesses || null,
        injuries,
        years_training: yearsTraining ? parseFloat(yearsTraining) : null,
        competition_experience: competitionExp,
        available_days_per_week: parseInt(availableDays) || 4,
        motivations,
        additional_context: additionalContext || null,
      });
      toast.success('Coach preferences saved');
    } catch {
      toast.error('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const daysUntilComp = compDate
    ? Math.ceil((new Date(compDate).getTime() - Date.now()) / 86400000)
    : null;

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[var(--surfaceElev)] rounded w-1/3"></div>
          <div className="h-40 bg-[var(--surfaceElev)] rounded"></div>
          <div className="h-40 bg-[var(--surfaceElev)] rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link to="/grapple" className="flex items-center gap-1 text-sm mb-3 hover:underline" style={{ color: 'var(--accent)' }}>
          <ArrowLeft className="w-4 h-4" /> Back to Grapple
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>Coach Settings</h1>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Personalise how Grapple coaches you</p>
          </div>
        </div>
      </div>

      {/* 1. Belt Level */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Your Belt</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Grapple adapts its coaching depth and terminology to your level</p>
        <div className="flex gap-2">
          {BELT_LEVELS.map(belt => (
            <button
              key={belt.id}
              onClick={() => setBeltLevel(belt.id)}
              className="flex-1 py-3 rounded-xl text-xs font-bold transition-all relative"
              style={{
                backgroundColor: beltLevel === belt.id ? belt.color : 'var(--surfaceElev)',
                color: beltLevel === belt.id
                  ? (belt.id === 'white' ? '#1F2937' : '#fff')
                  : 'var(--text)',
                border: beltLevel === belt.id ? `2px solid ${belt.color}` : '2px solid transparent',
                boxShadow: beltLevel === belt.id ? `0 0 12px ${belt.color}40` : 'none',
              }}
            >
              {belt.label}
            </button>
          ))}
        </div>
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
                onClick={() => setTrainingMode(mode.id)}
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

      {/* 2. Competition Details (conditional) */}
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
              <input className="input w-full text-sm" placeholder="e.g. IBJJF Sydney Open" value={compName} onChange={e => setCompName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Date</label>
              <input type="date" className="input w-full text-sm" value={compDate} onChange={e => setCompDate(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Division</label>
              <select className="input w-full text-sm" value={compDivision} onChange={e => setCompDivision(e.target.value)}>
                <option value="">Select...</option>
                <option value="gi">Gi</option>
                <option value="no-gi">No-Gi</option>
                <option value="both">Both</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Weight Class</label>
              <input className="input w-full text-sm" placeholder="e.g. Medium Heavy" value={compWeightClass} onChange={e => setCompWeightClass(e.target.value)} />
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
              onClick={() => setCompetitionRuleset(rs.id)}
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
              onClick={() => setCoachingStyle(style.id)}
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

      {/* 4. Your Game */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Your Game</h2>

        <div className="mb-4">
          <label className="text-xs font-medium block mb-2" style={{ color: 'var(--muted)' }}>Primary Position</label>
          <div className="flex gap-2">
            {['top', 'bottom', 'both'].map(pos => (
              <button
                key={pos}
                onClick={() => setPrimaryPosition(pos)}
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
                onClick={() => toggleFocusArea(area)}
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
            onChange={e => setWeaknesses(e.target.value)}
          />
        </div>
      </Card>

      {/* 5. Injuries */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Injuries</h2>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Persist across sessions, unlike your daily check-in hotspot</p>
          </div>
          <button
            onClick={addInjury}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--accent)' }}
          >
            <Plus className="w-3.5 h-3.5" /> Add
          </button>
        </div>

        {injuries.length === 0 && (
          <p className="text-xs py-4 text-center" style={{ color: 'var(--muted)' }}>
            No injuries recorded. Grapple will assume you're healthy.
          </p>
        )}

        <div className="space-y-3">
          {injuries.map((inj, i) => (
            <div
              key={i}
              className="p-3 rounded-lg"
              style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>Injury {i + 1}</span>
                <button onClick={() => removeInjury(i)} className="p-1 rounded hover:bg-[var(--border)]">
                  <X className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-2 mb-2">
                <select className="input text-xs" value={inj.area} onChange={e => updateInjury(i, 'area', e.target.value)}>
                  {INJURY_AREAS.map(a => <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>)}
                </select>
                <select className="input text-xs" value={inj.side} onChange={e => updateInjury(i, 'side', e.target.value)}>
                  {INJURY_SIDES.map(s => <option key={s} value={s}>{s === 'n/a' ? 'N/A' : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
                <select className="input text-xs" value={inj.severity} onChange={e => updateInjury(i, 'severity', e.target.value)}>
                  {INJURY_SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
              </div>
              <input
                className="input w-full text-xs"
                placeholder="Notes (e.g. ACL sprain, 3 months ago)"
                value={inj.notes}
                onChange={e => updateInjury(i, 'notes', e.target.value)}
              />
            </div>
          ))}
        </div>
      </Card>

      {/* 6. Training Background */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Training Background</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Years Training</label>
            <input
              type="number"
              className="input w-full text-sm"
              placeholder="e.g. 3.5"
              step="0.5"
              min="0"
              value={yearsTraining}
              onChange={e => setYearsTraining(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--muted)' }}>Comp Experience</label>
            <select className="input w-full text-sm" value={competitionExp} onChange={e => setCompetitionExp(e.target.value)}>
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
              onChange={e => setAvailableDays(e.target.value)}
            />
          </div>
        </div>
      </Card>

      {/* 7. Why You Train */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Why Do You Train?</h2>
        <div className="flex flex-wrap gap-2">
          {MOTIVATIONS.map(m => (
            <button
              key={m.id}
              onClick={() => toggleMotivation(m.id)}
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

      {/* 8. Anything Else */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Anything Else?</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>Tell Grapple anything else about you or your training</p>
        <textarea
          className="input w-full text-sm"
          rows={3}
          placeholder="e.g. I have a desk job and sit 8 hours a day, I'm left-handed, I recently switched gyms..."
          value={additionalContext}
          onChange={e => setAdditionalContext(e.target.value)}
        />
      </Card>

      {/* Save */}
      <PrimaryButton
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 text-sm font-semibold"
      >
        {saving ? 'Saving...' : 'Save Preferences'}
      </PrimaryButton>

      {/* Info note */}
      <p className="text-xs text-center pb-2" style={{ color: 'var(--muted)' }}>
        Your preferences shape how Grapple gives advice, generates insights, and suggests daily training. Changes take effect on your next interaction.
      </p>
      <p className="text-xs text-center pb-4" style={{ color: 'var(--muted)', opacity: 0.7 }}>
        Grapple is an AI training advisor and not a certified instructor. Always follow guidance from your in-person coach and consult medical professionals for injury or health concerns.
      </p>
    </div>
  );
}
