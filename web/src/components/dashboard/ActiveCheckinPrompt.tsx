import { useNavigate } from 'react-router-dom';
import MorningPrompt from './MorningPrompt';
import MiddayPrompt from './MiddayPrompt';
import EveningPrompt from './EveningPrompt';
import CheckinBadges from './CheckinBadges';
import type { DayCheckins } from '../../types';

interface ActiveCheckinPromptProps {
  dayCheckins: DayCheckins | null;
  todayPlan: string | undefined;
  onCheckinUpdated: () => void;
}

export default function ActiveCheckinPrompt({
  dayCheckins,
  todayPlan,
  onCheckinUpdated,
}: ActiveCheckinPromptProps) {
  const navigate = useNavigate();
  const hour = new Date().getHours();

  const hasMorning = dayCheckins?.morning != null;
  const hasMidday = dayCheckins?.midday != null;
  const hasEvening = dayCheckins?.evening != null;
  const anyCompleted = hasMorning || hasMidday || hasEvening;

  // Show ONE prompt based on time of day
  if (hour < 11 && !hasMorning) {
    return (
      <div>
        <MorningPrompt onNavigate={() => navigate('/readiness')} />
        {anyCompleted && (
          <CheckinBadges dayCheckins={dayCheckins} onUpdated={onCheckinUpdated} />
        )}
      </div>
    );
  }

  if (hour >= 11 && hour < 16 && !hasMidday) {
    return (
      <div>
        <MiddayPrompt onSubmitted={onCheckinUpdated} todayPlan={todayPlan} />
        {anyCompleted && (
          <CheckinBadges dayCheckins={dayCheckins} onUpdated={onCheckinUpdated} />
        )}
      </div>
    );
  }

  if (hour >= 16 && !hasEvening) {
    return (
      <div>
        <EveningPrompt onSubmitted={onCheckinUpdated} />
        {anyCompleted && (
          <CheckinBadges dayCheckins={dayCheckins} onUpdated={onCheckinUpdated} />
        )}
      </div>
    );
  }

  // All relevant prompts completed — show compact badges
  if (anyCompleted) {
    return <CheckinBadges dayCheckins={dayCheckins} onUpdated={onCheckinUpdated} />;
  }

  return null;
}
