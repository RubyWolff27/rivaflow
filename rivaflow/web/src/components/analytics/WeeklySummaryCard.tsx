import { useState, useEffect } from 'react';
import { Share2, Flame, Clock, Dumbbell, Users2 } from 'lucide-react';
import { analyticsApi } from '../../api/analytics';
import { logger } from '../../utils/logger';

interface WeeklySummary {
  week_start: string;
  week_end: string;
  total_sessions: number;
  total_rolls: number;
  total_hours: number;
  streak_days: number;
  class_types: Record<string, number>;
}

export default function WeeklySummaryCard() {
  const [data, setData] = useState<WeeklySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await analyticsApi.weeklySummary();
        if (!cancelled) setData(res.data);
      } catch (err) {
        logger.debug('Failed to load weekly summary', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const handleShare = async () => {
    if (!navigator.share) return;
    try {
      await navigator.share({
        title: 'My Training Week',
        text: `This week: ${data?.total_sessions} sessions, ${data?.total_rolls} rolls, ${data?.total_hours.toFixed(1)} hours${data?.streak_days ? `, ${data.streak_days}-day streak` : ''}`,
      });
    } catch {
      logger.debug('Share cancelled or unavailable');
    }
  };

  if (loading) return null;
  if (!data || data.total_sessions === 0) return null;

  const classTypeList = Object.entries(data.class_types)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <div
      className="rounded-[14px] p-4 sm:p-5"
      style={{
        background: 'linear-gradient(135deg, #1E3A5F 0%, #0F172A 100%)',
        border: '1px solid rgba(59,130,246,0.2)',
      }}
    >
      {/* Header row: title + share button */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-blue-300 uppercase tracking-wider">
            This Week
          </h3>
          <p className="text-xs text-blue-400/60 mt-0.5">
            {data.week_start} — {data.week_end}
          </p>
        </div>
        <button
          onClick={handleShare}
          className="p-2 rounded-full transition-colors hover:bg-white/10 shrink-0"
          aria-label="Share weekly summary"
        >
          <Share2 className="w-4 h-4 text-blue-300" />
        </button>
      </div>

      {/* Stats row — all 4 metrics in one row */}
      <div className="grid grid-cols-4 gap-2">
        <div className="text-center">
          <Dumbbell className="w-4 h-4 text-blue-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{data.total_sessions}</div>
          <div className="text-[10px] text-blue-300/70">sessions</div>
        </div>
        <div className="text-center">
          <Users2 className="w-4 h-4 text-blue-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{data.total_rolls}</div>
          <div className="text-[10px] text-blue-300/70">rolls</div>
        </div>
        <div className="text-center">
          <Clock className="w-4 h-4 text-blue-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{data.total_hours.toFixed(1)}</div>
          <div className="text-[10px] text-blue-300/70">hours</div>
        </div>
        <div className="text-center">
          <Flame className="w-4 h-4 text-orange-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{data.streak_days}</div>
          <div className="text-[10px] text-blue-300/70">day streak</div>
        </div>
      </div>

      {/* Class type pills + branding */}
      {classTypeList.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {classTypeList.map(([type, count]) => (
            <span
              key={type}
              className="px-2 py-0.5 rounded-full text-xs font-medium"
              style={{ backgroundColor: 'rgba(59,130,246,0.15)', color: '#93C5FD' }}
            >
              {type} × {count}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-1 mt-3">
        <Dumbbell className="w-3 h-3 text-blue-500/40" />
        <span className="text-[10px] text-blue-400/40 font-medium tracking-wider uppercase">
          RivaFlow
        </span>
      </div>
    </div>
  );
}
