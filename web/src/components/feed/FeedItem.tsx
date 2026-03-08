import { memo, useState } from 'react';
import { Calendar, Edit2, Eye, Lock, Moon, Trash2, Users2, Globe, ChevronDown, Dumbbell, Trophy, Flame, Zap } from 'lucide-react';
import ActivitySocialActions from '../ActivitySocialActions';
import CommentSection from '../CommentSection';
import PromotionCard from './PromotionCard';
import MilestoneCard from './MilestoneCard';
import BeltCelebration from './BeltCelebration';
import type { FeedItem } from '../../types';
import { ACTIVITY_COLORS, ACTIVITY_LABELS } from '../../constants/activity';

/* ── Score tier system ── */
const SCORE_TIERS: { min: number; label: string; color: string }[] = [
  { min: 85, label: 'Peak', color: 'var(--accent)' },
  { min: 70, label: 'Excellent', color: '#F59E0B' },
  { min: 50, label: 'Strong', color: '#10B981' },
  { min: 30, label: 'Solid', color: '#3B82F6' },
  { min: 0, label: 'Light', color: 'var(--muted)' },
];

function getScoreTier(score: number) {
  for (const tier of SCORE_TIERS) {
    if (score >= tier.min) return tier;
  }
  return SCORE_TIERS[SCORE_TIERS.length - 1];
}

/** Parse attendees from session data */
function getAttendeeNames(data: FeedItem['data']): string[] {
  if (!data?.attendees) return [];
  if (Array.isArray(data.attendees)) {
    return data.attendees.filter(Boolean);
  }
  if (typeof data.attendees === 'string') {
    try {
      const parsed = JSON.parse(data.attendees);
      if (Array.isArray(parsed)) return parsed.filter(Boolean);
    } catch {
      // Not JSON, treat as comma-separated
      return data.attendees.split(',').map(s => s.trim()).filter(Boolean);
    }
  }
  return [];
}

/** Get partner names from session data */
function getPartnerNames(data: FeedItem['data']): string[] {
  const names = new Set<string>();
  if (data?.session_rolls && Array.isArray(data.session_rolls)) {
    for (const roll of data.session_rolls) {
      if (roll.partner_name) names.add(roll.partner_name);
    }
  }
  if (data?.partners && Array.isArray(data.partners)) {
    for (const name of data.partners) {
      if (name) names.add(name);
    }
  }
  return Array.from(names);
}

/** Capitalize class type names in feed summary text */
function formatSummary(summary: string): string {
  return summary
    .replace(/\bno-gi\b/gi, 'No-Gi')
    .replace(/\bgi\b/g, 'Gi')
    .replace(/\bs&c\b/gi, 'S&C')
    .replace(/\bmma\b/gi, 'MMA');
}

/** Compute contextual achievements from session data */
function getAchievements(item: FeedItem): { icon: typeof Trophy; label: string; color: string }[] {
  const badges: { icon: typeof Trophy; label: string; color: string }[] = [];
  const data = item.data;
  if (!data) return badges;

  const score = data.session_score;
  if (score != null && score >= 85) {
    badges.push({ icon: Trophy, label: 'Peak Session', color: 'var(--accent)' });
  }
  if (data.duration_mins && data.duration_mins >= 120) {
    badges.push({ icon: Flame, label: 'Endurance', color: '#F59E0B' });
  }
  if (data.rolls && data.rolls >= 8) {
    badges.push({ icon: Zap, label: `${data.rolls} Rolls`, color: '#8B5CF6' });
  }
  const subs = (data.submissions_for || 0);
  if (subs >= 3) {
    badges.push({ icon: Trophy, label: `${subs} Subs`, color: '#10B981' });
  }
  if (data.class_type === 'competition') {
    badges.push({ icon: Trophy, label: 'Competition', color: '#EC4899' });
  }

  return badges.slice(0, 3);
}

/* ── Gradient Score Bar ── */
function GradientScoreBar({ score }: { score: number }) {
  const tier = getScoreTier(score);
  const pct = Math.min(100, Math.max(0, score));

  return (
    <div className="mt-2.5 mb-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: tier.color }}>
          {tier.label}
        </span>
        <span className="text-[10px] font-bold tabular-nums" style={{ color: 'var(--muted)' }}>
          {Math.round(score)}/100
        </span>
      </div>
      <div className="h-1.5 rounded-full w-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <div
          className="h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: tier.color }}
        />
      </div>
    </div>
  );
}

