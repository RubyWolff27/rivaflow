import { useState, useEffect } from 'react';
import { Sparkles, TrendingUp, DollarSign, Cpu, Users, MessageSquare, ThumbsUp, ThumbsDown, Activity } from 'lucide-react';
import { Card } from '../components/ui';
import AdminNav from '../components/AdminNav';
import { useToast } from '../contexts/ToastContext';
import axios from 'axios';

interface GlobalStats {
  total_users: number;
  active_users_7d: number;
  total_sessions: number;
  total_messages: number;
  total_tokens: number;
  total_cost_usd: number;
  by_provider: {
    [key: string]: {
      total_tokens: number;
      total_cost_usd: number;
      request_count: number;
    };
  };
  by_tier: {
    [key: string]: {
      users: number;
      messages: number;
      tokens: number;
      cost_usd: number;
    };
  };
}

interface CostProjection {
  current_month: {
    cost_so_far: number;
    projected_total: number;
    days_elapsed: number;
    days_remaining: number;
  };
  daily_average: {
    last_7_days: number;
    daily_costs: Array<{ date: string; cost_usd: number }>;
  };
}

interface ProviderStat {
  provider: string;
  model: string;
  request_count: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_tokens_per_request: number;
}

interface TopUser {
  user_id: number;
  email: string;
  subscription_tier: string;
  total_sessions: number;
  total_messages: number;
  total_tokens: number;
  total_cost_usd: number;
  last_activity: string;
}

interface Feedback {
  id: string;
  user_email: string;
  rating: string;
  category: string | null;
  comment: string | null;
  created_at: string;
}

