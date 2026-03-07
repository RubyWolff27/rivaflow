import { useState, useEffect, useMemo } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { Link } from 'react-router-dom';
import { sessionsApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Session } from '../types';
import { Calendar, MapPin, Clock, Activity, Target, Filter, Search, Zap } from 'lucide-react';
import { CardSkeleton, EmptyState } from '../components/ui';
import { useToast } from '../contexts/ToastContext';
import MiniZoneBar from '../components/MiniZoneBar';
import SessionScoreBadge from '../components/sessions/SessionScoreBadge';
import { formatClassType, ACTIVITY_COLORS } from '../constants/activity';
import { pluralize } from '../utils/text';
import { GYM_TYPES, SPARRING_TYPES } from '../components/sessions/sessionTypes';

type ZoneData = { zone_durations: Record<string, number> | null; strain: number | null; calories: number | null; score_state: string | null; recovery_score?: number | null };

const SESSIONS_PER_PAGE = 20;

/** One-line session story for list cards. */
function sessionStoryPreview(session: Session): string {
  const duration = session.duration_mins ?? 0;
  const classType = formatClassType(session.class_type);
  const rolls = session.rolls ?? 0;
  let story = `${duration}min ${classType}`;
  if (rolls > 0) story += ` · ${rolls} roll${rolls !== 1 ? 's' : ''}`;
  if (session.whoop_strain != null) story += ` · Strain ${Number(session.whoop_strain).toFixed(1)}`;
  return story;
}

