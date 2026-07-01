import { useEffect, useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { garminApi } from '../api/client';
import type { GarminDailyMetric } from '../types';
import GarminTrendChart from '../components/analytics/GarminTrendChart';
import { usePageTitle } from '../hooks/usePageTitle';
import { HeartPulse, Battery, Moon, Activity, Zap, Footprints } from 'lucide-react';

function fmt(v: number | null | undefined, dec = 0): string {
  return v == null ? '—' : Number(v).toFixed(dec);
}

function Card({ icon: Icon, label, value, unit, sub }: { icon: ComponentType<{ className?: string }>; label: string; value: string; unit?: string; sub?: string }) {
  return (
    <div className="rounded-2xl p-3" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-1.5 text-xs mb-1" style={{ color: 'var(--muted)' }}>
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div className="text-xl font-bold">
        {value}
        {unit ? <span className="text-xs font-normal ml-0.5" style={{ color: 'var(--muted)' }}>{unit}</span> : null}
      </div>
      {sub ? <div className="text-xs capitalize" style={{ color: 'var(--muted)' }}>{sub}</div> : null}
    </div>
  );
}

function Panel({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      {children}
    </div>
  );
}

export default function Health() {
  usePageTitle('Health');
  const [metrics, setMetrics] = useState<GarminDailyMetric[]>([]);
  const [latest, setLatest] = useState<GarminDailyMetric | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [d, s] = await Promise.all([garminApi.dailyMetrics(90), garminApi.summary()]);
        if (!alive) return;
        setMetrics(d.data ?? []);
        setLatest(s.data?.latest ?? null);
      } catch {
        /* ignore — page renders empty state */
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const series = (key: keyof GarminDailyMetric) =>
    metrics.map((m) => ({ date: m.metric_date, value: (m[key] as number | null) ?? null }));

  if (loading) {
    return <div className="p-4 text-sm" style={{ color: 'var(--muted)' }}>Loading Garmin metrics…</div>;
  }

  if (!metrics.length) {
    return (
      <div className="max-w-3xl mx-auto p-4">
        <h1 className="text-xl font-bold mb-2">Health</h1>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          No Garmin data yet — it appears here once your daily metrics sync.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <h1 className="text-xl font-bold">Health</h1>

      {latest && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Card icon={HeartPulse} label="Resting HR" value={fmt(latest.rhr)} unit="bpm" />
          <Card icon={Activity} label="HRV" value={fmt(latest.hrv_ms)} unit="ms" sub={latest.hrv_status ?? undefined} />
          <Card
            icon={Battery}
            label="Body Battery"
            value={latest.body_battery_high != null && latest.body_battery_low != null ? `${latest.body_battery_high}→${latest.body_battery_low}` : '—'}
          />
          <Card icon={Moon} label="Sleep" value={fmt(latest.sleep_hours, 1)} unit="h" sub={latest.sleep_score != null ? `score ${Math.round(latest.sleep_score)}` : undefined} />
          <Card icon={Zap} label="Readiness" value={fmt(latest.training_readiness_score)} sub={latest.training_readiness_level ? latest.training_readiness_level.toLowerCase() : undefined} />
          <Card icon={Footprints} label="Steps" value={latest.steps != null ? latest.steps.toLocaleString() : '—'} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Panel><GarminTrendChart title="HRV (ms)" data={series('hrv_ms')} color="#8B5CF6" /></Panel>
        <Panel><GarminTrendChart title="Resting HR (bpm)" data={series('rhr')} color="#EF4444" /></Panel>
        <Panel><GarminTrendChart title="Body Battery (peak)" data={series('body_battery_high')} color="#10B981" /></Panel>
        <Panel><GarminTrendChart title="Sleep (h)" data={series('sleep_hours')} color="#3B82F6" decimals={1} /></Panel>
        <Panel><GarminTrendChart title="Training readiness" data={series('training_readiness_score')} color="#F59E0B" /></Panel>
        <Panel><GarminTrendChart title="Avg stress" data={series('stress_avg')} color="#6B7280" /></Panel>
      </div>
    </div>
  );
}
