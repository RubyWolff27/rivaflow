import { useState, useEffect } from 'react';
import { readinessApi } from '../api/client';
import type { Readiness as ReadinessType } from '../types';
import { CheckCircle, Activity } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';

export default function Readiness() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [latest, setLatest] = useState<ReadinessType | null>(null);
  const toast = useToast();

  const [formData, setFormData] = useState({
    check_date: new Date().toISOString().split('T')[0],
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '' as string | number,
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
        if (!cancelled) console.error('Error loading readiness:', error);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const loadLatest = async () => {
    try {
      const res = await readinessApi.getLatest();
      if (res.data) {
        setLatest(res.data ?? null);
      }
    } catch (error) {
      console.error('Error loading readiness:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        weight_kg: formData.weight_kg !== '' ? Number(formData.weight_kg) : undefined,
      };
      await readinessApi.create(submitData);
      setSuccess(true);
      await loadLatest();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error logging readiness:', error);
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
          <h3 className="font-semibold mb-2">Latest Check-in</h3>
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

      {/* Form */}
      <form onSubmit={handleSubmit} className="card">
        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700">
            <CheckCircle className="w-5 h-5" />
            Readiness logged successfully!
          </div>
        )}

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
                onChange={(e) => setFormData({ ...formData, [metric]: parseInt(e.target.value) })}
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