/* ── Hero Metric Row (Strava-style) ── */
function HeroMetrics({ duration, rolls, score }: { duration?: number; rolls?: number; score?: number | null }) {
  const metrics: { value: string; label: string }[] = [];

  if (duration) {
    const h = Math.floor(duration / 60);
    const m = duration % 60;
    metrics.push({ value: h > 0 ? `${h}h ${m}m` : `${m}m`, label: 'Duration' });
  }
  if (rolls != null && rolls > 0) {
    metrics.push({ value: String(rolls), label: 'Rolls' });
  }
  if (score != null) {
    metrics.push({ value: String(Math.round(score)), label: 'Score' });
  }

  if (metrics.length === 0) return null;

  return (
    <div className="flex items-center gap-6 mt-3">
      {metrics.map((m, i) => (
        <div key={i}>
          <p className="text-lg font-bold tabular-nums leading-tight" style={{ color: 'var(--text)' }}>
            {m.value}
          </p>
          <p className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
            {m.label}
          </p>
        </div>
      ))}
    </div>
  );
}

/* ── Achievement Badges ── */
function AchievementBadges({ achievements }: { achievements: { icon: typeof Trophy; label: string; color: string }[] }) {
  if (achievements.length === 0) return null;
  return (
    <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
      {achievements.map((a, i) => {
        const Icon = a.icon;
        return (
          <span
            key={i}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
            style={{ backgroundColor: `${a.color}15`, color: a.color }}
          >
            <Icon className="w-3 h-3" />
            {a.label}
          </span>
        );
      })}
    </div>
  );
}

