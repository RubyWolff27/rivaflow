import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { restApi } from '../api/client';
import { logger } from '../utils/logger';
import { ArrowLeft, Save, Camera, Trash2 } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import { useToast } from '../contexts/ToastContext';

interface RestDay {
  id: number;
  rest_date: string;
  rest_type: string;
  rest_note?: string;
  tomorrow_intention?: string;
  created_at: string;
}

const REST_TYPES = [
  { value: 'active', label: 'Active Recovery' },
  { value: 'full', label: 'Full Rest' },
  { value: 'injury', label: 'Injury / Rehab' },
  { value: 'sick', label: 'Sick Day' },
  { value: 'travel', label: 'Travelling' },
  { value: 'life', label: 'Life Got in the Way' },
];

export default function EditRest() {
  usePageTitle('Edit Rest Day');
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [restId, setRestId] = useState<number | null>(null);
  const [photoCount, setPhotoCount] = useState(0);

  const [formData, setFormData] = useState({
    rest_date: date || '',
    rest_type: 'full',
    rest_note: '',
    tomorrow_intention: '',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await restApi.getByDate(date!);
        if (cancelled) return;
        const found: RestDay = response.data;
        setRestId(found.id);
        setFormData({
          rest_date: found.rest_date,
          rest_type: found.rest_type,
          rest_note: found.rest_note || '',
          tomorrow_intention: found.tomorrow_intention || '',
        });
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading rest day:', error);
          toast.error('Failed to load rest day');
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
      await restApi.logRestDay({
        check_date: formData.rest_date,
        rest_type: formData.rest_type,
        rest_note: formData.rest_note || undefined,
        tomorrow_intention: formData.tomorrow_intention || undefined,
      });

      toast.success('Rest day updated!');
      navigate('/feed');
    } catch (error) {
      logger.error('Error updating rest day:', error);
      toast.error('Failed to update rest day');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!restId) return;
    setDeleting(true);
    try {
      await restApi.delete(restId);
      toast.success('Rest day deleted');
      navigate('/feed');
    } catch (error) {
      logger.error('Error deleting rest day:', error);
      toast.error('Failed to delete rest day');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
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
        <h1 className="text-3xl font-bold">Edit Rest Day</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Date */}
        <div>
          <label className="label">Date</label>
          <input
            type="date"
            className="input"
            value={formData.rest_date}
            onChange={(e) => setFormData({ ...formData, rest_date: e.target.value })}
            required
          />
        </div>

        {/* Rest Type */}
        <div>
          <label className="label">Rest Type</label>
          <select
            className="input"
            value={formData.rest_type}
            onChange={(e) => setFormData({ ...formData, rest_type: e.target.value })}
            required
          >
            {REST_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Rest Note */}
        <div>
          <label className="label">Notes - Optional</label>
          <textarea
            className="input"
            value={formData.rest_note}
            onChange={(e) => setFormData({ ...formData, rest_note: e.target.value })}
            rows={4}
            placeholder="Why are you taking a rest day? How are you feeling?"
          />
        </div>

        {/* Tomorrow's Intention */}
        <div>
          <label className="label">Tomorrow's Intention - Optional</label>
          <input
            type="text"
            className="input"
            value={formData.tomorrow_intention}
            onChange={(e) => setFormData({ ...formData, tomorrow_intention: e.target.value })}
            placeholder="e.g., Light drilling session, Full training, Continue resting..."
          />
        </div>

        {/* Photos */}
        {restId && (
          <div className="border-t border-[var(--border)] pt-6">
            <div className="flex items-center gap-2 mb-4">
              <Camera className="w-5 h-5 text-[var(--muted)]" />
              <h3 className="font-semibold text-lg">Photos</h3>
              <span className="text-sm text-[var(--muted)]">({photoCount}/3)</span>
            </div>

            <div className="space-y-4">
              <PhotoGallery
                activityType="rest"
                activityId={restId}
                onPhotoCountChange={setPhotoCount}
              />

              <PhotoUpload
                activityType="rest"
                activityId={restId}
                activityDate={formData.rest_date}
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

      {/* Delete section */}
      {restId && (
        <div className="card border border-[var(--error)]" style={{ borderColor: 'var(--error)' }}>
          {showDeleteConfirm ? (
            <div className="space-y-3">
              <p className="text-sm font-medium">Are you sure you want to delete this rest day? This cannot be undone.</p>
              <div className="flex gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                  style={{ backgroundColor: 'var(--error)' }}
                >
                  {deleting ? 'Deleting...' : 'Yes, Delete'}
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="btn-secondary text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-2 text-sm font-medium"
              style={{ color: 'var(--error)' }}
            >
              <Trash2 className="w-4 h-4" />
              Delete Rest Day
            </button>
          )}
        </div>
      )}
    </div>
  );
}
