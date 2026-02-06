import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { restApi } from '../api/client';
import { ArrowLeft, Calendar, Moon, Edit2, Camera } from 'lucide-react';
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
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const [restDay, setRestDay] = useState<RestDay | null>(null);
  const [loading, setLoading] = useState(true);
  const [photoCount, setPhotoCount] = useState(0);

  useEffect(() => {
    loadRestDay();
  }, [date]);

  const loadRestDay = async () => {
    setLoading(true);
    try {
      // Get all recent rest days and find the one matching the date
      const response = await restApi.getRecent(365);
      const found = response.data.find((r: RestDay) => r.rest_date === date);
      if (found) {
        setRestDay(found);
      } else {
        throw new Error('Rest day not found');
      }
    } catch (error) {
      console.error('Error loading rest day:', error);
      toast.showToast('error', 'Failed to load rest day');
      navigate('/feed');
    } finally {
      setLoading(false);
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
      'full': 'Full Rest Day',
      'active': 'Active Recovery',
      'injury': 'Injury Recovery',
      'sick': 'Sick Day',
    };
    return labels[type] || type;
  };

  const getRestTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      'full': 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
      'active': 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
      'injury': 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
      'sick': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300',
    };
    return colors[type] || 'bg-gray-100 dark:bg-gray-800 text-[var(--text)]';
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
        <Link
          to={`/rest/edit/${restDay.rest_date}`}
          className="btn-primary flex items-center gap-2"
          aria-label="Edit rest day"
        >
          <Edit2 className="w-4 h-4" />
          Edit
        </Link>
      </div>

      {/* Main Info Card */}
      <div className="card">
        <div className="flex items-start gap-4 mb-4">
          <Moon className="w-8 h-8 text-purple-600" />
          <div className="flex-1">
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRestTypeColor(restDay.rest_type)}`}>
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
        <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
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
          <span className="text-sm text-gray-500">({photoCount}/3)</span>
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
