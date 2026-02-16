import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { restApi } from '../api/client';
import { logger } from '../utils/logger';
import { ArrowLeft, Calendar, Moon, Edit2, Camera, Trash2 } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';

interface RestDay {
  id: number;
  rest_date: string;
  rest_type: string;
  rest_note?: string;
  tomorrow_intention?: string;
  created_at: string;
}

export default function RestDetail() {
  usePageTitle('Rest Day');
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const [restDay, setRestDay] = useState<RestDay | null>(null);
  const [loading, setLoading] = useState(true);
  const [photoCount, setPhotoCount] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await restApi.getByDate(date!);
        if (cancelled) return;
        setRestDay(response.data);
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

  const handleDelete = async () => {
    if (!restDay) return;
    setDeleting(true);
    try {
      await restApi.delete(restDay.id);
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
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <CardSkeleton lines={2} />
        <CardSkeleton lines={3} />
      </div>
    );
  }

  if (!restDay) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p style={{ color: 'var(--muted)' }}>Rest day not found</p>
      </div>
    );
  }

  const restDate = new Date(restDay.rest_date);
  const formattedDate = restDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const getRestTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      'active': 'Active Recovery',
      'full': 'Full Rest',
      'injury': 'Injury / Rehab',
      'sick': 'Sick Day',
      'travel': 'Travelling',
      'life': 'Life Got in the Way',
    };
    return labels[type] || type;
  };

  const getRestTypeStyle = (type: string): React.CSSProperties => {
    const styles: { [key: string]: React.CSSProperties } = {
      'active': { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' },
      'full': { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7' },
      'injury': { backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)' },
      'sick': { backgroundColor: 'rgba(234,179,8,0.1)', color: '#ca8a04' },
      'travel': { backgroundColor: 'rgba(34,197,94,0.1)', color: '#16a34a' },
      'life': { backgroundColor: 'rgba(156,163,175,0.1)', color: '#6b7280' },
    };
    return styles[type] || { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' };
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="transition-colors"
            aria-label="Go back"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-3xl font-bold text-[var(--text)]" id="page-title">Rest Day</h1>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to={`/rest/edit/${restDay.rest_date}`}
            className="btn-primary flex items-center gap-2"
            aria-label="Edit rest day"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </Link>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-2 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
            aria-label="Delete rest day"
            style={{ color: 'var(--error)' }}
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Delete confirmation */}
      {showDeleteConfirm && (
        <div className="card border" style={{ borderColor: 'var(--error)' }}>
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
        </div>
      )}

      {/* Main Info Card */}
      <div className="card">
        <div className="flex items-start gap-4 mb-4">
          <Moon className="w-8 h-8 text-purple-600" />
          <div className="flex-1">
            <span className="inline-block px-3 py-1 rounded-full text-sm font-semibold" style={getRestTypeStyle(restDay.rest_type)}>
              {getRestTypeLabel(restDay.rest_type)}
            </span>
            <div className="flex items-center gap-2 text-[var(--muted)] mt-2">
              <Calendar className="w-4 h-4" />
              <p className="text-sm">{formattedDate}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Rest Note */}
      {restDay.rest_note && (
        <div className="card">
          <h3 className="font-semibold text-lg mb-3">Notes</h3>
          <p className="text-[var(--text)] whitespace-pre-wrap">
            {restDay.rest_note}
          </p>
        </div>
      )}

      {/* Tomorrow's Intention */}
      {restDay.tomorrow_intention && (
        <div className="card" style={{ backgroundColor: 'rgba(59,130,246,0.1)', borderColor: 'var(--accent)' }}>
          <h3 className="font-semibold text-lg mb-3">Tomorrow's Intention</h3>
          <p className="text-[var(--text)]">
            → {restDay.tomorrow_intention}
          </p>
        </div>
      )}

      {/* Photos */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Camera className="w-5 h-5 text-[var(--muted)]" />
          <h3 className="font-semibold text-lg">Photos</h3>
          <span className="text-sm text-[var(--muted)]">({photoCount}/3)</span>
        </div>

        <div className="space-y-4">
          <PhotoGallery
            activityType="rest"
            activityId={restDay.id}
            onPhotoCountChange={setPhotoCount}
          />

          <PhotoUpload
            activityType="rest"
            activityId={restDay.id}
            activityDate={restDay.rest_date}
            currentPhotoCount={photoCount}
            onUploadSuccess={() => {
              setPhotoCount(photoCount + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
