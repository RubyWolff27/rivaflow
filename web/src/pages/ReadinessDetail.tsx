import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { readinessApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Readiness } from '../types';
import { ArrowLeft, Calendar, Heart, Edit2, Camera } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import { useToast } from '../contexts/ToastContext';

export default function ReadinessDetail() {
  usePageTitle('Readiness Detail');
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [photoCount, setPhotoCount] = useState(0);
  const toast = useToast();

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await readinessApi.getByDate(date!);
        if (!cancelled) setReadiness(response.data);
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

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p className="text-[var(--muted)]">Loading readiness...</p>
      </div>
    );
  }

  if (!readiness) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p className="text-[var(--muted)]">Readiness not found</p>
      </div>
    );
  }

  const checkDate = new Date(readiness.check_date);
  const formattedDate = checkDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="text-[var(--muted)] hover:text-[var(--text)]"
            aria-label="Go back"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-3xl font-bold text-[var(--text)]" id="page-title">Readiness Check-in</h1>
        </div>
        <Link
          to={`/readiness/edit/${readiness.check_date}`}
          className="btn-primary flex items-center gap-2"
          aria-label="Edit readiness check-in"
        >
          <Edit2 className="w-4 h-4" />
          Edit
        </Link>
      </div>

      {/* Main Info Card */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <Heart className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm text-[var(--muted)]">Composite Score</p>
              <p className="text-4xl font-bold text-green-600">{readiness.composite_score}/5</p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 text-[var(--muted)]">
              <Calendar className="w-4 h-4" />
              <p className="text-sm">{formattedDate}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Scores Grid */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Readiness Scores</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-sm text-[var(--muted)] mb-1">Sleep Quality</p>
            <p className={`text-3xl font-bold ${getScoreColor(readiness.sleep)}`}>
              😴 {readiness.sleep}/5
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-[var(--muted)] mb-1">Stress Level</p>
            <p className={`text-3xl font-bold ${getScoreColor(5 - readiness.stress + 1)}`}>
              😰 {readiness.stress}/5
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-[var(--muted)] mb-1">Soreness</p>
            <p className={`text-3xl font-bold ${getScoreColor(5 - readiness.soreness + 1)}`}>
              💪 {readiness.soreness}/5
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-[var(--muted)] mb-1">Energy Level</p>
            <p className={`text-3xl font-bold ${getScoreColor(readiness.energy)}`}>
              ⚡ {readiness.energy}/5
            </p>
          </div>
        </div>
      </div>

      {/* Weight */}
      {readiness.weight_kg && (
        <div className="card">
          <h2 className="font-semibold text-lg mb-2">Weight</h2>
          <p className="text-2xl font-bold text-[var(--text)]">
            ⚖️ {readiness.weight_kg} kg
          </p>
        </div>
      )}

      {/* Hotspot Note */}
      {readiness.hotspot_note && (
        <div className="card">
          <h2 className="font-semibold text-lg mb-2">Injury/Hotspot Note</h2>
          <p className="text-[var(--text)] whitespace-pre-wrap">
            🔥 {readiness.hotspot_note}
          </p>
        </div>
      )}

      {/* Photos */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Camera className="w-5 h-5 text-[var(--muted)]" />
          <h2 className="font-semibold text-lg">Photos</h2>
          <span className="text-sm text-[var(--muted)]">({photoCount}/10)</span>
        </div>

        <div className="space-y-4">
          <PhotoGallery
            activityType="readiness"
            activityId={readiness.id}
            onPhotoCountChange={setPhotoCount}
          />

          <PhotoUpload
            activityType="readiness"
            activityId={readiness.id}
            activityDate={readiness.check_date}
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
