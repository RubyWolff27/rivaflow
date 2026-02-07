import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../ui';
import { Trophy, Target } from 'lucide-react';
import { dashboardApi, profileApi } from '../../api/client';

interface Milestone {
  id: number;
  milestone_type: string;
  target_value: number;
  current_value: number;
  progress_percentage: number;
  achieved: boolean;
  achieved_at?: string;
}

interface Profile {
  belt_rank?: string;
  belt_stripes?: number;
  current_grade?: string;
  total_sessions?: number;
  total_hours?: number;
  sessions_since_promotion?: number;
  hours_since_promotion?: number;
  promotion_date?: string;
}

const BELT_COLORS: Record<string, string> = {
  white: '#F3F4F6',
  blue: '#3B82F6',
  purple: '#8B5CF6',
  brown: '#78350F',
  black: '#1F2937',
};

export function JourneyProgress() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [closestMilestone, setClosestMilestone] = useState<Milestone | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [dashboardResponse, profileResponse] = await Promise.all([
          dashboardApi.getSummary(),
          profileApi.get(),
        ]);
        if (!cancelled) {
          setProfile(profileResponse.data);
          if (dashboardResponse.data.milestones?.closest) {
            setClosestMilestone(dashboardResponse.data.milestones.closest);
          }
        }
      } catch (error) {
        if (!cancelled) console.error('Failed to load journey progress:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-[var(--surfaceElev)] rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-full"></div>
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  // Use current_grade or belt_rank (fallback for compatibility)
  const gradeStr = profile?.current_grade || profile?.belt_rank || 'white';
  const beltBase = gradeStr.toLowerCase().split(' ')[0]; // Extract base belt color (e.g., "blue" from "Blue (1 stripe)")
  const beltColor = BELT_COLORS[beltBase] || '#9CA3AF';
  const beltRank = beltBase.charAt(0).toUpperCase() + beltBase.slice(1);

  // Extract stripes from grade string like "Blue (2 stripes)"
  const stripeMatch = gradeStr.match(/\((\d+) stripe/i);
  const stripes = stripeMatch ? parseInt(stripeMatch[1]) : (profile?.belt_stripes || 0);

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
          Journey Progress
        </h3>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Track your belt and milestone progress
        </p>
      </div>

      {/* Belt Progress */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-12 h-8 rounded border-2"
            style={{ backgroundColor: beltColor, borderColor: 'var(--border)' }}
          />
          <div>
            <p className="font-semibold" style={{ color: 'var(--text)' }}>
              {beltRank} Belt
            </p>
            <div className="flex items-center gap-1">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: i < stripes ? beltColor : 'var(--border)',
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        <Link
          to="/profile"
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--accent)' }}
        >
          Update belt rank →
        </Link>
      </div>

      {/* Next Milestone */}
      {closestMilestone ? (
        <div
          className="p-4 rounded-lg"
          style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            <p className="font-medium" style={{ color: 'var(--text)' }}>
              Next Milestone
            </p>
          </div>
          <p className="text-sm mb-2" style={{ color: 'var(--text)' }}>
            {closestMilestone.milestone_type}: {closestMilestone.target_value}
          </p>
          <div className="flex items-center gap-3 mb-2">
            <div className="flex-1 h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
              <div
                className="h-2 rounded-full transition-all"
                style={{
                  width: `${Math.min(100, closestMilestone.progress_percentage || 0)}%`,
                  backgroundColor: 'var(--accent)',
                }}
              />
            </div>
            <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              {closestMilestone.progress_percentage?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {closestMilestone.current_value} / {closestMilestone.target_value}
          </p>
        </div>
      ) : (
        <div
          className="p-4 rounded-lg text-center"
          style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
        >
          <Trophy className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--muted)' }} />
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Keep training to unlock milestones
          </p>
        </div>
      )}

      {/* Quick Stats - Sessions/Hours since last promotion */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div>
          <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            {profile?.sessions_since_promotion || 0}
          </p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Sessions at {beltRank}
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            {profile?.hours_since_promotion?.toFixed(0) || 0}
          </p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Hours at {beltRank}
          </p>
        </div>
      </div>
    </Card>
  );
}
