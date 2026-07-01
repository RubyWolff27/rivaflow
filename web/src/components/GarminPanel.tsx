import { Heart } from 'lucide-react';
import type { Session } from '../types';
import GarminZoneBar from './analytics/GarminZoneBar';

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

// Per-session Garmin biometrics: HR summary, time-in-HR-zones, training effect.
// Data rides on the session object (garmin_* fields). Renders nothing if unmatched.
export default function GarminPanel({ session }: { session: Session }) {
  const zones = [
    session.garmin_hr_z1_sec,
    session.garmin_hr_z2_sec,
    session.garmin_hr_z3_sec,
    session.garmin_hr_z4_sec,
    session.garmin_hr_z5_sec,
  ];
  const hasGarmin =
    session.garmin_avg_hr != null ||
    session.garmin_calories != null ||
    session.garmin_training_load != null ||
    zones.some((z) => z != null);
  if (!hasGarmin) return null;

  const teLabel = session.garmin_te_label ? session.garmin_te_label.replace(/_/g, ' ').toLowerCase() : null;

  return (
    <div className="rounded-2xl p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-2 mb-3">
        <Heart className="w-4 h-4" style={{ color: 'var(--accent)' }} />
        <span className="font-semibold text-sm">
          Garmin{session.garmin_activity_name ? ` — ${session.garmin_activity_name}` : ''}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
        {session.garmin_avg_hr != null && <Stat label="Avg HR" value={`${session.garmin_avg_hr}`} unit="bpm" />}
        {session.garmin_max_hr != null && <Stat label="Max HR" value={`${session.garmin_max_hr}`} unit="bpm" />}
        {session.garmin_calories != null && <Stat label="Calories" value={`${session.garmin_calories}`} />}
        {session.garmin_duration_min != null && <Stat label="Moving" value={`${Math.round(session.garmin_duration_min)}`} unit="min" />}
      </div>

      {zones.some((z) => z != null) && (
        <div className="mb-3">
          <div className="text-xs mb-1.5" style={{ color: 'var(--muted)' }}>Time in HR zones</div>
          <GarminZoneBar seconds={zones} />
        </div>
      )}

      {(session.garmin_aerobic_te != null || session.garmin_training_load != null) && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ color: 'var(--muted)' }}>
          {session.garmin_aerobic_te != null && (
            <span>Aerobic TE <b>{session.garmin_aerobic_te.toFixed(1)}</b>{teLabel ? ` (${teLabel})` : ''}</span>
          )}
          {session.garmin_anaerobic_te != null && session.garmin_anaerobic_te > 0 && (
            <span>Anaerobic <b>{session.garmin_anaerobic_te.toFixed(1)}</b></span>
          )}
          {session.garmin_training_load != null && <span>Load <b>{Math.round(session.garmin_training_load)}</b></span>}
        </div>
      )}
    </div>
  );
}
