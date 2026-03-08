import { Award, Flame, Target, Calendar, Users, Swords, Star, Zap, Shield, BookOpen } from 'lucide-react';

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  tier: 'bronze' | 'silver' | 'gold';
  earned: boolean;
  earned_date?: string;
  progress?: number;
  target?: number;
  category: string;
}

const TIER_COLORS = {
  bronze: { bg: '#CD7F32', text: '#FFFFFF', glow: 'rgba(205,127,50,0.3)' },
  silver: { bg: '#C0C0C0', text: '#1F2937', glow: 'rgba(192,192,192,0.3)' },
  gold: { bg: '#FFD700', text: '#1F2937', glow: 'rgba(255,215,0,0.3)' },
};

const ICON_MAP: Record<string, typeof Award> = {
  sessions: Calendar,
  streak: Flame,
  rolls: Target,
  subs: Swords,
  partners: Users,
  techniques: BookOpen,
  intensity: Zap,
  consistency: Shield,
  milestone: Star,
  default: Award,
};

// Default badge definitions for the achievement system
export const BADGE_DEFINITIONS: Omit<Badge, 'earned' | 'earned_date' | 'progress'>[] = [
  // Session milestones
  { id: 'sessions-10', name: 'Getting Started', description: 'Log 10 sessions', icon: 'sessions', tier: 'bronze', target: 10, category: 'Sessions' },
  { id: 'sessions-50', name: 'Dedicated', description: 'Log 50 sessions', icon: 'sessions', tier: 'silver', target: 50, category: 'Sessions' },
  { id: 'sessions-100', name: 'Centurion', description: 'Log 100 sessions', icon: 'sessions', tier: 'gold', target: 100, category: 'Sessions' },
  // Streak milestones
  { id: 'streak-4', name: 'Month Strong', description: '4-week training streak', icon: 'streak', tier: 'bronze', target: 4, category: 'Consistency' },
  { id: 'streak-12', name: 'Quarter Beast', description: '12-week training streak', icon: 'streak', tier: 'silver', target: 12, category: 'Consistency' },
  { id: 'streak-26', name: 'Half Year Warrior', description: '26-week training streak', icon: 'streak', tier: 'gold', target: 26, category: 'Consistency' },
  // Roll milestones
  { id: 'rolls-50', name: 'Roller', description: 'Log 50 rolls', icon: 'rolls', tier: 'bronze', target: 50, category: 'Rolling' },
  { id: 'rolls-200', name: 'Grinder', description: 'Log 200 rolls', icon: 'rolls', tier: 'silver', target: 200, category: 'Rolling' },
  { id: 'rolls-500', name: 'Mat Shark', description: 'Log 500 rolls', icon: 'rolls', tier: 'gold', target: 500, category: 'Rolling' },
  // Submission milestones
  { id: 'subs-10', name: 'Tap Collector', description: 'Catch 10 submissions', icon: 'subs', tier: 'bronze', target: 10, category: 'Submissions' },
  { id: 'subs-50', name: 'Submission Artist', description: 'Catch 50 submissions', icon: 'subs', tier: 'silver', target: 50, category: 'Submissions' },
  { id: 'subs-100', name: 'Submission Machine', description: 'Catch 100 submissions', icon: 'subs', tier: 'gold', target: 100, category: 'Submissions' },
  // Partner milestones
  { id: 'partners-5', name: 'Social Roller', description: 'Train with 5 different partners', icon: 'partners', tier: 'bronze', target: 5, category: 'Partners' },
  { id: 'partners-15', name: 'Connected', description: 'Train with 15 different partners', icon: 'partners', tier: 'silver', target: 15, category: 'Partners' },
  { id: 'partners-30', name: 'Gym Ambassador', description: 'Train with 30 different partners', icon: 'partners', tier: 'gold', target: 30, category: 'Partners' },
  // Technique milestones
  { id: 'techniques-5', name: 'Student', description: 'Log 5 different techniques', icon: 'techniques', tier: 'bronze', target: 5, category: 'Techniques' },
  { id: 'techniques-20', name: 'Diverse Game', description: 'Log 20 different techniques', icon: 'techniques', tier: 'silver', target: 20, category: 'Techniques' },
  { id: 'techniques-50', name: 'Encyclopedia', description: 'Log 50 different techniques', icon: 'techniques', tier: 'gold', target: 50, category: 'Techniques' },
];

