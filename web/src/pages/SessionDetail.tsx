import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { sessionsApi } from '../api/client';
import type { Session } from '../types';
import { ArrowLeft, Calendar, Clock, Zap, Users, MapPin, User, Book, Edit2, Activity, Target, Camera, ChevronLeft, ChevronRight } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [photoCount, setPhotoCount] = useState(0);
  const [prevSessionId, setPrevSessionId] = useState<number | null>(null);
  const [nextSessionId, setNextSessionId] = useState<number | null>(null);
  const toast = useToast();

  useEffect(() => {
    let cancelled = false;

    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await sessionsApi.getById(parseInt(id ?? '0'));
        if (!cancelled) setSession(response.data ?? null);
      } catch (error) {
        if (!cancelled) {
          console.error('Error loading session:', error);
          toast.error('Failed to load session');
          navigate('/feed');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const doLoadAdjacent = async () => {
      try {
        const response = await sessionsApi.list(1000);
        if (cancelled) return;
        const sessions = response.data || [];
        const currentIndex = sessions.findIndex(s => s.id === parseInt(id ?? '0'));
        if (currentIndex !== -1) {
          if (currentIndex < sessions.length - 1) {
            setPrevSessionId(sessions[currentIndex + 1].id);
          } else {
            setPrevSessionId(null);
          }
          if (currentIndex > 0) {
            setNextSessionId(sessions[currentIndex - 1].id);
          } else {
            setNextSessionId(null);
          }
        }
      } catch (error) {
        if (!cancelled) console.error('Error loading adjacent sessions:', error);
      }
    };

    doLoad();
    doLoadAdjacent();
    return () => { cancelled = true; };
  }, [id]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && prevSessionId) {
        navigate(`/session/${prevSessionId}`);
      } else if (e.key === 'ArrowRight' && nextSessionId) {
        navigate(`/session/${nextSessionId}`);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [prevSessionId, nextSessionId, navigate]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <CardSkeleton lines={2} />
        <CardSkeleton lines={4} />
        <CardSkeleton lines={2} />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p style={{ color: 'var(--muted)' }}>Session not found</p>
      </div>
    );
  }

  const sessionDate = new Date(session.session_date ?? new Date());
  const formattedDate = sessionDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            style={{ color: 'var(--muted)' }}
            aria-label="Go back"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-3xl font-bold" style={{ color: 'var(--text)' }} id="page-title">Session Details</h1>
        </div>
        <div className="flex items-center gap-2">
          {/* Previous/Next Navigation */}
          <div className="flex items-center gap-1 mr-2">
            <button
              onClick={() => prevSessionId && navigate(`/session/${prevSessionId}`)}
              disabled={!prevSessionId}
              className="p-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: prevSessionId ? 'var(--surface)' : 'transparent',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
              aria-label="Previous session (Left Arrow)"
              title="Previous session (←)"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => nextSessionId && navigate(`/session/${nextSessionId}`)}
              disabled={!nextSessionId}
              className="p-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: nextSessionId ? 'var(--surface)' : 'transparent',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
              aria-label="Next session (Right Arrow)"
              title="Next session (→)"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          <Link
            to={`/session/edit/${session.id}`}
            className="btn-primary flex items-center gap-2"
            aria-label="Edit session"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </Link>
        </div>
      </div>

      {/* Main Info Card */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-sm font-semibold uppercase"
                style={{ backgroundColor: 'rgba(var(--accent-rgb), 0.12)', color: 'var(--accent)' }}>
                {session.class_type}
              </span>
              <span className="flex items-center gap-1 text-sm">
                <Zap className="w-4 h-4" />
                Intensity: {session.intensity}/5
              </span>
            </div>
            <h2 className="text-2xl font-bold text-[var(--text)] mb-1">
              {session.gym_name ?? 'Unknown Gym'}
            </h2>
            {session.location && (
              <p className="flex items-center gap-1 text-[var(--muted)]">
                <MapPin className="w-4 h-4" />
                {session.location}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 border-t border-[var(--border)]">
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Calendar className="w-4 h-4" />
              Date & Time
            </div>
            <p className="font-semibold">{formattedDate}</p>
            {session.class_time && (
              <p className="text-sm mt-1">
                {session.class_time}
              </p>
            )}
          </div>
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Clock className="w-4 h-4" />
              Duration
            </div>
            <p className="font-semibold">{session.duration_mins ?? 0} mins</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Activity className="w-4 h-4" />
              Rolls
            </div>
            <p className="font-semibold">{session.rolls ?? 0}</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Target className="w-4 h-4" />
              Submissions
            </div>
            <p className="font-semibold">{session.submissions_for ?? 0} / {session.submissions_against ?? 0}</p>
            <p className="text-xs text-[var(--muted)]">For / Against</p>
          </div>
        </div>
      </div>

      {/* Instructor */}
      {session.instructor_name && (
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-5 h-5 text-[var(--muted)]" />
            <h3 className="font-semibold text-lg">Instructor</h3>
          </div>
          <p className="text-[var(--text)]">{session.instructor_name}</p>
        </div>
      )}

      {/* Partners */}
      {session.partners && Array.isArray(session.partners) && session.partners.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-[var(--muted)]" />
            <h3 className="font-semibold text-lg">Training Partners</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {session.partners.map((partner) => (
              <span
                key={partner}
                className="px-3 py-1 bg-[var(--surfaceElev)] text-[var(--text)] rounded-full text-sm"
              >
                {partner}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Techniques */}
      {session.techniques && Array.isArray(session.techniques) && session.techniques.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Book className="w-5 h-5 text-[var(--muted)]" />
            <h3 className="font-semibold text-lg">Techniques Practiced</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {session.techniques.map((technique) => (
              <span
                key={technique}
                className="px-3 py-1 bg-[rgba(var(--accent-rgb),0.1)] text-[var(--accent)] rounded-full text-sm font-medium"
              >
                {technique}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Techniques */}
      {session.session_techniques && Array.isArray(session.session_techniques) && session.session_techniques.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-lg mb-4">Technique Details</h3>
          <div className="space-y-4">
            {session.session_techniques.map((tech: any) => (
              <div key={tech.technique_number ?? tech.movement_name} className="border border-[var(--border)] rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-[var(--accent)]">
                    {tech.movement_name ?? `Technique #${tech.technique_number ?? '?'}`}
                  </h4>
                  <span className="text-xs px-2 py-1 bg-[var(--surfaceElev)] rounded">
                    #{tech.technique_number ?? '?'}
                  </span>
                </div>
                {tech.notes && (
                  <p className="text-sm text-[var(--text)] mt-2 whitespace-pre-wrap">
                    {tech.notes}
                  </p>
                )}
                {tech.media_urls && Array.isArray(tech.media_urls) && tech.media_urls.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs font-semibold text-[var(--muted)]">Reference Media:</p>
                    {tech.media_urls.map((media: any) => (
                      <a
                        key={media.url}
                        href={media.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-sm text-[var(--accent)] hover:opacity-80 underline"
                      >
                        {media.title ?? media.url ?? 'Media Link'}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Whoop Stats */}
      {(session.whoop_strain || session.whoop_calories || session.whoop_avg_hr || session.whoop_max_hr) && (
        <div className="card">
          <h3 className="font-semibold text-lg mb-4">Whoop Stats</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {session.whoop_strain && (
              <div>
                <p className="text-sm mb-1">Strain</p>
                <p className="text-xl font-bold">{session.whoop_strain}</p>
              </div>
            )}
            {session.whoop_calories && (
              <div>
                <p className="text-sm mb-1">Calories</p>
                <p className="text-xl font-bold">{session.whoop_calories}</p>
              </div>
            )}
            {session.whoop_avg_hr && (
              <div>
                <p className="text-sm mb-1">Avg HR</p>
                <p className="text-xl font-bold">{session.whoop_avg_hr} bpm</p>
              </div>
            )}
            {session.whoop_max_hr && (
              <div>
                <p className="text-sm mb-1">Max HR</p>
                <p className="text-xl font-bold">{session.whoop_max_hr} bpm</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notes */}
      {session.notes && (
        <div className="card">
          <h3 className="font-semibold text-lg mb-3">Notes</h3>
          <p className="text-[var(--text)] whitespace-pre-wrap">
            {session.notes}
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
            activityType="session"
            activityId={session.id}
            onPhotoCountChange={setPhotoCount}
          />

          <PhotoUpload
            activityType="session"
            activityId={session.id}
            activityDate={session.session_date}
            currentPhotoCount={photoCount}
            onUploadSuccess={() => {
              // Trigger gallery refresh by re-mounting
              setPhotoCount(photoCount + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
