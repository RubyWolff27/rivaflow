import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { sessionsApi, curriculumApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Session } from '../types';
import type { EvidenceCandidate } from '../types/curriculum';
import { ArrowLeft, Calendar, Clock, Zap, Users, MapPin, User, Book, Edit2, Activity, Target, Camera, Plus, Heart } from 'lucide-react';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import SessionInsights from '../components/SessionInsights';
import GarminPanel from '../components/GarminPanel';
import SessionScoreCard from '../components/sessions/SessionScoreCard';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';
import { formatClassType } from '../constants/activity';
import { NON_BJJ_TYPES } from '../components/sessions/sessionTypes';

/** Generate a human-readable story sentence for the session. */
function buildSessionStory(session: Session): string {
  const duration = session.duration_mins ?? 0;
  const classType = formatClassType(session.class_type);
  const gym = session.gym_name ?? 'training';
  const rolls = session.rolls ?? 0;

  let story = `${duration}-minute ${classType} session at ${gym}`;

  const isBjj = !NON_BJJ_TYPES.includes(session.class_type);
  if (isBjj && rolls > 0) {
    story += ` with ${rolls} roll${rolls !== 1 ? 's' : ''}`;
  }

  // Session strain (historical data stored on the session)
  const strain = session.whoop_strain;
  if (strain != null) {
    story += `. Strain ${Number(strain).toFixed(1)}`;
  }

  return story + '.';
}

