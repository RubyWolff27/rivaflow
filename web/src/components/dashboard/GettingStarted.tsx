import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, ChevronRight } from 'lucide-react';
import { Card } from '../ui';
import { profileApi } from '../../api/client';

interface Step {
  key: string;
  label: string;
  done: boolean;
}

const NAV_MAP: Record<string, string> = {
  profile: '/profile',
  readiness: '/readiness',
  session: '/log',
  goals: '/profile',
};

export default function GettingStarted() {
  const navigate = useNavigate();
  const [steps, setSteps] = useState<Step[]>([]);
  const [allDone, setAllDone] = useState(false);
  const [completed, setCompleted] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem('onboarding_dismissed') === '1',
  );

  useEffect(() => {
    if (dismissed) return;
    let cancelled = false;
    const load = async () => {
      try {
        const res = await profileApi.getOnboardingStatus();
        if (!cancelled) {
          setSteps(res.data.steps);
          setAllDone(res.data.all_done);
          setCompleted(res.data.completed);
          setTotal(res.data.total);
        }
      } catch {
        // Endpoint not available — hide widget
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [dismissed]);

  if (loading || dismissed || allDone) return null;

  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          Getting Started
        </h3>
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
          >
            {pct}%
          </span>
          <button
            onClick={() => {
              sessionStorage.setItem('onboarding_dismissed', '1');
              setDismissed(true);
            }}
            className="text-xs"
            style={{ color: 'var(--muted)' }}
          >
            Dismiss
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="h-1.5 rounded-full mb-3"
        style={{ backgroundColor: 'var(--border)' }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: 'var(--accent)' }}
        />
      </div>

      <div className="space-y-1">
        {steps.map((step) => (
          <button
            key={step.key}
            onClick={() => !step.done && navigate(NAV_MAP[step.key] || '/profile')}
            disabled={step.done}
            className="w-full flex items-center gap-2 py-1.5 text-left text-sm rounded-lg transition-colors"
            style={{ color: step.done ? 'var(--muted)' : 'var(--text)' }}
          >
            {step.done ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" style={{ color: 'var(--accent)' }} />
            ) : (
              <Circle className="w-4 h-4 shrink-0" style={{ color: 'var(--border)' }} />
            )}
            <span className={step.done ? 'line-through' : ''}>{step.label}</span>
            {!step.done && (
              <ChevronRight className="w-3.5 h-3.5 ml-auto shrink-0" style={{ color: 'var(--muted)' }} />
            )}
          </button>
        ))}
      </div>
    </Card>
  );
}
