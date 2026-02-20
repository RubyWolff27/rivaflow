import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { getLocalDateString } from '../utils/date';
import { readinessApi, profileApi, suggestionsApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Readiness as ReadinessType } from '../types';
import { Activity, Heart, Waves, Wind, Target, Pencil } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import { triggerInsightRefresh } from '../utils/insightRefresh';
import ReadinessResult from '../components/ReadinessResult';
import ReadinessTrendChart from '../components/analytics/ReadinessTrendChart';

interface WhoopAutoFill {
  sleep: number;
  energy: number;
  hrv_ms: number | null;
  resting_hr: number | null;
  spo2: number | null;
  whoop_recovery_score: number | null;
  whoop_sleep_score: number | null;
  data_source: string;
}

export default function Readiness() {
  usePageTitle('Readiness');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [latest, setLatest] = useState<ReadinessType | null>(null);
  const [suggestionData, setSuggestionData] = useState<{ suggestion?: string; triggered_rules?: { name: string; recommendation: string; explanation: string; priority: number }[] } | null>(null);
  const [whoopAutoFill, setWhoopAutoFill] = useState<WhoopAutoFill | null>(null);
  const [whoopApplied, setWhoopApplied] = useState(false);
  const [trendData, setTrendData] = useState<{ date: string; score: number }[]>([]);
  const [weightGoal, setWeightGoal] = useState<{ target_weight_kg: number; target_weight_date: string } | null>(null);
  const toast = useToast();

  const [formData, setFormData] = useState({
    check_date: getLocalDateString(),
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '',
    data_source: 'manual' as string,
    hrv_ms: null as number | null,
    resting_hr: null as number | null,
    spo2: null as number | null,
    whoop_recovery_score: null as number | null,
    whoop_sleep_score: null as number | null,
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const res = await readinessApi.getLatest();
        if (!cancelled && res.data) {
          setLatest(res.data ?? null);
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading readiness:', error);
          toast.error('Failed to load readiness data');
        }
      }

      // Fetch profile for weight goal
      try {
        const profileRes = await profileApi.get();
        const p = profileRes.data;
        if (!cancelled && p?.target_weight_kg && p?.target_weight_date) {
          setWeightGoal({
            target_weight_kg: p.target_weight_kg,
            target_weight_date: p.target_weight_date,
          });
        }
      } catch (err) {
        logger.debug('Profile not available', err);
      }

      // Fetch 7-day trend on page load
      try {
        const end = getLocalDateString();
        const startD = new Date();
        startD.setDate(startD.getDate() - 6);
        const start = startD.toISOString().split('T')[0];
        const trendRes = await readinessApi.getByRange(start, end);
        const items = Array.isArray(trendRes.data) ? trendRes.data : [];
        if (!cancelled) {
          setTrendData(
            items.map((r: ReadinessType) => ({
              date: r.check_date || '',
              score: r.composite_score ?? 0,
            }))
          );
        }
      } catch (err) {
        logger.debug('Trend data not available', err);
      }

      // Try WHOOP auto-fill
      try {
        const today = getLocalDateString();
        const autoRes = await whoopApi.getReadinessAutoFill(today);
        if (!cancelled && autoRes.data?.auto_fill) {
          const af = autoRes.data.auto_fill as WhoopAutoFill;
          setWhoopAutoFill(af);
          // Pre-fill sleep and energy from WHOOP
          setFormData(prev => ({
            ...prev,
            sleep: af.sleep,
            energy: af.energy,
            data_source: 'whoop',
            hrv_ms: af.hrv_ms,
            resting_hr: af.resting_hr,
            spo2: af.spo2,
            whoop_recovery_score: af.whoop_recovery_score,
            whoop_sleep_score: af.whoop_sleep_score,
          }));
          setWhoopApplied(true);
        }
      } catch (err) {
        logger.debug('WHOOP not connected or no data', err);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [toast]);

  const loadLatest = async () => {
    try {
      const res = await readinessApi.getLatest();
      if (res.data) {
        setLatest(res.data ?? null);
      }
    } catch (error) {
      logger.error('Error loading readiness:', error);
      toast.error('Failed to load readiness data');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        check_date: formData.check_date,
        sleep: formData.sleep,
        stress: formData.stress,
        soreness: formData.soreness,
        energy: formData.energy,
        hotspot_note: formData.hotspot_note || undefined,
        weight_kg: formData.weight_kg !== '' ? Number(formData.weight_kg) : undefined,
        hrv_ms: formData.hrv_ms ?? undefined,
        resting_hr: formData.resting_hr ?? undefined,
        spo2: formData.spo2 ?? undefined,
        whoop_recovery_score: formData.whoop_recovery_score ?? undefined,
        whoop_sleep_score: formData.whoop_sleep_score ?? undefined,
        data_source: formData.data_source || undefined,
      };
      await readinessApi.create(submitData);
      setSuccess(true);
      triggerInsightRefresh();
      await loadLatest();
      // Fetch suggestion for recommendation display
      try {
        const sugRes = await suggestionsApi.getToday();
        if (sugRes.data) {
          setSuggestionData({
            suggestion: sugRes.data.suggestion,
            triggered_rules: sugRes.data.triggered_rules,
          });
        }
      } catch (err) {
        logger.debug('Suggestion not available', err);
      }
      // Fetch 7-day trend for chart
      try {
        const end = getLocalDateString();
        const startD = new Date();
        startD.setDate(startD.getDate() - 6);
        const start = startD.toISOString().split('T')[0];
        const trendRes = await readinessApi.getByRange(start, end);
        const items = Array.isArray(trendRes.data) ? trendRes.data : [];
        setTrendData(
          items.map((r: ReadinessType) => ({
            date: r.check_date || '',
            score: r.composite_score ?? 0,
          }))
        );
      } catch (err) {
        logger.debug('Trend data not available', err);
      }
    } catch (error) {
      logger.error('Error logging readiness:', error);
      toast.error('Failed to log readiness. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const compositeScore = formData.sleep + (6 - formData.stress) + (6 - formData.soreness) + formData.energy;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Activity className="w-8 h-8 text-[var(--accent)]" />
        <h1 className="text-3xl font-bold">Daily Readiness</h1>
      </div>

      {/* Latest Readiness */}
      {latest && (
        <div className="card bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">Latest Check-in</h2>
            <Link
              to={`/readiness/edit/${latest.check_date}`}
              className="flex items-center gap-1 text-xs font-medium hover:underline"
              style={{ color: 'var(--accent)' }}
            >
              <Pencil className="w-3 h-3" />
              Edit
            </Link>
          </div>
          <p className="text-sm text-[var(--muted)] mb-3">
            {new Date(latest.check_date ?? new Date()).toLocaleDateString()} • Score: {latest.composite_score ?? 0}/20
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>Sleep: {latest.sleep ?? 0}/5</div>
            <div>Stress: {latest.stress ?? 0}/5</div>
            <div>Soreness: {latest.soreness ?? 0}/5</div>
            <div>Energy: {latest.energy ?? 0}/5</div>
          </div>
          {latest.weight_kg && (
            <div className="mt-2">Weight: {latest.weight_kg} kg</div>
          )}
          {latest.hotspot_note && (
            <p className="mt-3 text-sm">Hotspot: {latest.hotspot_note}</p>
          )}
        </div>
      )}

      {/* Trend chart — shown whenever data is available */}
      {trendData.length > 1 && (
        <div className="card">
          <h2 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>7-Day Readiness Trend</h2>
          <ReadinessTrendChart data={trendData} />
        </div>
      )}

      {/* Result after submission */}
      {success && (
        <ReadinessResult
          compositeScore={compositeScore}
          suggestion={suggestionData?.suggestion}
          triggeredRules={suggestionData?.triggered_rules}
        />
      )}

      {/* WHOOP auto-fill banner */}
      {whoopApplied && whoopAutoFill && (
        <div className="card bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-4 h-4 text-green-600" />
            <p className="text-sm font-semibold text-green-800 dark:text-green-300">
              Pre-filled from WHOOP recovery (score: {whoopAutoFill.whoop_recovery_score}%)
            </p>
          </div>
          <p className="text-xs text-green-700 dark:text-green-400 mb-3">
            Sleep and energy have been set based on your WHOOP data. Adjust stress and soreness manually.
          </p>
          <div className="flex gap-3 flex-wrap">
            {whoopAutoFill.hrv_ms != null && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-100 dark:bg-green-900/40 text-xs font-medium text-green-800 dark:text-green-300">
                <Waves className="w-3 h-3" />
                HRV: {Math.round(whoopAutoFill.hrv_ms)} ms
              </div>
            )}
            {whoopAutoFill.resting_hr != null && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-100 dark:bg-green-900/40 text-xs font-medium text-green-800 dark:text-green-300">
                <Heart className="w-3 h-3" />
                RHR: {Math.round(whoopAutoFill.resting_hr)} bpm
              </div>
            )}
            {whoopAutoFill.spo2 != null && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-100 dark:bg-green-900/40 text-xs font-medium text-green-800 dark:text-green-300">
                <Wind className="w-3 h-3" />
                SpO2: {Math.round(whoopAutoFill.spo2)}%
              </div>
            )}
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="card">

        <div className="space-y-6">
          <div>
            <label className="label">Date</label>
            <input
              type="date"
              className="input"
              value={formData.check_date}
              onChange={(e) => setFormData({ ...formData, check_date: e.target.value })}
              required
            />
          </div>

          {/* Sliders */}
          {(['sleep', 'stress', 'soreness', 'energy'] as const).map((metric) => (
            <div key={metric}>
              <label className="label capitalize flex justify-between">
                <span>{metric}</span>
                <span className="font-bold">{formData[metric]}/5</span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={formData[metric]}
                onChange={(e) => {
                  const newVal = parseInt(e.target.value);
                  const update: Record<string, unknown> = { [metric]: newVal };
                  // If user modifies WHOOP-prefilled values, mark as whoop+manual
                  if (whoopApplied && (metric === 'sleep' || metric === 'energy') && formData.data_source === 'whoop') {
                    update.data_source = 'whoop+manual';
                  }
                  setFormData(prev => ({ ...prev, ...update }));
                }}
                className="w-full h-2 bg-[var(--surfaceElev)] rounded-lg appearance-none cursor-pointer"
                aria-label={metric}
                aria-valuetext={`${metric}: ${formData[metric]} out of 5`}
              />
              <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
                <span>{metric === 'sleep' ? 'Poor' : metric === 'soreness' ? 'None' : 'Low'}</span>
                <span>{metric === 'sleep' ? 'Great' : metric === 'soreness' ? 'Severe' : 'High'}</span>
              </div>
            </div>
          ))}

          {/* Composite Score */}
          <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
            <p className="text-sm text-[var(--muted)] mb-1">Composite Score</p>
            <p className="text-3xl font-bold text-[var(--accent)]">{compositeScore}/20</p>
          </div>

          {/* Weight */}
          <div>
            <label className="label">Body Weight (optional)</label>
            <div className="relative">
              <input
                type="number"
                inputMode="decimal"
                step="0.1"
                min="0"
                className="input pr-10"
                value={formData.weight_kg}
                onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
                placeholder="e.g., 78.5"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-[var(--muted)]">kg</span>
            </div>
          </div>

          {/* Weight Goal Progress */}
          {weightGoal && formData.weight_kg !== '' && (
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>Weight Goal</span>
              </div>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Target: {weightGoal.target_weight_kg} kg by{' '}
                {new Date(weightGoal.target_weight_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                {' '}({Math.max(0, Math.ceil((new Date(weightGoal.target_weight_date).getTime() - Date.now()) / 86400000))} days remaining)
              </p>
              <p className="text-sm mt-1" style={{ color: 'var(--text)' }}>
                Current: {formData.weight_kg} kg
                {' '}({(Number(formData.weight_kg) - weightGoal.target_weight_kg) > 0 ? '+' : ''}
                {(Number(formData.weight_kg) - weightGoal.target_weight_kg).toFixed(1)} kg from target)
              </p>
            </div>
          )}

          {/* Hotspot */}
          <div>
            <label className="label">Hotspot / Injury Note (optional)</label>
            <input
              type="text"
              className="input"
              value={formData.hotspot_note}
              onChange={(e) => setFormData({ ...formData, hotspot_note: e.target.value })}
              placeholder="e.g., left shoulder, right knee"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Logging...' : 'Log Readiness'}
          </button>
        </div>
      </form>
    </div>
  );
}
