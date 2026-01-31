import { useState, useEffect } from 'react';
import { readinessApi } from '../api/client';
import type { Readiness as ReadinessType } from '../types';
import { CheckCircle, Activity } from 'lucide-react';

export default function Readiness() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [latest, setLatest] = useState<ReadinessType | null>(null);

  const [formData, setFormData] = useState({
    check_date: new Date().toISOString().split('T')[0],
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
  });

  useEffect(() => {
    loadLatest();
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
      await readinessApi.create(formData);
      setSuccess(true);
      await loadLatest();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error logging readiness:', error);
      alert('Failed to log readiness. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const compositeScore = formData.sleep + (6 - formData.stress) + (6 - formData.soreness) + formData.energy;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Activity className="w-8 h-8 text-primary-600" />
        <h1 className="text-3xl font-bold">Daily Readiness</h1>
      </div>

      {/* Latest Readiness */}
      {latest && (
        <div className="card bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
          <h3 className="font-semibold mb-2">Latest Check-in</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {new Date(latest.check_date ?? new Date()).toLocaleDateString()} • Score: {latest.composite_score ?? 0}/20
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>Sleep: {latest.sleep ?? 0}/5</div>
            <div>Stress: {latest.stress ?? 0}/5</div>
            <div>Soreness: {latest.soreness ?? 0}/5</div>
            <div>Energy: {latest.energy ?? 0}/5</div>
          </div>
          {latest.hotspot_note && (
            <p className="mt-3 text-sm">Hotspot: {latest.hotspot_note}</p>
          )}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="card">
        {success && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-700 dark:text-green-400">
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
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Low</span>
                <span>High</span>
              </div>
            </div>
          ))}

          {/* Composite Score */}
          <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Composite Score</p>
            <p className="text-3xl font-bold text-primary-600">{compositeScore}/20</p>
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
