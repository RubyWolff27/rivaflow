import { Activity } from 'lucide-react';
import type { Session } from '../types';

function Stat({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div>
      <div className="text-xs" style={{ color: 'var(--muted)' }}>{label}</div>
      <div className="text-lg font-semibold">
        {value}
        {unit ? <span className="text-xs font-normal ml-0.5" style={{ color: 'var(--muted)' }}>{unit}</span> : null}
      </div>
    </div>
  );
}

// Per-session Strava biometrics. Data rides on the session object (strava_* fields),
// the same way GarminPanel reads garmin_*. Renders nothing when unmatched.
export default function StravaPanel({ session }: { session: Session }) {
  const hasStrava =
    session.strava_avg_hr != null ||
    session.strava_max_hr != null ||
    session.strava_calories != null ||
    session.strava_suffer_score != null;
  if (!hasStrava) return null;

  const distanceKm =
    session.strava_distance_m != null && session.strava_distance_m > 0
      ? (session.strava_distance_m / 1000).toFixed(1)
      : null;

  return (
    <div className="rounded-2xl p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-2 mb-3">
        <Activity className="w-4 h-4" style={{ color: '#FC4C02' }} />
        <span className="font-semibold text-sm">
          Strava{session.strava_activity_name ? ` — ${session.strava_activity_name}` : ''}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {session.strava_avg_hr != null && <Stat label="Avg HR" value={`${session.strava_avg_hr}`} unit="bpm" />}
        {session.strava_max_hr != null && <Stat label="Max HR" value={`${session.strava_max_hr}`} unit="bpm" />}
        {session.strava_calories != null && <Stat label="Calories" value={`${session.strava_calories}`} />}
        {session.strava_duration_min != null && (
          <Stat label="Duration" value={`${Math.round(session.strava_duration_min)}`} unit="min" />
        )}
        {distanceKm && <Stat label="Distance" value={distanceKm} unit="km" />}
        {session.strava_suffer_score != null && (
          <Stat label="Relative effort" value={`${Math.round(session.strava_suffer_score)}`} />
        )}
      </div>
    </div>
  );
}
