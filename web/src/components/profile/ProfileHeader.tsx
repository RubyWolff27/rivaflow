import { User, Crown, Star } from 'lucide-react';

interface TierInfo {
  isPremium: boolean;
  isBeta: boolean;
  displayName: string;
}

export interface ProfileHeaderProps {
  tierInfo: TierInfo;
}

export default function ProfileHeader({ tierInfo }: ProfileHeaderProps) {
  return (
    <>
      <div className="flex items-center gap-3">
        <User className="w-8 h-8 text-[var(--accent)]" />
        <h1 className="text-3xl font-bold">Profile</h1>
      </div>

      {/* Subscription Tier */}
      <div className="card bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {tierInfo.isPremium ? (
              <Crown className="w-6 h-6 text-[var(--accent)]" />
            ) : (
              <Star className="w-6 h-6 text-[var(--muted)]" />
            )}
            <div>
              <h2 className="text-lg font-semibold">Subscription Tier</h2>
              <p className="text-2xl font-bold text-[var(--accent)]">{tierInfo.displayName}</p>
              {tierInfo.isBeta && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 mt-1">
                  Beta User
                </span>
              )}
            </div>
          </div>
          {!tierInfo.isPremium && (
            <button className="btn-primary">
              Upgrade
            </button>
          )}
        </div>
        <div className="mt-3 text-sm text-[var(--muted)]">
          {tierInfo.isPremium ? (
            <p>You have access to all premium features. Thank you for your support!</p>
          ) : (
            <p>Upgrade to premium to unlock advanced analytics, unlimited sessions, and more.</p>
          )}
        </div>
      </div>
    </>
  );
}