interface BadgeDisplayProps {
  badges: Badge[];
  compact?: boolean;
}

export default function BadgeDisplay({ badges, compact = false }: BadgeDisplayProps) {
  const earned = badges.filter(b => b.earned);

  if (compact) {
    // Show only earned badges in a row (for profile)
    if (earned.length === 0) return null;
    return (
      <div className="flex flex-wrap gap-2">
        {earned.map(badge => (
          <BadgeIcon key={badge.id} badge={badge} size="sm" />
        ))}
      </div>
    );
  }

  // Group by category
  const categories = [...new Set(badges.map(b => b.category))];

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <span className="text-lg font-bold" style={{ color: 'var(--text)' }}>
            {earned.length}
          </span>
          <span className="text-sm" style={{ color: 'var(--muted)' }}>
            / {badges.length} earned
          </span>
        </div>
      </div>

      {/* Badges by category */}
      {categories.map(cat => {
        const catBadges = badges.filter(b => b.category === cat);
        return (
          <div key={cat}>
            <h4 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--muted)' }}>
              {cat}
            </h4>
            <div className="grid grid-cols-3 gap-3">
              {catBadges.map(badge => (
                <BadgeCard key={badge.id} badge={badge} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BadgeCard({ badge }: { badge: Badge }) {
  const tierColors = TIER_COLORS[badge.tier];
  const IconComponent = ICON_MAP[badge.icon] || ICON_MAP.default;
  const progressPct = badge.target && badge.progress != null
    ? Math.min(100, Math.round((badge.progress / badge.target) * 100))
    : badge.earned ? 100 : 0;

  return (
    <div
      className="rounded-[14px] p-3 text-center"
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        opacity: badge.earned ? 1 : 0.5,
      }}
    >
      {/* Icon */}
      <div
        className="w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center"
        style={{
          backgroundColor: badge.earned ? tierColors.bg : 'var(--surfaceElev)',
          boxShadow: badge.earned ? `0 0 12px ${tierColors.glow}` : 'none',
        }}
      >
        <IconComponent
          className="w-5 h-5"
          style={{ color: badge.earned ? tierColors.text : 'var(--muted)' }}
        />
      </div>

      {/* Name */}
      <p className="text-xs font-semibold truncate" style={{ color: 'var(--text)' }}>
        {badge.name}
      </p>

      {/* Description */}
      <p className="text-[10px] mt-0.5 truncate" style={{ color: 'var(--muted)' }}>
        {badge.description}
      </p>

      {/* Progress bar */}
      {!badge.earned && badge.target && (
        <div className="mt-2">
          <div className="w-full h-1 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${progressPct}%`, backgroundColor: 'var(--accent)' }}
            />
          </div>
          <p className="text-[9px] mt-0.5 tabular-nums" style={{ color: 'var(--muted)' }}>
            {badge.progress || 0} / {badge.target}
          </p>
        </div>
      )}

      {/* Earned date */}
      {badge.earned && badge.earned_date && (
        <p className="text-[9px] mt-1" style={{ color: 'var(--muted)' }}>
          {new Date(badge.earned_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
        </p>
      )}
    </div>
  );
}

function BadgeIcon({ badge, size = 'md' }: { badge: Badge; size?: 'sm' | 'md' }) {
  const tierColors = TIER_COLORS[badge.tier];
  const IconComponent = ICON_MAP[badge.icon] || ICON_MAP.default;
  const dim = size === 'sm' ? 'w-7 h-7' : 'w-10 h-10';
  const iconDim = size === 'sm' ? 'w-3.5 h-3.5' : 'w-5 h-5';

  return (
    <div
      className={`${dim} rounded-full flex items-center justify-center`}
      style={{
        backgroundColor: tierColors.bg,
        boxShadow: `0 0 8px ${tierColors.glow}`,
      }}
      title={`${badge.name}: ${badge.description}`}
    >
      <IconComponent className={iconDim} style={{ color: tierColors.text }} />
    </div>
  );
}
