import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminApi } from '../api/client';
import { Users, Building2, MessageSquare, Activity, TrendingUp, Shield } from 'lucide-react';
import { Card } from '../components/ui';

interface DashboardStats {
  total_users: number;
  active_users: number;
  new_users_week: number;
  total_sessions: number;
  total_gyms: number;
  verified_gyms: number;
  pending_gyms: number;
  total_comments: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await adminApi.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!stats) {
    return <div className="text-center py-12">Failed to load dashboard</div>;
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      subtitle: `${stats.new_users_week} new this week`,
      icon: Users,
      color: 'var(--primary)',
      link: '/admin/users',
    },
    {
      title: 'Active Users',
      value: stats.active_users,
      subtitle: 'Last 30 days',
      icon: TrendingUp,
      color: 'var(--success)',
    },
    {
      title: 'Total Sessions',
      value: stats.total_sessions,
      subtitle: 'All time',
      icon: Activity,
      color: 'var(--primary)',
    },
    {
      title: 'Gyms',
      value: stats.total_gyms,
      subtitle: `${stats.pending_gyms} pending verification`,
      icon: Building2,
      color: 'var(--warning)',
      link: '/admin/gyms',
    },
    {
      title: 'Comments',
      value: stats.total_comments,
      subtitle: 'Platform-wide',
      icon: MessageSquare,
      color: 'var(--muted)',
      link: '/admin/content',
    },
    {
      title: 'Verified Gyms',
      value: stats.verified_gyms,
      subtitle: `${((stats.verified_gyms / stats.total_gyms) * 100).toFixed(0)}% verified`,
      icon: Shield,
      color: 'var(--success)',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
          Admin Dashboard
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Platform overview and management
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat) => {
          const CardContent = (
            <Card className="h-full">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium" style={{ color: 'var(--muted)' }}>
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold mt-2" style={{ color: 'var(--text)' }}>
                    {stat.value.toLocaleString()}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                    {stat.subtitle}
                  </p>
                </div>
                <div
                  className="p-3 rounded-lg"
                  style={{ backgroundColor: `${stat.color}20` }}
                >
                  <stat.icon className="w-6 h-6" style={{ color: stat.color }} />
                </div>
              </div>
            </Card>
          );

          return stat.link ? (
            <Link key={stat.title} to={stat.link} className="block hover:opacity-80 transition-opacity">
              {CardContent}
            </Link>
          ) : (
            <div key={stat.title}>{CardContent}</div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <Card>
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text)' }}>
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Link
            to="/admin/users"
            className="p-4 rounded-lg border transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            style={{ borderColor: 'var(--border)' }}
          >
            <Users className="w-5 h-5 mb-2" style={{ color: 'var(--primary)' }} />
            <p className="font-medium" style={{ color: 'var(--text)' }}>Manage Users</p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>View and edit user accounts</p>
          </Link>

          <Link
            to="/admin/gyms"
            className="p-4 rounded-lg border transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            style={{ borderColor: 'var(--border)' }}
          >
            <Building2 className="w-5 h-5 mb-2" style={{ color: 'var(--primary)' }} />
            <p className="font-medium" style={{ color: 'var(--text)' }}>Manage Gyms</p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {stats.pending_gyms} pending verification
            </p>
          </Link>

          <Link
            to="/admin/content"
            className="p-4 rounded-lg border transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            style={{ borderColor: 'var(--border)' }}
          >
            <MessageSquare className="w-5 h-5 mb-2" style={{ color: 'var(--primary)' }} />
            <p className="font-medium" style={{ color: 'var(--text)' }}>Content Moderation</p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Review comments and reports</p>
          </Link>

          <Link
            to="/admin/techniques"
            className="p-4 rounded-lg border transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            style={{ borderColor: 'var(--border)' }}
          >
            <Activity className="w-5 h-5 mb-2" style={{ color: 'var(--primary)' }} />
            <p className="font-medium" style={{ color: 'var(--text)' }}>Manage Techniques</p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Edit glossary and movements</p>
          </Link>
        </div>
      </Card>

      {/* Engagement Rate */}
      <Card>
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text)' }}>
          Platform Health
        </h2>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm" style={{ color: 'var(--text)' }}>User Engagement</span>
              <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                {((stats.active_users / stats.total_users) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div
                className="h-2 rounded-full transition-all"
                style={{
                  width: `${(stats.active_users / stats.total_users) * 100}%`,
                  backgroundColor: 'var(--success)',
                }}
              />
            </div>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {stats.active_users} of {stats.total_users} users logged sessions in the last 30 days
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm" style={{ color: 'var(--text)' }}>Gym Verification Rate</span>
              <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                {((stats.verified_gyms / stats.total_gyms) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <div
                className="h-2 rounded-full transition-all"
                style={{
                  width: `${(stats.verified_gyms / stats.total_gyms) * 100}%`,
                  backgroundColor: 'var(--primary)',
                }}
              />
            </div>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {stats.verified_gyms} verified, {stats.pending_gyms} pending review
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
