import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../ui';
import { Trophy, Target } from 'lucide-react';

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
  total_sessions?: number;
  total_hours?: number;
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
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load from dashboard API
      const dashboardResponse = await fetch('/api/v1/dashboard/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const dashboardData = await dashboardResponse.json();

      // Load profile
      const profileResponse = await fetch('/api/v1/profile', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const profileData = await profileResponse.json();

      setProfile(profileData);
      if (dashboardData.milestones?.closest) {
        setClosestMilestone(dashboardData.milestones.closest);
      }
    } catch (error) {
      console.error('Failed to load journey progress:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full"></div>
            <div className="h-4 bg-gray-700 rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  const beltColor = BELT_COLORS[profile?.belt_rank || 'white'] || '#9CA3AF';
  const beltRank = profile?.belt_rank ? profile.belt_rank.charAt(0).toUpperCase() + profile.belt_rank.slice(1) : 'White';
  const stripes = profile?.belt_stripes || 0;

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

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div>
          <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            {profile?.total_sessions || 0}
          </p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>Total Sessions</p>
        </div>
        <div>
          <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            {profile?.total_hours?.toFixed(0) || 0}
          </p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>Total Hours</p>
        </div>
      </div>
    </Card>
  );
}
