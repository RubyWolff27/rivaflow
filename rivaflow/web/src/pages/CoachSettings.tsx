import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { PrimaryButton } from '../components/ui';
import { coachPreferencesApi, profileApi } from '../api/client';
import { logger } from '../utils/logger';
import { useToast } from '../contexts/ToastContext';
import CoachSettingsForm from '../components/coach/CoachSettingsForm';
import InjuryManager from '../components/coach/InjuryManager';
import type { Injury } from '../components/coach/InjuryManager';

interface CoachPreferencesData {
  competition_ruleset?: string;
  training_mode?: string;
  comp_date?: string;
  comp_name?: string;
  comp_division?: string;
  comp_weight_class?: string;
  coaching_style?: string;
  primary_position?: string;
  focus_areas?: string[];
  weaknesses?: string;
  injuries?: Partial<Injury>[];
  training_start_date?: string;
  years_training?: number;
  competition_experience?: string;
  available_days_per_week?: number;
  motivations?: string[];
  additional_context?: string;
  gi_nogi_preference?: string;
  gi_bias_pct?: number;
  data?: CoachPreferencesData;
}

export default function CoachSettings() {
  usePageTitle('Coach Settings');
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [currentGrade, setCurrentGrade] = useState('');
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
  const [trainingStartDate, setTrainingStartDate] = useState('');
  const [yearsTraining, setYearsTraining] = useState('');
  const [competitionExp, setCompetitionExp] = useState('none');
  const [availableDays, setAvailableDays] = useState('4');
  const [motivations, setMotivations] = useState<string[]>([]);
  const [additionalContext, setAdditionalContext] = useState('');
  const [giNogiPreference, setGiNogiPreference] = useState('both');
  const [giBiasPct, setGiBiasPct] = useState(50);

  useEffect(() => {
    const load = async () => {
      try {
        try {
          const profileRes = await profileApi.get();
          const p = profileRes.data;
          if (p?.current_grade) setCurrentGrade(p.current_grade);
        } catch (err) { logger.debug('Profile not set yet', err); }

        const res = await coachPreferencesApi.get();
        const raw = res.data as CoachPreferencesData;
        const d = raw?.data || raw;
        if (d) {
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
          setInjuries((d.injuries || []).map((inj: Partial<Injury>) => ({
            area: inj.area || 'knee',
            side: inj.side || 'n/a',
            severity: inj.severity || 'moderate',
            notes: inj.notes || '',
            status: inj.status || 'active',
            resolved_date: inj.resolved_date || '',
            start_date: inj.start_date || '',
          })));
          setTrainingStartDate(d.training_start_date || '');
          setYearsTraining(d.years_training != null ? String(d.years_training) : '');
          setCompetitionExp(d.competition_experience || 'none');
          setAvailableDays(d.available_days_per_week != null ? String(d.available_days_per_week) : '4');
          setMotivations(d.motivations || []);
          setAdditionalContext(d.additional_context || '');
          setGiNogiPreference(d.gi_nogi_preference || 'both');
          setGiBiasPct(d.gi_bias_pct != null ? d.gi_bias_pct : 50);
        }
      } catch (err) {
        logger.debug('Coach preferences first time — use defaults', err);
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
    setInjuries(prev => [...prev, { area: 'knee', side: 'n/a', severity: 'moderate', notes: '', status: 'active', resolved_date: '', start_date: '' }]);
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
        training_start_date: trainingStartDate || null,
        years_training: yearsTraining ? parseFloat(yearsTraining) : null,
        competition_experience: competitionExp,
        available_days_per_week: parseInt(availableDays) || 4,
        motivations,
        additional_context: additionalContext || null,
        gi_nogi_preference: giNogiPreference,
        gi_bias_pct: giNogiPreference === 'both' ? giBiasPct : 50,
      });
      toast.success('Coach preferences saved');
    } catch (err) {
      logger.warn('Failed to save preferences', err);
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
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          style={{ color: 'var(--muted)' }}
          aria-label="Go back"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>Coach Settings</h1>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>Personalise how Grapple coaches you</p>
        </div>
      </div>

      <CoachSettingsForm
        currentGrade={currentGrade}
        trainingMode={trainingMode}
        onTrainingModeChange={setTrainingMode}
        compDate={compDate}
        onCompDateChange={setCompDate}
        compName={compName}
        onCompNameChange={setCompName}
        compDivision={compDivision}
        onCompDivisionChange={setCompDivision}
        compWeightClass={compWeightClass}
        onCompWeightClassChange={setCompWeightClass}
        competitionRuleset={competitionRuleset}
        onCompetitionRulesetChange={setCompetitionRuleset}
        coachingStyle={coachingStyle}
        onCoachingStyleChange={setCoachingStyle}
        giNogiPreference={giNogiPreference}
        onGiNogiPreferenceChange={setGiNogiPreference}
        giBiasPct={giBiasPct}
        onGiBiasPctChange={setGiBiasPct}
        primaryPosition={primaryPosition}
        onPrimaryPositionChange={setPrimaryPosition}
        focusAreas={focusAreas}
        onToggleFocusArea={toggleFocusArea}
        weaknesses={weaknesses}
        onWeaknessesChange={setWeaknesses}
        trainingStartDate={trainingStartDate}
        onTrainingStartDateChange={setTrainingStartDate}
        yearsTraining={yearsTraining}
        onYearsTrainingChange={setYearsTraining}
        competitionExp={competitionExp}
        onCompetitionExpChange={setCompetitionExp}
        availableDays={availableDays}
        onAvailableDaysChange={setAvailableDays}
        motivations={motivations}
        onToggleMotivation={toggleMotivation}
        additionalContext={additionalContext}
        onAdditionalContextChange={setAdditionalContext}
        daysUntilComp={daysUntilComp}
      />

      <InjuryManager
        injuries={injuries}
        onAdd={addInjury}
        onRemove={removeInjury}
        onUpdate={updateInjury}
      />

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
