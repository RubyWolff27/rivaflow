import { useEffect, useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { garminApi, analyticsApi } from '../api/client';
import type { GarminDailyMetric } from '../types';
import GarminTrendChart from '../components/analytics/GarminTrendChart';
import { usePageTitle } from '../hooks/usePageTitle';
import { CardSkeleton } from '../components/ui';
import { HeartPulse, Moon, Activity, Zap, Footprints, Wind, Droplets, BedDouble } from 'lucide-react';

interface SleepDebt {
  available?: boolean;
  debt_hours?: number;
  nights?: number;
  tonight_recommended_hours?: number;
}

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
  const [sleepDebt, setSleepDebt] = useState<SleepDebt | null>(null);
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
      try {
        const p = await analyticsApi.physiology();
        if (alive) setSleepDebt(p.data?.sleep_debt ?? null);
      } catch {
        /* debt tile simply doesn't render */
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const series = (key: keyof GarminDailyMetric) =>
    metrics.map((m) => ({ date: m.metric_date, value: (m[key] as number | null) ?? null }));

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <CardSkeleton lines={3} />
        <CardSkeleton lines={5} />
      </div>
    );
  }

  if (!metrics.length) {
    return (
      <div className="max-w-3xl mx-auto p-4">
        <h1 className="text-xl font-bold mb-2">Health</h1>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          No health data yet — it appears here once your watch syncs.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <h1 className="text-xl font-bold">Health</h1>

      {latest && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Card
            icon={Zap}
            label="Readiness"
            value={fmt(latest.training_readiness_score)}
            sub={
              latest.training_readiness_score != null
                ? latest.training_readiness_score >= 66
                  ? 'green — train hard'
                  : latest.training_readiness_score >= 34
                    ? 'yellow — as planned'
                    : 'red — recover'
                : undefined
            }
          />
          <Card icon={HeartPulse} label="Resting HR" value={fmt(latest.rhr)} unit="bpm" />
          <Card icon={Activity} label="HRV" value={fmt(latest.hrv_ms)} unit="ms" sub={latest.hrv_status ?? undefined} />
          <Card
            icon={Moon}
            label="Sleep"
            value={fmt(latest.sleep_hours, 1)}
            unit="h"
            sub={
              latest.sleep_deep_hours != null && latest.sleep_rem_hours != null
                ? `deep ${Number(latest.sleep_deep_hours).toFixed(1)}h · REM ${Number(latest.sleep_rem_hours).toFixed(1)}h`
                : latest.sleep_score != null
                  ? `score ${Math.round(latest.sleep_score)}`
                  : undefined
            }
          />
          {sleepDebt?.available && (
            <Card
              icon={BedDouble}
              label="Sleep debt"
              value={fmt(sleepDebt.debt_hours, 1)}
              unit="h"
              sub={
                sleepDebt.tonight_recommended_hours != null
                  ? `over ${sleepDebt.nights} nights · aim ${sleepDebt.tonight_recommended_hours}h tonight`
                  : undefined
              }
            />
          )}
          <Card icon={Droplets} label="SpO2" value={fmt(latest.spo2_pct, 1)} unit="%" />
          <Card icon={Wind} label="Resp rate" value={fmt(latest.respiration_rate, 1)} unit="br/min" />
          <Card icon={Footprints} label="Steps" value={latest.steps != null ? latest.steps.toLocaleString() : '—'} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Panel><GarminTrendChart title="Training readiness" data={series('training_readiness_score')} color="#F59E0B" /></Panel>
        <Panel><GarminTrendChart title="HRV (ms)" data={series('hrv_ms')} color="#8B5CF6" /></Panel>
        <Panel><GarminTrendChart title="Resting HR (bpm)" data={series('rhr')} color="#EF4444" /></Panel>
        <Panel><GarminTrendChart title="Sleep (h)" data={series('sleep_hours')} color="#3B82F6" decimals={1} /></Panel>
        <Panel><GarminTrendChart title="Deep sleep (h)" data={series('sleep_deep_hours')} color="#1D4ED8" decimals={1} /></Panel>
        <Panel><GarminTrendChart title="SpO2 (%)" data={series('spo2_pct')} color="#10B981" decimals={1} /></Panel>
      </div>
    </div>
  );
}
