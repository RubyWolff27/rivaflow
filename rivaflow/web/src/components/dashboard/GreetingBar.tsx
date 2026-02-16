import { Flame } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface GreetingBarProps {
  streakCount: number;
  longestStreak: number;
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function GreetingBar({ streakCount, longestStreak }: GreetingBarProps) {
  const { user } = useAuth();
  const firstName = user?.first_name || '';
  const isPersonalBest = streakCount > 0 && streakCount >= longestStreak;

  return (
    <div className="flex items-center justify-between px-1">
      <h1 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
        {getGreeting()}{firstName ? `, ${firstName}` : ''}
      </h1>
      {streakCount > 0 && (
        <div className="flex items-center gap-1.5">
          <Flame className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <span className="text-lg font-bold tabular-nums" style={{ color: 'var(--accent)' }}>
            {streakCount}
          </span>
          {isPersonalBest && streakCount >= 3 && (
            <span className="text-xs font-medium ml-1" style={{ color: 'var(--accent)' }}>
              Personal best!
            </span>
          )}
        </div>
      )}
    </div>
  );
}