export default function SessionDetail() {
  usePageTitle('Session Detail');
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [photoCount, setPhotoCount] = useState(0);
  const [recalculating, setRecalculating] = useState(false);
  const [showAllRolls, setShowAllRolls] = useState(false);
  const [evidenceCandidates, setEvidenceCandidates] = useState<EvidenceCandidate[]>([]);
  const [confirmingSlot, setConfirmingSlot] = useState<number | null>(null);
  const toast = useToast();

  const loadCandidates = async (sessionId: number) => {
    try {
      const res = await curriculumApi.evidenceCandidates(sessionId);
      setEvidenceCandidates(res.data?.candidates ?? []);
    } catch (err) {
      logger.debug('Evidence candidates unavailable', err);
    }
  };

  const confirmEvidence = async (candidate: EvidenceCandidate) => {
    setConfirmingSlot(candidate.slot_id);
    try {
      await curriculumApi.addEvidence(candidate.slot_id, {
        kind: candidate.kind,
        session_id: candidate.session_id,
        partner_ref: candidate.partner_ref ?? undefined,
      });
      toast.success(`${candidate.kind === 'live' ? 'Live' : 'Drilled'} evidence logged`);
      setEvidenceCandidates((prev) => prev.filter((c) => c.slot_id !== candidate.slot_id));
    } catch (err) {
      logger.error('Failed to log evidence', err);
      toast.error('Failed to log evidence');
    } finally {
      setConfirmingSlot(null);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await sessionsApi.getWithRolls(parseInt(id ?? '0'));
        if (!cancelled) {
          setSession(response.data ?? null);
          if (response.data?.id) loadCandidates(response.data.id);
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading session:', error);
          toast.error('Failed to load session');
          navigate('/feed');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    doLoad();
    return () => { cancelled = true; };
  }, [id]);

  const handleRecalculate = async () => {
    if (!session) return;
    setRecalculating(true);
    try {
      const res = await sessionsApi.recalculateScore(session.id);
      if (res.data) {
        setSession({
          ...session,
          session_score: res.data.session_score,
          score_breakdown: res.data.score_breakdown,
        });
        toast.success('Score recalculated');
      }
    } catch (err) {
      logger.warn('Failed to recalculate score', err);
      toast.error('Failed to recalculate score');
    } finally {
      setRecalculating(false);
    }
  };

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
        <button
          onClick={() => navigate('/sessions')}
          className="mt-4 px-4 py-2 rounded-lg text-sm"
          style={{ color: 'var(--accent)' }}
        >
          Back to Sessions
        </button>
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

  const hasWhoop = session.whoop_strain || session.whoop_calories || session.whoop_avg_hr || session.whoop_max_hr;

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

      {/* ── ISC-1,2,3: Main Info Card with strain pill + recovery dot ── */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-sm font-semibold uppercase"
                style={{ backgroundColor: 'rgba(var(--accent-rgb), 0.12)', color: 'var(--accent)' }}>
                {formatClassType(session.class_type)}
              </span>
              {session.intensity > 0 && (
                <span className="flex items-center gap-1 text-sm">
                  <Zap className="w-4 h-4" />
                  Intensity: {session.intensity}/5
                </span>
              )}
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

          {/* Strain pill — top right (historical data on the session) */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {session.whoop_strain != null && (
              <span
                className="px-3 py-1 rounded-full text-sm font-bold flex items-center gap-1"
                style={{
                  backgroundColor: session.whoop_strain <= 7 ? '#10B98120' : session.whoop_strain <= 14 ? '#F59E0B20' : '#EF444420',
                  color: session.whoop_strain <= 7 ? '#10B981' : session.whoop_strain <= 14 ? '#F59E0B' : '#EF4444',
                }}
              >
                <Zap className="w-3.5 h-3.5" />
                {Number(session.whoop_strain).toFixed(1)}
              </span>
            )}
          </div>
        </div>

        <div className={`grid ${!NON_BJJ_TYPES.includes(session.class_type) ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2'} gap-4 py-4 border-t border-[var(--border)]`}>
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
          {!NON_BJJ_TYPES.includes(session.class_type) && (
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Activity className="w-4 h-4" />
              Rolls
            </div>
            <p className="font-semibold">{session.rolls ?? 0}</p>
          </div>
          )}
          {!NON_BJJ_TYPES.includes(session.class_type) && (
          <div>
            <div className="flex items-center gap-1 text-sm mb-1">
              <Target className="w-4 h-4" />
              Submissions
            </div>
            <p className="font-semibold">{session.submissions_for ?? 0} / {session.submissions_against ?? 0}</p>
            <p className="text-xs text-[var(--muted)]">For / Against</p>
          </div>
          )}
        </div>
      </div>

      {/* ── ISC-4,5: Session Story Sentence ── */}
      <p className="text-sm px-1" style={{ color: 'var(--muted)' }}>
        {buildSessionStory(session)}
      </p>

      {/* ── ISC-6: Performance Score at position 3 ── */}
      <SessionScoreCard
        score={session.session_score}
        breakdown={session.score_breakdown}
        onRecalculate={handleRecalculate}
        recalculating={recalculating}
      />

      {/* Review auto-created session or add details CTA */}
      {session.needs_review ? (
        <div className="card" style={{ borderColor: '#f59e0b', borderWidth: '2px' }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-5 h-5 text-amber-500" />
                <h2 className="font-semibold text-lg" style={{ color: 'var(--text)' }}>Review Auto-Created Session</h2>
              </div>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Created from WHOOP BJJ workout. Review details and add rolls/techniques.
              </p>
            </div>
            <Link
              to={`/session/edit/${session.id}`}
              className="btn-primary flex items-center gap-2"
            >
              <Edit2 className="w-4 h-4" />
              Review & Edit
            </Link>
          </div>
        </div>
      ) : ['gi', 'no-gi', 'open-mat', 'competition'].includes(session.class_type) &&
        (session.rolls ?? 0) === 0 &&
        (!session.session_techniques || session.session_techniques.length === 0) && (
        <div className="card" style={{ borderColor: 'var(--accent)', borderWidth: '2px' }}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-lg" style={{ color: 'var(--text)' }}>Add Roll Details</h2>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Add partners, rolls, and techniques to unlock insights
              </p>
            </div>
            <Link
              to={`/session/edit/${session.id}`}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Details
            </Link>
          </div>
        </div>
      )}

      {/* Instructor */}
      {session.instructor_name && (
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-5 h-5 text-[var(--muted)]" />
            <h2 className="font-semibold text-lg">Instructor</h2>
          </div>
          <p className="text-[var(--text)]">{session.instructor_name}</p>
        </div>
      )}

      {/* ── ISC-7: Technique Details directly after Performance Score ── */}
      {session.techniques && Array.isArray(session.techniques) && session.techniques.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Book className="w-5 h-5 text-[var(--muted)]" />
            <h2 className="font-semibold text-lg">Techniques Practiced</h2>
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

      {session.session_techniques && Array.isArray(session.session_techniques) && session.session_techniques.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Technique Details</h2>
          <div className="space-y-4">
            {session.session_techniques.map((tech) => (
              <div key={tech.technique_number ?? tech.movement_name} className="border border-[var(--border)] rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-[var(--accent)]">
                    {tech.movement_name ?? `Technique #${tech.technique_number ?? '?'}`}
                  </h4>
                  <div className="flex items-center gap-2">
                    {/* ISC-29: Times previously trained */}
                    {tech.train_count != null && tech.train_count > 1 && (
                      <span className="text-xs px-2 py-1 bg-[rgba(var(--accent-rgb),0.1)] text-[var(--accent)] rounded">
                        {tech.train_count}x trained
                      </span>
                    )}
                    <span className="text-xs px-2 py-1 bg-[var(--surfaceElev)] rounded">
                      #{tech.technique_number ?? '?'}
                    </span>
                  </div>
                </div>
                {tech.notes && (
                  <p className="text-sm text-[var(--text)] mt-2 whitespace-pre-wrap">
                    {tech.notes}
                  </p>
                )}
                {tech.media_urls && Array.isArray(tech.media_urls) && tech.media_urls.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs font-semibold text-[var(--muted)]">Reference Media:</p>
                    {tech.media_urls.map((media) => (
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

      {/* ── ISC-8: Notes directly after Technique Details ── */}
      {session.notes && (
        <div className="card">
          <h2 className="font-semibold text-lg mb-3">Notes</h2>
          <p className="text-[var(--text)] whitespace-pre-wrap">
            {session.notes}
          </p>
        </div>
      )}

      {/* ── ISC-9: Roll Details after Notes ── */}
      {session.partners && Array.isArray(session.partners) && session.partners.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-[var(--muted)]" />
            <h2 className="font-semibold text-lg">Training Partners</h2>
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

      {session.detailed_rolls && Array.isArray(session.detailed_rolls) && session.detailed_rolls.length > 0 && (() => {
        // ISC-28: Compute per-partner submission record
        const partnerRecords: Record<string, { subsFor: number; subsAgainst: number; rolls: number }> = {};
        for (const roll of session.detailed_rolls) {
          if (!roll.partner_name) continue;
          const name = roll.partner_name;
          if (!partnerRecords[name]) partnerRecords[name] = { subsFor: 0, subsAgainst: 0, rolls: 0 };
          partnerRecords[name].rolls++;
          partnerRecords[name].subsFor += (roll.submissions_for && Array.isArray(roll.submissions_for)) ? roll.submissions_for.length : 0;
          partnerRecords[name].subsAgainst += (roll.submissions_against && Array.isArray(roll.submissions_against)) ? roll.submissions_against.length : 0;
        }

        return (
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-5 h-5 text-[var(--muted)]" />
              <h2 className="font-semibold text-lg">Roll Details</h2>
            </div>

            {/* Per-partner submission summary */}
            {Object.keys(partnerRecords).length > 0 && (
              <div className="flex flex-wrap gap-3 mb-4 pb-4 border-b border-[var(--border)]">
                {Object.entries(partnerRecords).map(([name, rec]) => (
                  <div key={name} className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                    <span className="font-medium text-[var(--text)]">{name}</span>
                    <span className="text-emerald-500 font-bold">{rec.subsFor}</span>
                    <span className="text-[var(--muted)]">-</span>
                    <span className="text-red-400 font-bold">{rec.subsAgainst}</span>
                    <span className="text-[var(--muted)]">({rec.rolls} {rec.rolls === 1 ? 'roll' : 'rolls'})</span>
                  </div>
                ))}
              </div>
            )}

            <div className="space-y-3">
              {(showAllRolls ? session.detailed_rolls : session.detailed_rolls.slice(0, 3))
                .filter((roll) => roll.partner_name)
                .map((roll) => (
                <div
                  key={roll.roll_number ?? roll.id}
                  className="flex items-center gap-4 p-3 rounded-lg"
                  style={{ backgroundColor: 'var(--surfaceElev)' }}
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                    {roll.roll_number ?? '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                      {roll.partner_name}
                    </p>
                    <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
                      {roll.duration_mins && <span>{roll.duration_mins} min</span>}
                      {roll.submissions_for && Array.isArray(roll.submissions_for) && roll.submissions_for.length > 0 && (
                        <span className="text-green-500">+{roll.submissions_for.length} sub</span>
                      )}
                      {roll.submissions_against && Array.isArray(roll.submissions_against) && roll.submissions_against.length > 0 && (
                        <span className="text-red-400">-{roll.submissions_against.length} sub</span>
                      )}
                    </div>
                    {roll.notes && (
                      <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>{roll.notes}</p>
                    )}
                  </div>
                </div>
              ))}
              {!showAllRolls && session.detailed_rolls.filter(r => r.partner_name).length > 3 && (
                <button
                  onClick={() => setShowAllRolls(true)}
                  className="w-full text-center text-sm font-medium py-2 rounded-lg transition-colors hover:opacity-80"
                  style={{ color: 'var(--accent)', backgroundColor: 'var(--surfaceElev)' }}
                >
                  Show all {session.detailed_rolls.filter(r => r.partner_name).length} rolls
                </button>
              )}
            </div>
          </div>
        );
      })()}

      {/* ── Session Biometrics Card (historical data on the session) ── */}
      {hasWhoop && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-5 h-5" style={{ color: '#8B5CF6' }} />
            <h2 className="font-semibold text-lg">Biometrics</h2>
          </div>

          {/* During Session — strain, HR, calories */}
          {hasWhoop && (
            <div className="mb-6">
              <p className="text-xs font-medium uppercase tracking-wide mb-3" style={{ color: 'var(--muted)' }}>During Session</p>

              {/* Strain gauge */}
              {session.whoop_strain != null && (
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-[var(--muted)]">Activity Strain</span>
                    <span className="text-2xl font-bold">{Number(session.whoop_strain).toFixed(1)}</span>
                  </div>
                  <div className="h-2.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, (session.whoop_strain / 21) * 100)}%`,
                        background: session.whoop_strain <= 7
                          ? 'linear-gradient(90deg, #22c55e, #86efac)'
                          : session.whoop_strain <= 14
                            ? 'linear-gradient(90deg, #eab308, #facc15)'
                            : session.whoop_strain <= 18
                              ? 'linear-gradient(90deg, #f97316, #fb923c)'
                              : 'linear-gradient(90deg, #ef4444, #f87171)',
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-[var(--muted)] mt-1">
                    <span>0</span>
                    <span>Light</span>
                    <span>Moderate</span>
                    <span>Hard</span>
                    <span>21</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {session.whoop_calories != null && (
                  <div className="p-3 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)] mb-1">Calories</p>
                    <p className="text-xl font-bold">{session.whoop_calories}</p>
                  </div>
                )}
                {session.whoop_avg_hr != null && (
                  <div className="p-3 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)] mb-1">Avg HR</p>
                    <p className="text-xl font-bold">{session.whoop_avg_hr} <span className="text-xs font-normal">bpm</span></p>
                  </div>
                )}
                {session.whoop_max_hr != null && (
                  <div className="p-3 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)] mb-1">Max HR</p>
                    <p className="text-xl font-bold">{session.whoop_max_hr} <span className="text-xs font-normal">bpm</span></p>
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      )}

      {/* ── Curriculum evidence bridge (MA-F1): one-tap confirms ── */}
      {evidenceCandidates.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Book className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Purple-belt evidence — this session matches {evidenceCandidates.length} slot
              {evidenceCandidates.length !== 1 ? 's' : ''}
            </h3>
          </div>
          <div className="space-y-2">
            {evidenceCandidates.map((c) => (
              <div
                key={c.slot_id}
                className="flex items-center justify-between gap-3 p-2.5 rounded-lg"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
                    {c.sequence || c.label}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    {c.kind === 'live'
                      ? `Live — ${c.matched_movement}${c.partner_ref ? ` on ${c.partner_ref}` : ''}`
                      : `Drilled — ${c.matched_movement}`}
                  </p>
                </div>
                <button
                  onClick={() => confirmEvidence(c)}
                  disabled={confirmingSlot === c.slot_id}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold shrink-0"
                  style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF', opacity: confirmingSlot === c.slot_id ? 0.6 : 1 }}
                >
                  {confirmingSlot === c.slot_id ? 'Logging…' : `Log ${c.kind}`}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Garmin biometrics (HR zones, training effect) ── */}
      <GarminPanel session={session} />

      {/* ── ISC-15: Achievement Badges below Biometrics ── */}
      <SessionInsights sessionId={session.id} />

      {/* ── ISC-16: Photos at bottom ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Camera className="w-5 h-5 text-[var(--muted)]" />
          <h2 className="font-semibold text-lg">Photos</h2>
          <span className="text-sm text-[var(--muted)]">({photoCount}/10)</span>
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
              setPhotoCount(photoCount + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
