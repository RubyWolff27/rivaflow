import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { sessionsApi } from '../api/client';
import type { Session } from '../types';
import { Calendar, MapPin, Clock, Activity, Target, Filter, Search } from 'lucide-react';

export default function Sessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'duration' | 'intensity'>('date');

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    filterAndSortSessions();
  }, [sessions, searchTerm, filterType, sortBy]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const response = await sessionsApi.list(1000); // Get all sessions
      setSessions(response.data ?? []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortSessions = () => {
    let filtered = [...sessions];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(s =>
        s.gym_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.notes?.toLowerCase().includes(searchTerm.toLowerCase())
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

    setFilteredSessions(filtered);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const uniqueClassTypes = Array.from(new Set(sessions.map(s => s.class_type)));

  const stats = {
    total: sessions.length,
    totalHours: sessions.reduce((sum, s) => sum + (s.duration_mins ?? 0), 0) / 60,
    totalRolls: sessions.reduce((sum, s) => sum + (s.rolls ?? 0), 0),
    avgIntensity: sessions.length > 0
      ? sessions.reduce((sum, s) => sum + (s.intensity ?? 0), 0) / sessions.length
      : 0,
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">Loading sessions...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" id="page-title">All Sessions</h1>
        <p className="text-gray-600 dark:text-gray-400">View and manage your training history</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Sessions</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Hours</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalHours.toFixed(1)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Rolls</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalRolls}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Intensity</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.avgIntensity.toFixed(1)}/5</p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by gym, location, notes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 w-full"
            />
          </div>

          {/* Filter by Type */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input pl-10 w-full"
            >
              <option value="all">All Types</option>
              {uniqueClassTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'date' | 'duration' | 'intensity')}
            className="input w-full"
          >
            <option value="date">Sort by Date</option>
            <option value="duration">Sort by Duration</option>
            <option value="intensity">Sort by Intensity</option>
          </select>
        </div>
      </div>

      {/* Sessions List */}
      {filteredSessions.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">
            {searchTerm || filterType !== 'all'
              ? 'No sessions match your filters'
              : 'No sessions logged yet. Start training!'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSessions.map((session) => (
            <Link
              key={session.id}
              to={`/session/${session.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded text-xs font-semibold uppercase">
                      {session.class_type}
                    </span>
                    <span className="text-xs text-gray-500">
                      Intensity: {session.intensity}/5
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {session.gym_name}
                  </h3>
                  {session.location && (
                    <p className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mt-1">
                      <MapPin className="w-3 h-3" />
                      {session.location}
                    </p>
                  )}
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 py-3 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <Calendar className="w-3 h-3" />
                    Date
                  </div>
                  <p className="text-sm font-semibold">{formatDate(session.session_date)}</p>
                  {session.class_time && (
                    <p className="text-xs text-gray-500">{session.class_time}</p>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <Clock className="w-3 h-3" />
                    Duration
                  </div>
                  <p className="text-sm font-semibold">{session.duration_mins} min</p>
                </div>
                <div>
                  <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <Activity className="w-3 h-3" />
                    Rolls
                  </div>
                  <p className="text-sm font-semibold">{session.rolls}</p>
                </div>
              </div>

              {/* Submissions */}
              <div className="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <Target className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-semibold text-green-600">{session.submissions_for}</span>
                  {' / '}
                  <span className="font-semibold text-red-600">{session.submissions_against}</span>
                  {' '}submissions
                </span>
              </div>

              {/* Notes Preview */}
              {session.notes && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 line-clamp-2">
                  {session.notes}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