/* ── Score Breakdown Mini Bars ── */
function ScoreBreakdown({ breakdown }: { breakdown: Record<string, unknown> }) {
  const pillars = (breakdown as { pillars?: Record<string, { score: number; max: number; pct: number }> })?.pillars;
  if (!pillars) return null;

  const PILLAR_LABELS: Record<string, string> = {
    technique: 'Technique',
    intensity: 'Intensity',
    consistency: 'Consistency',
    progression: 'Progression',
    duration: 'Duration',
    volume: 'Volume',
    engagement: 'Engagement',
    effort: 'Effort',
    effectiveness: 'Effectiveness',
    readiness_alignment: 'Readiness',
    biometric_validation: 'Biometrics',
  };

  /** Normalize label from snake_case key */
  function formatPillarLabel(key: string): string {
    if (PILLAR_LABELS[key]) return PILLAR_LABELS[key];
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
        Score Breakdown
      </p>
      {Object.entries(pillars).map(([key, pillar]) => {
        // pct may be 0-1 or 0-100 — normalize to 0-100
        const rawPct = pillar.pct > 1 ? pillar.pct : pillar.pct * 100;
        const pct = Math.min(100, Math.max(0, Math.round(rawPct)));
        const barColor = pct >= 70 ? '#10B981' : pct >= 40 ? '#F59E0B' : '#EF4444';
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-[11px] w-24 shrink-0 truncate" style={{ color: 'var(--muted)' }}>
              {formatPillarLabel(key)}
            </span>
            <div className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div
                className="h-1.5 rounded-full"
                style={{ width: `${pct}%`, backgroundColor: barColor }}
              />
            </div>
            <span className="text-[10px] tabular-nums w-8 text-right" style={{ color: 'var(--muted)' }}>
              {pct}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Technique Chips ── */
function TechniqueChips({ techniques }: { techniques: string[] }) {
  if (techniques.length === 0) return null;
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--muted)' }}>
        Techniques
      </p>
      <div className="flex flex-wrap gap-1.5">
        {techniques.map((t, i) => (
          <span
            key={i}
            className="px-2 py-0.5 rounded-full text-[11px] font-medium"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

export interface FeedItemComponentProps {
  item: FeedItem;
  prevItem: FeedItem | null;
  view: 'my' | 'friends';
  currentUserId: number | null;
  navigate: (path: string) => void;
  expandedComments: Set<string>;
  handleLike: (type: string, id: number) => void;
  handleUnlike: (type: string, id: number) => void;
  toggleComments: (type: string, id: number) => void;
  formatDate: (date: string) => string;
  shouldShowSocialActions: (item: FeedItem) => boolean;
  isActivityEditable: (item: FeedItem) => boolean;
  handleVisibilityChange: (type: string, id: number, visibility: string) => void;
  handleDeleteRest: (id: number) => void;
}

const FeedItemComponent = memo(function FeedItemComponent({
  item,
  prevItem,
  view,
  currentUserId,
  navigate,
  expandedComments,
  handleLike,
  handleUnlike,
  toggleComments,
  formatDate,
  shouldShowSocialActions,
  isActivityEditable,
  handleVisibilityChange,
  handleDeleteRest,
}: FeedItemComponentProps) {
  const [expanded, setExpanded] = useState(false);
  const [celebrationOpen, setCelebrationOpen] = useState(false);
  const showDateHeader = !prevItem || prevItem.date !== item.date;
  const commentKey = `${item.type}-${item.id}`;
  const isCommentsOpen = expandedComments.has(commentKey);

  const isFriend = !!(item.owner_user_id && currentUserId && item.owner_user_id !== currentUserId);
  const ownerName = item.owner
    ? `${item.owner.first_name || ''} ${item.owner.last_name || ''}`.trim()
    : '';
  const ownerInitial = ownerName ? ownerName[0].toUpperCase() : '?';

  const isPromotion = item.type === 'promotion';
  const isMilestone = item.type === 'milestone';
  const isRest = item.type === 'rest';
  const classType = item.data?.class_type?.toLowerCase() ?? '';
  const activityColor = ACTIVITY_COLORS[classType] || 'var(--accent)';
  const achievements = isRest ? [] : getAchievements(item);

  const getRestTypeStyle = (type: string): React.CSSProperties => {
    const styles: Record<string, React.CSSProperties> = {
      'active': { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' },
      'passive': { backgroundColor: 'rgba(107,114,128,0.1)', color: '#6b7280' },
      'full': { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7' },
      'injury': { backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)' },
      'sick': { backgroundColor: 'rgba(234,179,8,0.1)', color: '#ca8a04' },
      'travel': { backgroundColor: 'rgba(34,197,94,0.1)', color: '#16a34a' },
      'life': { backgroundColor: 'rgba(156,163,175,0.1)', color: '#6b7280' },
    };
    return styles[type] || { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' };
  };

  const getRestTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'active': '\u{1F3C3} Active Recovery',
      'passive': '\u{1F6B6} Passive Recovery',
      'full': '\u{1F6CC} Full Rest',
      'injury': '\u{1F915} Injury / Rehab',
      'sick': '\u{1F912} Sick Day',
      'travel': '\u{2708}\u{FE0F} Travelling',
      'life': '\u{1F937} Life Got in the Way',
    };
    return labels[type] || type || 'Rest';
  };

  // Expandable detail content for sessions
  const partnerNames = !isRest ? getPartnerNames(item.data) : [];
  const attendeeNames = !isRest ? getAttendeeNames(item.data) : [];
  const techniques = (!isRest && item.data?.techniques && Array.isArray(item.data.techniques)) ? item.data.techniques : [];
  const hasExpandableContent = !isRest && (
    (item.data?.score_breakdown && typeof item.data.score_breakdown === 'object') ||
    techniques.length > 0 ||
    partnerNames.length > 0 ||
    attendeeNames.length > 0 ||
    item.data?.notes
  );

  return (
    <div>
      {showDateHeader && (
        <div className="flex items-center gap-3 mb-3 mt-6 first:mt-0">
          <Calendar className="w-4 h-4 text-[var(--muted)]" />
          <h3 className="text-sm font-semibold text-[var(--text)] uppercase tracking-wide">
            {formatDate(item.date)}
          </h3>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>
      )}

      <div
        className="rounded-[14px] overflow-hidden"
        role="article"
        aria-label={item.summary}
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
        }}
      >
        {/* Friend name header */}
        {isFriend && ownerName && (
          <div className="px-4 pt-3 pb-0">
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => navigate(`/users/${item.owner_user_id}`)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
              >
                {ownerInitial}
              </button>
              <div className="flex items-center gap-1.5 min-w-0">
                <button
                  onClick={() => navigate(`/users/${item.owner_user_id}`)}
                  className="text-sm font-semibold truncate hover:underline"
                  style={{ color: 'var(--text)' }}
                >
                  {ownerName}
                </button>
                <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
                  · {formatDate(item.date)}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="p-4">
          {isPromotion ? (
            <>
              <div
                className="cursor-pointer"
                onClick={() => setCelebrationOpen(true)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setCelebrationOpen(true)}
              >
                <PromotionCard
                  grade={item.grade || ''}
                  date={item.date}
                  professor={item.professor}
                  sessionsSinceLastPromotion={item.sessions_since_last}
                  hoursSinceLastPromotion={item.hours_since_last}
                  rollsSinceLastPromotion={item.rolls_since_last}
                />
              </div>
              <BeltCelebration
                isOpen={celebrationOpen}
                onClose={() => setCelebrationOpen(false)}
                grade={item.grade || ''}
                date={item.date}
                professor={item.professor}
                sessionsSincePromotion={item.sessions_since_last}
                hoursSincePromotion={item.hours_since_last}
                rollsSincePromotion={item.rolls_since_last}
                userName={isFriend ? ownerName : undefined}
              />
            </>
          ) : isMilestone ? (
            <MilestoneCard
              label={item.milestone_label || item.summary}
              type={item.milestone_type}
              value={item.milestone_value}
            />
          ) : isRest ? (
            /* ═══ Rest day card (unchanged) ═══ */
            <>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Moon className="w-5 h-5 text-purple-500" />
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                    {formatSummary(item.summary)}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {view === 'my' && (
                    <>
                      <button
                        onClick={() => navigate(`/rest/${item.date}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="View rest day"
                      >
                        <Eye className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => navigate(`/rest/edit/${item.date}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Edit rest day"
                      >
                        <Edit2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => handleDeleteRest(item.id)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Delete rest day"
                      >
                        <Trash2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {item.data?.rest_type && (
                <span
                  className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold mb-2"
                  style={getRestTypeStyle(item.data.rest_type)}
                >
                  {getRestTypeLabel(item.data.rest_type)}
                </span>
              )}

              {item.data?.rest_note && (
                <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
                  {item.data.rest_note}
                </p>
              )}

              {item.data?.tomorrow_intention && (
                <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  Tomorrow: {item.data.tomorrow_intention}
                </div>
              )}
            </>
          ) : (
            /* ═══ Session card — redesigned two-tier layout ═══ */
            <>
              {/* ── Header: Session identity + actions ── */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  {/* Activity type icon */}
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: `${activityColor}15` }}
                  >
                    <Dumbbell className="w-4.5 h-4.5" style={{ color: activityColor }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-bold leading-tight" style={{ color: 'var(--text)' }}>
                      {ACTIVITY_LABELS[classType] || item.data?.class_type || 'Session'}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      {item.data?.class_time && (
                        <span className="text-xs" style={{ color: 'var(--muted)' }}>
                          {item.data.class_time}
                        </span>
                      )}
                      {item.data?.class_time && item.data?.gym_name && (
                        <span className="text-xs" style={{ color: 'var(--border)' }}>&middot;</span>
                      )}
                      {item.data?.gym_name && (
                        <span className="text-xs truncate" style={{ color: 'var(--muted)' }}>
                          {item.data.gym_name}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-1.5 shrink-0">
                  {isActivityEditable(item) && (
                    <>
                      <button
                        onClick={() => navigate(`/session/${item.id}`)}
                        className="p-1.5 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="View session details"
                      >
                        <Eye className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => navigate(`/session/edit/${item.id}`)}
                        className="p-1.5 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Edit session"
                      >
                        <Edit2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                    </>
                  )}
                  {isActivityEditable(item) && (() => {
                    const vis = item.data?.visibility_level || item.data?.visibility || 'summary';
                    const options = [
                      { value: 'private', icon: Lock, label: 'Private' },
                      { value: 'summary', icon: Users2, label: 'Friends' },
                      { value: 'full', icon: Globe, label: 'Public' },
                    ] as const;
                    return (
                      <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }} role="group" aria-label="Visibility">
                        {options.map(opt => {
                          const Icon = opt.icon;
                          const active = vis === opt.value;
                          return (
                            <button
                              key={opt.value}
                              onClick={() => handleVisibilityChange(item.type, item.id, opt.value)}
                              className="p-1.5 transition-colors"
                              style={{
                                backgroundColor: active ? 'var(--accent)' : 'transparent',
                                color: active ? '#FFFFFF' : 'var(--muted)',
                                opacity: active ? 1 : 0.5,
                              }}
                              title={opt.label}
                              aria-label={opt.label}
                              aria-pressed={active}
                            >
                              <Icon className="w-3.5 h-3.5" />
                            </button>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              </div>

              {/* ── Gradient score bar ── */}
              {item.data?.session_score != null && (
                <GradientScoreBar score={item.data.session_score} />
              )}

              {/* ── Hero metrics row (Strava-style bold numbers) ── */}
              <HeroMetrics
                duration={item.data?.duration_mins}
                rolls={item.data?.rolls}
                score={item.data?.session_score}
              />

              {/* ── Achievement badges ── */}
              <AchievementBadges achievements={achievements} />

              {/* ── Photo (contained, not background) ── */}
              {item.thumbnail && (
                <div
                  className="mt-3 cursor-pointer"
                  onClick={() => navigate(`/session/${item.id}`)}
                >
                  <div className="relative">
                    <img
                      src={item.thumbnail}
                      alt="Session photo"
                      loading="lazy"
                      className="w-full max-h-56 rounded-lg object-cover border border-[var(--border)]"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                    {(item.photo_count ?? 0) > 1 && (
                      <span className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded-full font-medium">
                        +{(item.photo_count ?? 1) - 1}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* ── Notes preview (collapsed) ── */}
              {item.data?.notes && !expanded && (
                <p className="text-sm mt-2.5 line-clamp-2 italic" style={{ color: 'var(--text)', opacity: 0.8 }}>
                  &ldquo;{item.data.notes}&rdquo;
                </p>
              )}

              {/* ── Expand/collapse toggle ── */}
              {hasExpandableContent && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 mt-2.5 text-xs font-medium"
                  style={{ color: 'var(--accent)' }}
                >
                  <ChevronDown
                    className="w-3.5 h-3.5 transition-transform"
                    style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
                  />
                  {expanded ? 'Less detail' : 'More detail'}
                </button>
              )}

              {/* ── Expanded detail panel ── */}
              {expanded && (
                <div
                  className="mt-3 pt-3 space-y-3"
                  style={{ borderTop: '1px solid var(--border)' }}
                >
                  {/* Score breakdown */}
                  {item.data?.score_breakdown && typeof item.data.score_breakdown === 'object' && (
                    <ScoreBreakdown breakdown={item.data.score_breakdown} />
                  )}

                  {/* Technique chips */}
                  {techniques.length > 0 && <TechniqueChips techniques={techniques} />}

                  {/* Rolling partners */}
                  {partnerNames.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                        Rolling Partners
                      </p>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {partnerNames.map((name, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
                          >
                            <Users2 className="w-3 h-3" style={{ color: 'var(--muted)' }} />
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* In Class (attendees) */}
                  {attendeeNames.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                        In Class
                      </p>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {attendeeNames.map((name, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                            style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: '#3B82F6' }}
                          >
                            <Users2 className="w-3 h-3" style={{ color: '#3B82F6' }} />
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full notes */}
                  {item.data?.notes && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                        Notes
                      </p>
                      <p className="text-sm" style={{ color: 'var(--text)' }}>
                        {item.data.notes}
                      </p>
                    </div>
                  )}

                  {/* Submissions stats */}
                  {((item.data?.submissions_for ?? 0) > 0 || (item.data?.submissions_against ?? 0) > 0) && (
                    <div className="flex items-center gap-4">
                      {(item.data?.submissions_for ?? 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
                            Subs For
                          </span>
                          <span className="text-sm font-bold" style={{ color: '#10B981' }}>
                            {item.data?.submissions_for}
                          </span>
                        </div>
                      )}
                      {(item.data?.submissions_against ?? 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
                            Subs Against
                          </span>
                          <span className="text-sm font-bold" style={{ color: '#EF4444' }}>
                            {item.data?.submissions_against}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {item.data?.tomorrow_intention && (
                <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  Tomorrow: {item.data.tomorrow_intention}
                </div>
              )}
            </>
          )}

          {/* Social actions bar — only for session/rest types */}
          {shouldShowSocialActions(item) && currentUserId && (item.type === 'session' || item.type === 'rest') && (
            <>
              <ActivitySocialActions
                activityType={item.type}
                activityId={item.id}
                likeCount={item.like_count || 0}
                commentCount={item.comment_count || 0}
                hasLiked={item.has_liked || false}
                onLike={() => handleLike(item.type, item.id)}
                onUnlike={() => handleUnlike(item.type, item.id)}
                onToggleComments={() => toggleComments(item.type, item.id)}
              />

              <CommentSection
                activityType={item.type}
                activityId={item.id}
                currentUserId={currentUserId}
                isOpen={isCommentsOpen}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
});

export default FeedItemComponent;