export default function AdminGrapple() {
  const toast = useToast();
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [costProjection, setCostProjection] = useState<CostProjection | null>(null);
  const [providerStats, setProviderStats] = useState<ProviderStat[]>([]);
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllStats();
  }, []);

  const getApiBase = () => import.meta.env.VITE_API_URL || '/api/v1';

  const loadAllStats = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [global, projection, providers, users, feedbackData] = await Promise.all([
        axios.get(`${getApiBase()}/admin/grapple/stats/global?days=30`, { headers }),
        axios.get(`${getApiBase()}/admin/grapple/stats/projections`, { headers }),
        axios.get(`${getApiBase()}/admin/grapple/stats/providers?days=7`, { headers }),
        axios.get(`${getApiBase()}/admin/grapple/stats/users?limit=10`, { headers }),
        axios.get(`${getApiBase()}/admin/grapple/feedback?limit=20`, { headers }),
      ]);

      setGlobalStats(global.data);
      setCostProjection(projection.data);
      setProviderStats(providers.data.providers);
      setTopUsers(users.data.users);
      setFeedback(feedbackData.data.feedback);
    } catch (error: any) {
      console.error('Failed to load stats:', error);
      toast.error('Failed to load Grapple statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading Grapple Analytics...</div>;
  }

  if (!globalStats || !costProjection) {
    return <div className="text-center py-12">Failed to load analytics</div>;
  }

  const totalCostThisMonth = costProjection.current_month.cost_so_far;
  const projectedCost = costProjection.current_month.projected_total;
  const avgDailyCost = costProjection.daily_average.last_7_days;

  const mainStats = [
    {
      title: 'Total Users',
      value: globalStats.total_users,
      subtitle: `${globalStats.active_users_7d} active (7d)`,
      icon: Users,
      color: '#4F46E5',
    },
    {
      title: 'Total Messages',
      value: globalStats.total_messages.toLocaleString(),
      subtitle: `${globalStats.total_sessions} sessions`,
      icon: MessageSquare,
      color: '#10B981',
    },
    {
      title: 'Total Tokens',
      value: (globalStats.total_tokens / 1000000).toFixed(2) + 'M',
      subtitle: 'All time',
      icon: Activity,
      color: '#F59E0B',
    },
    {
      title: 'Total Cost',
      value: '$' + globalStats.total_cost_usd.toFixed(2),
      subtitle: 'All time',
      icon: DollarSign,
      color: '#EF4444',
    },
  ];

  const costStats = [
    {
      title: 'Cost This Month',
      value: '$' + totalCostThisMonth.toFixed(2),
      subtitle: `${costProjection.current_month.days_elapsed} days elapsed`,
      icon: DollarSign,
      color: '#EF4444',
    },
    {
      title: 'Projected Month Cost',
      value: '$' + projectedCost.toFixed(2),
      subtitle: `${costProjection.current_month.days_remaining} days remaining`,
      icon: TrendingUp,
      color: '#F59E0B',
    },
    {
      title: 'Daily Average',
      value: '$' + avgDailyCost.toFixed(4),
      subtitle: 'Last 7 days',
      icon: Activity,
      color: '#10B981',
    },
  ];

  const positiveFeedback = feedback.filter((f) => f.rating === 'positive').length;
  const negativeFeedback = feedback.filter((f) => f.rating === 'negative').length;
  const satisfactionRate = feedback.length > 0 ? (positiveFeedback / feedback.length) * 100 : 0;

  return (
    <div className="space-y-6">
      <AdminNav />

      <div className="flex items-center gap-3">
        <Sparkles className="w-8 h-8 text-primary-600" />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Grapple Analytics</h1>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {mainStats.map((stat) => (
          <Card key={stat.title} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stat.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{stat.subtitle}</p>
              </div>
              <stat.icon className="w-10 h-10" style={{ color: stat.color }} />
            </div>
          </Card>
        ))}
      </div>

      {/* Cost Projections */}
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Cost Projections</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {costStats.map((stat) => (
            <div key={stat.title} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <stat.icon className="w-8 h-8" style={{ color: stat.color }} />
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.title}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{stat.subtitle}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Daily Cost Chart */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Daily Costs (Last 7 Days)</p>
          {costProjection.daily_average.daily_costs.map((day) => (
            <div key={day.date} className="flex items-center gap-3">
              <span className="text-xs text-gray-500 dark:text-gray-400 w-24">{day.date}</span>
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-6 overflow-hidden">
                <div
                  className="bg-primary-600 h-full flex items-center justify-end px-2"
                  style={{
                    width: `${(day.cost_usd / Math.max(...costProjection.daily_average.daily_costs.map((d) => d.cost_usd))) * 100}%`,
                  }}
                >
                  <span className="text-xs text-white font-medium">${day.cost_usd.toFixed(4)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Provider Stats */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">LLM Provider Performance</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Provider</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Model</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Requests</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tokens</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Avg Tokens</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {providerStats.map((stat, idx) => (
                <tr key={idx}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white capitalize">{stat.provider}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{stat.model}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-white">{stat.request_count.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-white">{(stat.total_tokens / 1000).toFixed(1)}k</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">{stat.avg_tokens_per_request.toFixed(0)}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">${stat.total_cost_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Tier Breakdown */}
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Usage by Subscription Tier</h2>
        <div className="space-y-4">
          {Object.entries(globalStats.by_tier).map(([tier, stats]) => (
            <div key={tier} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-900 dark:text-white uppercase">{tier}</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">{stats.users} users</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Messages</p>
                  <p className="font-medium text-gray-900 dark:text-white">{stats.messages.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Tokens</p>
                  <p className="font-medium text-gray-900 dark:text-white">{(stats.tokens / 1000).toFixed(1)}k</p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Cost</p>
                  <p className="font-medium text-gray-900 dark:text-white">${stats.cost_usd.toFixed(2)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Top Users */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Top Users by Usage</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tier</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Messages</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Sessions</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Cost</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {topUsers.map((user) => (
                <tr key={user.user_id}>
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-1 text-xs font-medium rounded-full bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 uppercase">
                      {user.subscription_tier}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-white">{user.total_messages}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">{user.total_sessions}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">${user.total_cost_usd.toFixed(4)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {user.last_activity ? new Date(user.last_activity).toLocaleDateString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* User Feedback */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">User Feedback</h2>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <ThumbsUp className="w-4 h-4 text-green-600" />
              <span className="text-gray-900 dark:text-white font-medium">{positiveFeedback}</span>
            </div>
            <div className="flex items-center gap-2">
              <ThumbsDown className="w-4 h-4 text-red-600" />
              <span className="text-gray-900 dark:text-white font-medium">{negativeFeedback}</span>
            </div>
            <div className="text-gray-500 dark:text-gray-400">
              {satisfactionRate.toFixed(0)}% positive
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {feedback.slice(0, 10).map((item) => (
            <div key={item.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  {item.rating === 'positive' ? (
                    <ThumbsUp className="w-4 h-4 text-green-600" />
                  ) : (
                    <ThumbsDown className="w-4 h-4 text-red-600" />
                  )}
                  <span className="text-sm text-gray-600 dark:text-gray-400">{item.user_email}</span>
                  {item.category && (
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">{item.category}</span>
                  )}
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>
              {item.comment && (
                <p className="text-sm text-gray-700 dark:text-gray-300">{item.comment}</p>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
