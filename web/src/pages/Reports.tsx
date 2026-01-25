import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/client';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  TrendingUp, Award, Users, Target, Activity, Heart, Flame, Trophy,
  Calendar, BarChart3, Zap
} from 'lucide-react';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [loading, setLoading] = useState(false);

  // Data states for each dashboard
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [partnerData, setPartnerData] = useState<any>(null);
  const [readinessData, setReadinessData] = useState<any>(null);
  const [whoopData, setWhoopData] = useState<any>(null);
  const [techniqueData, setTechniqueData] = useState<any>(null);
  const [consistencyData, setConsistencyData] = useState<any>(null);
  const [milestonesData, setMilestonesData] = useState<any>(null);
  const [instructorData, setInstructorData] = useState<any>(null);

  useEffect(() => {
    // Set default date range (last 90 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 90);
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    });
  }, []);

  useEffect(() => {
    if (dateRange.start && dateRange.end) {
      loadData();
    }
  }, [dateRange, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = { start_date: dateRange.start, end_date: dateRange.end };

      // Load data based on active tab
      switch (activeTab) {
        case 'overview':
          const perfRes = await analyticsApi.performanceOverview(params);
          setPerformanceData(perfRes.data);
          break;
        case 'partners':
          const partRes = await analyticsApi.partnerStats(params);
          setPartnerData(partRes.data);
          break;
        case 'readiness':
          const readRes = await analyticsApi.readinessTrends(params);
          setReadinessData(readRes.data);
          break;
        case 'whoop':
          const whoopRes = await analyticsApi.whoopAnalytics(params);
          setWhoopData(whoopRes.data);
          break;
        case 'techniques':
          const techRes = await analyticsApi.techniqueBreakdown(params);
          setTechniqueData(techRes.data);
          break;
        case 'consistency':
          const consRes = await analyticsApi.consistencyMetrics(params);
          setConsistencyData(consRes.data);
          break;
        case 'milestones':
          const mileRes = await analyticsApi.milestones();
          setMilestonesData(mileRes.data);
          break;
        case 'instructors':
          const instRes = await analyticsApi.instructorInsights(params);
          setInstructorData(instRes.data);
          break;
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Performance', icon: TrendingUp },
    { id: 'partners', name: 'Partners', icon: Users },
    { id: 'readiness', name: 'Readiness', icon: Activity },
    { id: 'whoop', name: 'Whoop', icon: Heart },
    { id: 'techniques', name: 'Techniques', icon: Target },
    { id: 'consistency', name: 'Consistency', icon: Calendar },
    { id: 'milestones', name: 'Milestones', icon: Trophy },
    { id: 'instructors', name: 'Instructors', icon: Award },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>

        {/* Date Range Picker */}
        <div className="flex gap-2 items-center">
          <input
            type="date"
            className="input text-sm"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
          />
          <span className="text-gray-500">to</span>
          <input
            type="date"
            className="input text-sm"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
          />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-1 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Dashboard Content */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* PERFORMANCE OVERVIEW */}
          {activeTab === 'overview' && performanceData && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total Sessions</p>
                      <p className="text-2xl font-bold mt-1">{performanceData.summary.total_sessions}</p>
                    </div>
                    <Calendar className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Subs Given</p>
                      <p className="text-2xl font-bold mt-1 text-green-600">{performanceData.summary.total_submissions_for}</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-green-600" />
                  </div>
                </div>
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Subs Against</p>
                      <p className="text-2xl font-bold mt-1 text-red-600">{performanceData.summary.total_submissions_against}</p>
                    </div>
                    <Target className="w-8 h-8 text-red-600" />
                  </div>
                </div>
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Avg Intensity</p>
                      <p className="text-2xl font-bold mt-1">{performanceData.summary.avg_intensity}/5</p>
                    </div>
                    <Flame className="w-8 h-8 text-orange-600" />
                  </div>
                </div>
              </div>

              {/* Submission Success Over Time */}
              {performanceData.submission_success_over_time.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Submission Success Over Time</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={performanceData.submission_success_over_time}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="for" stroke="#10B981" name="Subs For" strokeWidth={2} />
                      <Line type="monotone" dataKey="against" stroke="#EF4444" name="Subs Against" strokeWidth={2} />
                      <Line type="monotone" dataKey="ratio" stroke="#3B82F6" name="Ratio" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Top Submissions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {performanceData.top_submissions_for.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Top Submissions Given</h3>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={performanceData.top_submissions_for} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={100} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#10B981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
                {performanceData.top_submissions_against.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Top Submissions Received</h3>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={performanceData.top_submissions_against} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={100} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#EF4444" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Belt Progression */}
              {performanceData.performance_by_belt.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Performance by Belt Rank</h3>
                  <div className="space-y-3">
                    {performanceData.performance_by_belt.map((belt: any, idx: number) => (
                      <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold">{belt.belt}</span>
                          <span className="text-sm text-gray-500">{belt.sessions} sessions</span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Subs: {belt.subs_for} for / {belt.subs_against} against
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {performanceData.submission_success_over_time.length === 0 &&
               performanceData.top_submissions_for.length === 0 && (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No detailed roll data available yet. Start logging rolls with the detailed mode to see analytics!</p>
                </div>
              )}
            </div>
          )}

          {/* PARTNER ANALYTICS */}
          {activeTab === 'partners' && partnerData && (
            <div className="space-y-6">
              {/* Diversity Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Unique Partners</p>
                  <p className="text-3xl font-bold mt-1">{partnerData.diversity_metrics.unique_partners}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-600 dark:text-gray-400">New Partners</p>
                  <p className="text-3xl font-bold mt-1 text-green-600">{partnerData.diversity_metrics.new_partners}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Recurring Partners</p>
                  <p className="text-3xl font-bold mt-1 text-blue-600">{partnerData.diversity_metrics.recurring_partners}</p>
                </div>
              </div>

              {/* Partner Matrix */}
              {partnerData.partner_matrix.length > 0 ? (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Partner Performance Matrix</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-left border-b border-gray-200 dark:border-gray-700">
                          <th className="pb-2 px-2">Partner</th>
                          <th className="pb-2 px-2">Belt</th>
                          <th className="pb-2 px-2">Rolls</th>
                          <th className="pb-2 px-2">Subs For</th>
                          <th className="pb-2 px-2">Subs Against</th>
                          <th className="pb-2 px-2">Ratio</th>
                        </tr>
                      </thead>
                      <tbody>
                        {partnerData.partner_matrix.slice(0, 10).map((partner: any) => (
                          <tr key={partner.id} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="py-2 px-2 font-medium">{partner.name}</td>
                            <td className="py-2 px-2">
                              {partner.belt_rank || '-'}
                              {partner.belt_stripes > 0 && ` (${partner.belt_stripes})`}
                            </td>
                            <td className="py-2 px-2">{partner.total_rolls}</td>
                            <td className="py-2 px-2 text-green-600">{partner.submissions_for}</td>
                            <td className="py-2 px-2 text-red-600">{partner.submissions_against}</td>
                            <td className="py-2 px-2 font-semibold">
                              {partner.sub_ratio === Infinity ? '∞' : partner.sub_ratio.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No partner data available. Add training partners in Contacts and log detailed rolls!</p>
                </div>
              )}
            </div>
          )}

          {/* READINESS & RECOVERY */}
          {activeTab === 'readiness' && readinessData && (
            <div className="space-y-6">
              {/* Readiness Over Time */}
              {readinessData.readiness_over_time.length > 0 ? (
                <>
                  <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Readiness Trend</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={readinessData.readiness_over_time}>
                        <defs>
                          <linearGradient id="colorReadiness" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis domain={[0, 20]} />
                        <Tooltip />
                        <Legend />
                        <Area type="monotone" dataKey="composite_score" stroke="#3B82F6" fillOpacity={1} fill="url(#colorReadiness)" name="Readiness Score" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Training Load vs Readiness */}
                  {readinessData.training_load_vs_readiness.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Training Load vs Readiness</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="readiness" name="Readiness" />
                          <YAxis dataKey="intensity" name="Intensity" />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Legend />
                          <Scatter name="Sessions" data={readinessData.training_load_vs_readiness} fill="#8B5CF6" />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Recovery Patterns */}
                  {readinessData.recovery_patterns.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Readiness by Day of Week</h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={readinessData.recovery_patterns}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="day" />
                          <YAxis domain={[0, 20]} />
                          <Tooltip />
                          <Bar dataKey="avg_readiness" fill="#10B981" name="Avg Readiness" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Injury Timeline */}
                  {readinessData.injury_timeline.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Injury & Hotspot Timeline</h3>
                      <div className="space-y-2">
                        {readinessData.injury_timeline.map((injury: any, idx: number) => (
                          <div key={idx} className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                            <div className="flex justify-between items-center">
                              <span className="font-medium text-red-800 dark:text-red-300">{injury.hotspot}</span>
                              <span className="text-sm text-gray-500">{injury.date}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No readiness data available. Start logging readiness check-ins to track recovery!</p>
                </div>
              )}
            </div>
          )}

          {/* WHOOP ANALYTICS */}
          {activeTab === 'whoop' && whoopData && (
            <div className="space-y-6">
              {whoopData.summary.total_whoop_sessions > 0 ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="card">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Sessions with Whoop</p>
                      <p className="text-3xl font-bold mt-1">{whoopData.summary.total_whoop_sessions}</p>
                    </div>
                    <div className="card">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Avg Strain</p>
                      <p className="text-3xl font-bold mt-1 text-orange-600">{whoopData.summary.avg_strain}</p>
                    </div>
                    <div className="card">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total Calories</p>
                      <p className="text-3xl font-bold mt-1 text-red-600">{whoopData.summary.total_calories.toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Strain vs Performance */}
                  {whoopData.strain_vs_performance.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Strain vs Submission Ratio</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={whoopData.strain_vs_performance}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis yAxisId="left" />
                          <YAxis yAxisId="right" orientation="right" />
                          <Tooltip />
                          <Legend />
                          <Line yAxisId="left" type="monotone" dataKey="strain" stroke="#F59E0B" name="Strain" strokeWidth={2} />
                          <Line yAxisId="right" type="monotone" dataKey="sub_ratio" stroke="#10B981" name="Sub Ratio" strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Heart Rate Zones */}
                  {whoopData.heart_rate_zones.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Heart Rate by Class Type</h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={whoopData.heart_rate_zones}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="class_type" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="avg_hr" fill="#EF4444" name="Avg HR" />
                          <Bar dataKey="max_hr" fill="#DC2626" name="Max HR" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Calorie Burn */}
                  {whoopData.calorie_burn.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Calorie Burn by Class Type</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {whoopData.calorie_burn.map((item: any) => (
                          <div key={item.class_type} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-semibold capitalize">{item.class_type}</span>
                              <span className="text-sm text-gray-500">{item.sessions} sessions</span>
                            </div>
                            <div className="text-2xl font-bold text-red-600 mb-1">
                              {item.total_calories.toLocaleString()} cal
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {item.calories_per_min.toFixed(1)} cal/min
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recovery Correlation */}
                  {whoopData.recovery_correlation.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Strain vs Next-Day Readiness</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="strain" name="Strain" />
                          <YAxis dataKey="next_day_readiness" name="Next Day Readiness" />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Legend />
                          <Scatter name="Sessions" data={whoopData.recovery_correlation} fill="#F59E0B" />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </>
              ) : (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No Whoop data available. Start adding Whoop stats when logging sessions!</p>
                </div>
              )}
            </div>
          )}

          {/* TECHNIQUE MASTERY */}
          {activeTab === 'techniques' && techniqueData && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Unique Techniques Used</p>
                  <p className="text-3xl font-bold mt-1">{techniqueData.summary.total_unique_techniques_used}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Stale Techniques (30+ days)</p>
                  <p className="text-3xl font-bold mt-1 text-orange-600">{techniqueData.summary.stale_count}</p>
                </div>
              </div>

              {techniqueData.category_breakdown.length > 0 ||
               techniqueData.gi_top_techniques.length > 0 ||
               techniqueData.nogi_top_techniques.length > 0 ? (
                <>
                  {/* Category Breakdown */}
                  {techniqueData.category_breakdown.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Technique Category Distribution</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={techniqueData.category_breakdown}
                            dataKey="count"
                            nameKey="category"
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            label
                          >
                            {techniqueData.category_breakdown.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Gi vs No-Gi Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {techniqueData.gi_top_techniques.length > 0 && (
                      <div className="card">
                        <h3 className="text-lg font-semibold mb-4">Top Gi Techniques</h3>
                        <div className="space-y-2">
                          {techniqueData.gi_top_techniques.slice(0, 10).map((tech: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                              <span>{tech.name}</span>
                              <span className="font-semibold text-blue-600">{tech.count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {techniqueData.nogi_top_techniques.length > 0 && (
                      <div className="card">
                        <h3 className="text-lg font-semibold mb-4">Top No-Gi Techniques</h3>
                        <div className="space-y-2">
                          {techniqueData.nogi_top_techniques.slice(0, 10).map((tech: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                              <span>{tech.name}</span>
                              <span className="font-semibold text-purple-600">{tech.count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Stale Techniques */}
                  {techniqueData.stale_techniques.length > 0 && (
                    <div className="card">
                      <h3 className="text-lg font-semibold mb-4">Techniques to Revisit (30+ days)</h3>
                      <div className="flex flex-wrap gap-2">
                        {techniqueData.stale_techniques.slice(0, 30).map((tech: any) => (
                          <span key={tech.id} className="px-3 py-1 bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 rounded-full text-sm">
                            {tech.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No technique data available. Log sessions with detailed rolls and select submissions from the glossary!</p>
                </div>
              )}
            </div>
          )}

          {/* TRAINING CONSISTENCY */}
          {activeTab === 'consistency' && consistencyData && (
            <div className="space-y-6">
              {/* Streaks */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Current Streak</p>
                      <p className="text-4xl font-bold mt-1 text-green-600">{consistencyData.streaks.current}</p>
                      <p className="text-sm text-gray-500 mt-1">days</p>
                    </div>
                    <Flame className="w-12 h-12 text-green-600" />
                  </div>
                </div>
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Longest Streak</p>
                      <p className="text-4xl font-bold mt-1 text-blue-600">{consistencyData.streaks.longest}</p>
                      <p className="text-sm text-gray-500 mt-1">days</p>
                    </div>
                    <Trophy className="w-12 h-12 text-blue-600" />
                  </div>
                </div>
              </div>

              {/* Weekly Volume */}
              {consistencyData.weekly_volume.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Weekly Training Volume</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={consistencyData.weekly_volume}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="sessions" fill="#3B82F6" name="Sessions" />
                      <Bar dataKey="hours" fill="#10B981" name="Hours" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Class Type Distribution */}
              {consistencyData.class_type_distribution.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Class Type Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={consistencyData.class_type_distribution}
                        dataKey="count"
                        nameKey="class_type"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label
                      >
                        {consistencyData.class_type_distribution.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Gym Breakdown */}
              {consistencyData.gym_breakdown.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Training by Gym</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={consistencyData.gym_breakdown} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="gym" type="category" width={150} />
                      <Tooltip />
                      <Bar dataKey="sessions" fill="#8B5CF6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* MILESTONES */}
          {activeTab === 'milestones' && milestonesData && (
            <div className="space-y-6">
              {/* Rolling Totals */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card">
                  <h4 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Lifetime</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Sessions:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.lifetime.sessions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Hours:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.lifetime.hours}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Rolls:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.lifetime.rolls}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Submissions:</span>
                      <span className="font-bold text-green-600">{milestonesData.rolling_totals.lifetime.submissions}</span>
                    </div>
                  </div>
                </div>
                <div className="card">
                  <h4 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Current Belt</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Sessions:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.current_belt.sessions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Hours:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.current_belt.hours}</span>
                    </div>
                  </div>
                </div>
                <div className="card">
                  <h4 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">This Year</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Sessions:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.this_year.sessions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Hours:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.this_year.hours.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Rolls:</span>
                      <span className="font-bold">{milestonesData.rolling_totals.this_year.rolls}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Personal Records */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Personal Records</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg">
                    <Trophy className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-yellow-600">{milestonesData.personal_records.most_rolls_session}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Most Rolls</div>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
                    <BarChart3 className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-blue-600">{milestonesData.personal_records.longest_session} min</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Longest Session</div>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
                    <Zap className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-green-600">{milestonesData.personal_records.best_sub_ratio_day.toFixed(1)}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Best Sub Ratio</div>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
                    <Users className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-purple-600">{milestonesData.personal_records.most_partners_session}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Most Partners</div>
                  </div>
                </div>
              </div>

              {/* Belt Progression */}
              {milestonesData.belt_progression.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Belt Progression Timeline</h3>
                  <div className="space-y-3">
                    {milestonesData.belt_progression.map((belt: any, idx: number) => (
                      <div key={idx} className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <div>
                            <span className="font-bold text-lg">{belt.belt}</span>
                            {belt.professor && <span className="text-sm text-gray-500 ml-2">with {belt.professor}</span>}
                          </div>
                          <span className="text-sm text-gray-500">{new Date(belt.date).toLocaleDateString()}</span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {belt.sessions_at_belt} sessions • {belt.hours_at_belt.toFixed(1)} hours
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* INSTRUCTOR INSIGHTS */}
          {activeTab === 'instructors' && instructorData && (
            <div className="space-y-6">
              {instructorData.performance_by_instructor.length > 0 ? (
                <div className="grid grid-cols-1 gap-4">
                  {instructorData.performance_by_instructor.map((instructor: any) => (
                    <div key={instructor.instructor_id} className="card">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-bold">{instructor.instructor_name}</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {instructor.belt_rank && `${instructor.belt_rank} belt`}
                            {instructor.certification && ` • ${instructor.certification}`}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600">{instructor.total_sessions}</div>
                          <div className="text-sm text-gray-500">sessions</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Avg Intensity</p>
                          <p className="text-xl font-bold">{instructor.avg_intensity}/5</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Subs For</p>
                          <p className="text-xl font-bold text-green-600">{instructor.submissions_for}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Subs Against</p>
                          <p className="text-xl font-bold text-red-600">{instructor.submissions_against}</p>
                        </div>
                      </div>
                      {instructor.top_techniques.length > 0 && (
                        <div>
                          <p className="text-sm font-semibold mb-2">Top Techniques Taught:</p>
                          <div className="flex flex-wrap gap-2">
                            {instructor.top_techniques.map((tech: any, idx: number) => (
                              <span key={idx} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm">
                                {tech.name} ({tech.count})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="card text-center py-12">
                  <p className="text-gray-500">No instructor data available. Select instructors when logging sessions to see insights!</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
