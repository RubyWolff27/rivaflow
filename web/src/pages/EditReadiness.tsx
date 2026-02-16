import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { readinessApi } from '../api/client';
import { logger } from '../utils/logger';
import { ArrowLeft, Save, Camera } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import { useToast } from '../contexts/ToastContext';

export default function EditReadiness() {
  usePageTitle('Edit Readiness');
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [readinessId, setReadinessId] = useState<number | null>(null);
  const [photoCount, setPhotoCount] = useState(0);
  const toast = useToast();

  const [formData, setFormData] = useState({
    check_date: date || '',
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await readinessApi.getByDate(date!);
        if (!cancelled) {
          const readiness = response.data;
          setReadinessId(readiness.id);
          setFormData({
            check_date: readiness.check_date,
            sleep: readiness.sleep,
            stress: readiness.stress,
            soreness: readiness.soreness,
            energy: readiness.energy,
            hotspot_note: readiness.hotspot_note || '',
            weight_kg: readiness.weight_kg?.toString() || '',
          });
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading readiness:', error);
          toast.error('Failed to load readiness check-in');
          navigate('/feed');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [date]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await readinessApi.create({
        check_date: formData.check_date,
        sleep: formData.sleep,
        stress: formData.stress,
        soreness: formData.soreness,
        energy: formData.energy,
        hotspot_note: formData.hotspot_note || undefined,
        weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : undefined,
      });

      toast.success('Readiness check-in updated successfully!');
      navigate('/feed');
    } catch (error) {
      logger.error('Error updating readiness:', error);
      toast.error('Failed to update readiness check-in');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="text-[var(--muted)] hover:text-[var(--text)]"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-3xl font-bold">Edit Readiness Check-in</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Date */}
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

        {/* Sleep */}
        <div>
          <label className="label">
            Sleep Quality: {formData.sleep}/5
            <span className="text-sm font-normal text-[var(--muted)] ml-2">
              (1 = Very Poor, 5 = Excellent)
            </span>
          </label>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            className="w-full"
            value={formData.sleep}
            onChange={(e) => setFormData({ ...formData, sleep: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
            <span>Very Poor</span>
            <span>Poor</span>
            <span>Fair</span>
            <span>Good</span>
            <span>Excellent</span>
          </div>
        </div>

        {/* Stress */}
        <div>
          <label className="label">
            Stress Level: {formData.stress}/5
            <span className="text-sm font-normal text-[var(--muted)] ml-2">
              (1 = Very Low, 5 = Very High)
            </span>
          </label>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            className="w-full"
            value={formData.stress}
            onChange={(e) => setFormData({ ...formData, stress: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
            <span>Very Low</span>
            <span>Low</span>
            <span>Moderate</span>
            <span>High</span>
            <span>Very High</span>
          </div>
        </div>

        {/* Soreness */}
        <div>
          <label className="label">
            Muscle Soreness: {formData.soreness}/5
            <span className="text-sm font-normal text-[var(--muted)] ml-2">
              (1 = None, 5 = Extreme)
            </span>
          </label>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            className="w-full"
            value={formData.soreness}
            onChange={(e) => setFormData({ ...formData, soreness: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
            <span>None</span>
            <span>Mild</span>
            <span>Moderate</span>
            <span>Severe</span>
            <span>Extreme</span>
          </div>
        </div>

        {/* Energy */}
        <div>
          <label className="label">
            Energy Level: {formData.energy}/5
            <span className="text-sm font-normal text-[var(--muted)] ml-2">
              (1 = Very Low, 5 = Very High)
            </span>
          </label>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            className="w-full"
            value={formData.energy}
            onChange={(e) => setFormData({ ...formData, energy: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
            <span>Very Low</span>
            <span>Low</span>
            <span>Moderate</span>
            <span>High</span>
            <span>Very High</span>
          </div>
        </div>

        {/* Weight */}
        <div>
          <label className="label">Weight (kg) - Optional</label>
          <input
            type="number"
            className="input"
            value={formData.weight_kg}
            onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
            placeholder="e.g., 75.5"
            step="0.1"
            min="30"
            max="300"
          />
        </div>

        {/* Hotspot Note */}
        <div>
          <label className="label">Injury/Hotspot Note - Optional</label>
          <textarea
            className="input"
            value={formData.hotspot_note}
            onChange={(e) => setFormData({ ...formData, hotspot_note: e.target.value })}
            rows={3}
            placeholder="Any injuries, soreness areas, or physical issues..."
          />
        </div>

        {/* Photos */}
        {readinessId && (
          <div className="border-t border-[var(--border)] pt-6">
            <div className="flex items-center gap-2 mb-4">
              <Camera className="w-5 h-5 text-[var(--muted)]" />
              <h3 className="font-semibold text-lg">Photos</h3>
              <span className="text-sm text-[var(--muted)]">({photoCount}/3)</span>
            </div>

            <div className="space-y-4">
              <PhotoGallery
                activityType="readiness"
                activityId={readinessId}
                onPhotoCountChange={setPhotoCount}
              />

              <PhotoUpload
                activityType="readiness"
                activityId={readinessId}
                activityDate={formData.check_date}
                currentPhotoCount={photoCount}
                onUploadSuccess={() => {
                  setPhotoCount(photoCount + 1);
                }}
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="btn-primary flex items-center gap-2 flex-1"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
