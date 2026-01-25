import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { sessionsApi, suggestionsApi } from '../api/client';
import type { Session, Suggestion } from '../types';
import { TrendingUp, Calendar, Users, Target } from 'lucide-react';

export default function Dashboard() {
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [sessionsRes, suggestionRes] = await Promise.all([
        sessionsApi.list(5),
        suggestionsApi.getToday(),
      ]);
      setRecentSessions(sessionsRes.data);
      setSuggestion(suggestionRes.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  // Calculate stats
  const totalSessions = recentSessions.length;
  const totalRolls = recentSessions.reduce((sum, s) => sum + s.rolls, 0);
  const avgIntensity = totalSessions > 0
    ? (recentSessions.reduce((sum, s) => sum + s.intensity, 0) / totalSessions).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Recent Sessions</p>
              <p className="text-2xl font-bold mt-1">{totalSessions}</p>
            </div>
            <Calendar className="w-8 h-8 text-primary-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Rolls</p>
              <p className="text-2xl font-bold mt-1">{totalRolls}</p>
            </div>
            <Users className="w-8 h-8 text-primary-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Avg Intensity</p>
              <p className="text-2xl font-bold mt-1">{avgIntensity}/5</p>
            </div>
            <TrendingUp className="w-8 h-8 text-primary-600" />
          </div>
        </div>
      </div>

      {/* Today's Suggestion */}
      {suggestion && (
        <div className="card bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-800">
          <div className="flex items-start gap-3">
            <Target className="w-6 h-6 text-primary-600 mt-1" />
            <div className="flex-1">
              <h3 className="font-semibold text-lg mb-2">Today's Recommendation</h3>
              <p className="text-gray-700 dark:text-gray-300 mb-3">{suggestion.suggestion}</p>
              {suggestion.readiness && (
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Readiness: {suggestion.readiness.composite_score}/20 •
                  Sleep: {suggestion.readiness.sleep}/5 •
                  Energy: {suggestion.readiness.energy}/5
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Sessions</h2>
          <Link to="/log" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
            Log New Session →
          </Link>
        </div>

        {recentSessions.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No sessions logged yet. <Link to="/log" className="text-primary-600 hover:underline">Log your first session!</Link>
          </p>
        ) : (
          <div className="space-y-3">
            {recentSessions.map((session) => (
              <div
                key={session.id}
                className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {session.gym_name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(session.session_date).toLocaleDateString()} • {session.class_type}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded">
                    {session.duration_mins} mins
                  </span>
                </div>
                <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>Rolls: {session.rolls}</span>
                  <span>Intensity: {session.intensity}/5</span>
                  {session.submissions_for > 0 && (
                    <span>Subs: {session.submissions_for}-{session.submissions_against}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
