import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi } from '../api/client';
import { logger } from '../utils/logger';
import { Award } from 'lucide-react';
import { CardSkeleton } from '../components/ui';
import BadgeDisplay, { BADGE_DEFINITIONS } from '../components/achievements/BadgeDisplay';
import type { Badge } from '../components/achievements/BadgeDisplay';

export default function Achievements() {
  usePageTitle('Achievements');
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        // Fetch user stats to compute badge progress
        const [perfRes, partnerRes, techRes, consistRes] = await Promise.allSettled([
          analyticsApi.performanceOverview(),
          analyticsApi.partnerStats(),
          analyticsApi.techniqueBreakdown(),
          analyticsApi.consistencyMetrics(),
        ]);

        if (cancelled) return;

        const perf = perfRes.status === 'fulfilled' ? perfRes.value.data : {};
        const partners = partnerRes.status === 'fulfilled' ? partnerRes.value.data : {};
        const techs = techRes.status === 'fulfilled' ? techRes.value.data : {};
        const consist = consistRes.status === 'fulfilled' ? consistRes.value.data : {};

        // Extract values
        const totalSessions = Number(perf?.total_sessions || perf?.sessions_count || 0);
        const totalRolls = Number(perf?.total_rolls || 0);
        const totalSubs = Number(perf?.total_submissions_for || perf?.submissions_for || 0);
        const uniquePartners = Number(partners?.partner_diversity?.unique_partners || partners?.partner_matrix?.length || 0);
        const uniqueTechniques = Number(techs?.unique_techniques || techs?.technique_count || 0);
        const currentStreak = Number(consist?.current_streak?.weeks || consist?.training_streak || 0);

        // Map progress to badge definitions
        const progressMap: Record<string, number> = {
          sessions: totalSessions,
          streak: currentStreak,
          rolls: totalRolls,
          subs: totalSubs,
          partners: uniquePartners,
          techniques: uniqueTechniques,
        };

        const computed: Badge[] = BADGE_DEFINITIONS.map(def => {
          const progress = progressMap[def.icon] || 0;
          const earned = def.target ? progress >= def.target : false;
          return {
            ...def,
            progress,
            earned,
            earned_date: earned ? new Date().toISOString() : undefined,
          };
        });

        setBadges(computed);
      } catch (err) {
        logger.error('Failed to load achievements', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={2} />
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 9 }).map((_, i) => <CardSkeleton key={i} lines={2} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3" style={{ color: 'var(--text)' }}>
          <Award className="w-7 h-7" style={{ color: 'var(--accent)' }} />
          Achievements
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Track your BJJ milestones and earn badges
        </p>
      </div>

      <BadgeDisplay badges={badges} />
    </div>
  );
}
