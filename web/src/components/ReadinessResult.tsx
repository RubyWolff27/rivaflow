import { useNavigate } from 'react-router-dom';
import { PrimaryButton, SecondaryButton } from './ui';

interface ReadinessResultProps {
  compositeScore: number;
  suggestion?: string;
  triggeredRules?: { name: string; recommendation: string; explanation: string; priority: number }[];
}

export default function ReadinessResult({ compositeScore, suggestion, triggeredRules }: ReadinessResultProps) {
  const navigate = useNavigate();

  let label: string;
  let color: string;
  let bgColor: string;

  if (compositeScore >= 16) {
    label = 'Train Hard';
    color = 'var(--success)';
    bgColor = 'var(--success-bg)';
  } else if (compositeScore >= 12) {
    label = 'Light Session';
    color = 'var(--warning)';
    bgColor = 'var(--warning-bg)';
  } else {
    label = 'Rest Day';
    color = 'var(--danger)';
    bgColor = 'var(--danger-bg)';
  }

  return (
    <div className="card text-center space-y-4">
      <div
        className="inline-flex items-center justify-center w-20 h-20 rounded-full mx-auto"
        style={{ backgroundColor: bgColor }}
      >
        <span className="text-3xl font-bold" style={{ color }}>
          {compositeScore}
        </span>
      </div>
      <div>
        <span
          className="text-lg font-semibold px-4 py-1 rounded-full"
          style={{ backgroundColor: bgColor, color }}
        >
          {label}
        </span>
      </div>
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        Composite score: {compositeScore}/20
      </p>
      {suggestion && (
        <p className="text-sm" style={{ color: 'var(--text)' }}>
          {suggestion}
        </p>
      )}
      {triggeredRules && triggeredRules.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1">
          {triggeredRules.slice(0, 3).map((rule, i) => (
            <span
              key={i}
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)', border: '1px solid var(--border)' }}
            >
              {rule.name}
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-3 justify-center pt-2">
        <PrimaryButton onClick={() => navigate('/log')} className="flex items-center gap-2">
          Log Session
        </PrimaryButton>
        <SecondaryButton onClick={() => navigate('/log')} className="flex items-center gap-2">
          Log Rest Day
        </SecondaryButton>
      </div>
    </div>
  );
}