export default function Sessions() {
  usePageTitle('Sessions');
  const toast = useToast();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'duration' | 'intensity'>('date');
  const [zoneMap, setZoneMap] = useState<Record<string, ZoneData | null>>({});
  const [visibleCount, setVisibleCount] = useState(SESSIONS_PER_PAGE);

  useEffect(() => {
    const controller = new AbortController();
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await sessionsApi.list(200);
        if (!controller.signal.aborted) {
          const loaded = response.data ?? [];
          setSessions(loaded);
          // Fetch zone data for first 50 sessions
          const ids = loaded.slice(0, 50).map(s => s.id);
          if (ids.length > 0) {
            try {
              const zRes = await whoopApi.getZonesBatch(ids);
              if (!controller.signal.aborted && zRes.data?.zones) {
                setZoneMap(zRes.data.zones);
              }
            } catch (err) { logger.debug('WHOOP not connected', err); }
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          logger.error('Error loading sessions:', error);
          toast.error('Failed to load sessions');
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    doLoad();
    return () => { controller.abort(); };
  }, []);

  const filteredSessions = useMemo(() => {
    let filtered = [...sessions];

    // Apply search filter
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(s =>
        s.gym_name?.toLowerCase().includes(lowerSearch) ||
        s.location?.toLowerCase().includes(lowerSearch) ||
        s.notes?.toLowerCase().includes(lowerSearch)
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(s => s.class_type === filterType);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.session_date).getTime() - new Date(a.session_date).getTime();
      } else if (sortBy === 'duration') {
        return (b.duration_mins ?? 0) - (a.duration_mins ?? 0);
      } else if (sortBy === 'intensity') {
        return (b.intensity ?? 0) - (a.intensity ?? 0);
      }
      return 0;
    });

    return filtered;
  }, [sessions, searchTerm, filterType, sortBy]);

  // Reset pagination when filters/search change
  useEffect(() => {
    setVisibleCount(SESSIONS_PER_PAGE);
  }, [searchTerm, filterType, sortBy]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const uniqueClassTypes = useMemo(
    () => Array.from(new Set(sessions.map(s => s.class_type))),
    [sessions]
  );

  const stats = useMemo(() => {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    startOfWeek.setHours(0, 0, 0, 0);
    const startOfLastWeek = new Date(startOfWeek);
    startOfLastWeek.setDate(startOfLastWeek.getDate() - 7);

    const thisWeek = sessions.filter(s => new Date(s.session_date) >= startOfWeek);
    const lastWeek = sessions.filter(s => {
      const d = new Date(s.session_date);
      return d >= startOfLastWeek && d < startOfWeek;
    });

    // Average score this week vs last week
    const scoredThisWeek = thisWeek.filter(s => s.session_score != null && s.session_score > 0);
    const scoredLastWeek = lastWeek.filter(s => s.session_score != null && s.session_score > 0);
    const avgScoreThisWeek = scoredThisWeek.length > 0
      ? scoredThisWeek.reduce((sum, s) => sum + (s.session_score ?? 0), 0) / scoredThisWeek.length
      : 0;
    const avgScoreLastWeek = scoredLastWeek.length > 0
      ? scoredLastWeek.reduce((sum, s) => sum + (s.session_score ?? 0), 0) / scoredLastWeek.length
      : 0;

    // Training streak (consecutive days with at least one session)
    let streak = 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const sessionDates = new Set(sessions.map(s => new Date(s.session_date).toDateString()));
    for (let d = new Date(today); ; d.setDate(d.getDate() - 1)) {
      if (sessionDates.has(d.toDateString())) {
        streak++;
      } else {
        // Allow skipping today if no session yet
        if (d.getTime() === today.getTime()) continue;
        break;
      }
    }

    // Weekly hours comparison
    const hoursThisWeek = thisWeek.reduce((sum, s) => sum + (s.duration_mins ?? 0), 0) / 60;
    const hoursLastWeek = lastWeek.reduce((sum, s) => sum + (s.duration_mins ?? 0), 0) / 60;

    return {
      sessionsThisWeek: thisWeek.length,
      avgScore: avgScoreThisWeek,
      scoreTrend: avgScoreThisWeek - avgScoreLastWeek,
      streak,
      hoursThisWeek,
      hoursLastWeek,
    };
  }, [sessions]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} lines={1} />)}
        </div>
        <CardSkeleton lines={2} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} lines={3} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2" id="page-title">All Sessions</h1>
        <p className="text-[var(--muted)]">View and manage your training history</p>
      </div>

      {/* ISC-22,23,24,25: Trailing Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-[var(--muted)] mb-1">This Week</p>
          <p className="text-2xl font-bold text-[var(--text)]">{stats.sessionsThisWeek} <span className="text-sm font-normal text-[var(--muted)]">{stats.sessionsThisWeek === 1 ? 'session' : 'sessions'}</span></p>
        </div>
        <div className="card">
          <p className="text-sm text-[var(--muted)] mb-1">Avg Score</p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-[var(--text)]">{stats.avgScore > 0 ? Math.round(stats.avgScore) : '—'}</p>
            {stats.scoreTrend !== 0 && stats.avgScore > 0 && (
              <span className={`text-sm font-medium ${stats.scoreTrend > 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                {stats.scoreTrend > 0 ? '↑' : '↓'}{Math.abs(Math.round(stats.scoreTrend))}
              </span>
            )}
          </div>
        </div>
        <div className="card">
          <p className="text-sm text-[var(--muted)] mb-1">Streak</p>
          <p className="text-2xl font-bold text-[var(--text)]">{stats.streak} <span className="text-sm font-normal text-[var(--muted)]">{stats.streak === 1 ? 'day' : 'days'}</span></p>
        </div>
        <div className="card">
          <p className="text-sm text-[var(--muted)] mb-1">Weekly Hours</p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-[var(--text)]">{stats.hoursThisWeek.toFixed(1)}</p>
            {stats.hoursLastWeek > 0 && (
              <span className="text-xs text-[var(--muted)]">
                vs {stats.hoursLastWeek.toFixed(1)} last wk
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 w-full"
            />
          </div>

          {/* Filter by Type */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input pl-10 w-full"
              aria-label="Filter by class type"
            >
              <option value="all">All Types</option>
              {uniqueClassTypes.map(type => (
                <option key={type} value={type}>{formatClassType(type)}</option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'date' | 'duration' | 'intensity')}
            className="input w-full"
            aria-label="Sort sessions by"
          >
            <option value="date">Sort by Date</option>
            <option value="duration">Sort by Duration</option>
            <option value="intensity">Sort by Intensity</option>
          </select>
        </div>
      </div>

      {/* Sessions List */}
      {filteredSessions.length === 0 ? (
        <EmptyState
          icon={Activity}
          title={searchTerm || filterType !== 'all' ? 'No sessions match your filters' : 'No sessions logged yet'}
          description={searchTerm || filterType !== 'all' ? 'Try adjusting your search or filter criteria.' : 'Start training and log your first session!'}
          actionLabel={searchTerm || filterType !== 'all' ? undefined : 'Log Session'}
          actionPath={searchTerm || filterType !== 'all' ? undefined : '/log'}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSessions.slice(0, visibleCount).map((session) => (
              <Link
                key={session.id}
                to={`/session/${session.id}`}
                className="card hover:shadow-lg transition-shadow"
                role="article"
                aria-label={`${formatClassType(session.class_type)} session${GYM_TYPES.includes(session.class_type) && session.gym_name ? ` at ${session.gym_name}` : ''} on ${formatDate(session.session_date)}`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                        style={{
                          backgroundColor: (ACTIVITY_COLORS[session.class_type] || 'var(--accent)') + '1A',
                          color: ACTIVITY_COLORS[session.class_type] || 'var(--accent)',
                        }}
                      >
                        {formatClassType(session.class_type)}
                      </span>
                      {session.needs_review && (
                        <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded text-xs font-semibold">
                          Review
                        </span>
                      )}
                      {session.intensity > 0 && (
                        <span
                          className="text-xs font-medium"
                          style={{ color: session.intensity >= 4 ? '#EF4444' : session.intensity === 3 ? '#F59E0B' : '#10B981' }}
                        >
                          Intensity: {session.intensity}/5
                        </span>
                      )}
                    </div>
                    {GYM_TYPES.includes(session.class_type) && session.gym_name && (
                      <h3 className="font-semibold text-[var(--text)]">
                        {session.gym_name}
                      </h3>
                    )}
                    {session.location && (
                      <p className="flex items-center gap-1 text-xs text-[var(--muted)] mt-1">
                        <MapPin className="w-3 h-3" />
                        {session.location}
                      </p>
                    )}
                  </div>
                  <SessionScoreBadge score={session.session_score} size="md" />
                </div>

                {/* Stats */}
                <div className={`grid grid-cols-1 ${SPARRING_TYPES.includes(session.class_type) ? 'sm:grid-cols-3' : 'sm:grid-cols-2'} gap-3 py-3 border-t border-[var(--border)]`}>
                  <div>
                    <div className="flex items-center gap-1 text-xs text-[var(--muted)] mb-1">
                      <Calendar className="w-3 h-3" />
                      Date
                    </div>
                    <p className="text-sm font-semibold">{formatDate(session.session_date)}</p>
                    {session.class_time && (
                      <p className="text-xs text-[var(--muted)]">{session.class_time}</p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-1 text-xs text-[var(--muted)] mb-1">
                      <Clock className="w-3 h-3" />
                      Duration
                    </div>
                    <p className="text-sm font-semibold">{session.duration_mins} min</p>
                  </div>
                  {SPARRING_TYPES.includes(session.class_type) && (
                    <div>
                      <div className="flex items-center gap-1 text-xs text-[var(--muted)] mb-1">
                        <Activity className="w-3 h-3" />
                        Rolls
                      </div>
                      <p className="text-sm font-semibold">{session.rolls}</p>
                    </div>
                  )}
                </div>

                {/* Submissions — sparring types only */}
                {SPARRING_TYPES.includes(session.class_type) && (
                  <div className="flex items-center gap-2 pt-2 border-t border-[var(--border)]">
                    <Target className="w-4 h-4 text-[var(--muted)]" />
                    <span className="text-sm text-[var(--muted)]">
                      <span className="font-semibold text-emerald-500">{session.submissions_for}</span>
                      {' / '}
                      <span className="font-semibold text-[var(--error)]">{session.submissions_against}</span>
                      {' '}{pluralize((session.submissions_for ?? 0) + (session.submissions_against ?? 0), 'submission')}
                    </span>
                  </div>
                )}

                {/* ISC-18,19: Strain + Recovery indicators */}
                {(session.whoop_strain != null || zoneMap[String(session.id)]?.recovery_score != null) && (
                  <div className="flex items-center gap-3 pt-2 border-t border-[var(--border)]">
                    {session.whoop_strain != null && (
                      <span
                        className="px-2 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"
                        style={{
                          backgroundColor: session.whoop_strain <= 7 ? '#10B98120' : session.whoop_strain <= 14 ? '#F59E0B20' : '#EF444420',
                          color: session.whoop_strain <= 7 ? '#10B981' : session.whoop_strain <= 14 ? '#F59E0B' : '#EF4444',
                        }}
                      >
                        <Zap className="w-3 h-3" />
                        {Number(session.whoop_strain).toFixed(1)}
                      </span>
                    )}
                    {zoneMap[String(session.id)]?.recovery_score != null && (() => {
                      const score = zoneMap[String(session.id)]!.recovery_score!;
                      const color = score >= 67 ? '#10B981' : score >= 34 ? '#F59E0B' : '#EF4444';
                      return (
                        <span className="flex items-center gap-1 text-xs">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                          <span style={{ color }}>{Math.round(score)}%</span>
                        </span>
                      );
                    })()}
                  </div>
                )}

                {/* ISC-30: Session story preview */}
                <p className="text-xs text-[var(--muted)] mt-2">
                  {sessionStoryPreview(session)}
                </p>

                {/* HR Zone Mini Bar */}
                {zoneMap[String(session.id)]?.zone_durations && (
                  <div className="pt-2 border-t border-[var(--border)]">
                    <MiniZoneBar zones={zoneMap[String(session.id)]!.zone_durations!} />
                  </div>
                )}
              </Link>
            ))}
          </div>

          {visibleCount < filteredSessions.length && (
            <div className="flex justify-center">
              <button
                className="btn-secondary"
                onClick={() => setVisibleCount(prev => prev + SESSIONS_PER_PAGE)}
              >
                Show More ({filteredSessions.length - visibleCount} more)
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
