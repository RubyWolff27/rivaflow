/**
 * UpgradePrompt Component
 * Displays upgrade messages when users try to access premium features
 */

import { Crown, X } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from './ui';
import { FEATURE_DESCRIPTIONS } from '../config/tiers';

interface UpgradePromptProps {
  feature?: string;
  customTitle?: string;
  customDescription?: string;
  onClose?: () => void;
  inline?: boolean;
  showClose?: boolean;
}

export function UpgradePrompt({
  feature,
  customTitle,
  customDescription,
  onClose,
  inline = false,
  showClose = true,
}: UpgradePromptProps) {
  // Get feature info
  const featureInfo = feature ? FEATURE_DESCRIPTIONS[feature] : null;
  const title = customTitle || featureInfo?.title || 'Premium Feature';
  const description = customDescription || featureInfo?.description || 'This feature is available on our Premium plan.';

  const handleUpgrade = () => {
    // TODO: Navigate to pricing/upgrade page when implemented
    console.log('Upgrade clicked');
  };

  if (inline) {
    return (
      <Card className="p-4 border-[var(--accent)]/20 bg-gradient-to-r from-[var(--accent)]/5 to-transparent">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg" style={{ backgroundColor: 'var(--accent)', opacity: 0.1 }}>
            <Crown className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold mb-1" style={{ color: 'var(--text)' }}>
              {title}
            </h4>
            <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
              {description}
            </p>
            <PrimaryButton onClick={handleUpgrade} className="text-sm">
              Upgrade to Premium
            </PrimaryButton>
          </div>
          {showClose && onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-[var(--surfaceElev)] rounded"
              aria-label="Close"
            >
              <X className="w-4 h-4" style={{ color: 'var(--muted)' }} />
            </button>
          )}
        </div>
      </Card>
    );
  }

  // Modal version
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}>
      <Card className="max-w-md w-full p-6 relative">
        {showClose && onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 hover:bg-[var(--surfaceElev)] rounded"
            aria-label="Close"
          >
            <X className="w-5 h-5" style={{ color: 'var(--muted)' }} />
          </button>
        )}

        <div className="flex flex-col items-center text-center">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
            style={{ backgroundColor: 'var(--accent)', opacity: 0.1 }}
          >
            <Crown className="w-8 h-8" style={{ color: 'var(--accent)' }} />
          </div>

          <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--text)' }}>
            {title}
          </h3>

          <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
            {description}
          </p>

          <div className="w-full space-y-3">
            <PrimaryButton onClick={handleUpgrade} className="w-full">
              Upgrade to Premium
            </PrimaryButton>
            {onClose && (
              <SecondaryButton onClick={onClose} className="w-full">
                Maybe Later
              </SecondaryButton>
            )}
          </div>

          {/* Premium benefits */}
          <div className="mt-6 pt-6 border-t w-full" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs font-semibold mb-3" style={{ color: 'var(--text)' }}>
              Premium includes:
            </p>
            <ul className="text-xs space-y-2 text-left" style={{ color: 'var(--muted)' }}>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--accent)' }}>✓</span>
                <span>Advanced analytics with activity filtering</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--accent)' }}>✓</span>
                <span>Unlimited friends and training partners</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--accent)' }}>✓</span>
                <span>Unlimited photo uploads</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--accent)' }}>✓</span>
                <span>Friend suggestions and discovery</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--accent)' }}>✓</span>
                <span>Priority support</span>
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}

/**
 * LimitReachedPrompt Component
 * Displays when user reaches a tier limit (e.g., max friends)
 */
interface LimitReachedPromptProps {
  limitName: string;
  currentUsage: number;
  maxLimit: number;
  onClose?: () => void;
}

export function LimitReachedPrompt({
  limitName,
  currentUsage: _currentUsage,
  maxLimit,
  onClose,
}: LimitReachedPromptProps) {
  const getLimitMessage = () => {
    switch (limitName) {
      case 'max_friends':
        return {
          title: 'Friend Limit Reached',
          description: `You've reached your limit of ${maxLimit} friends on the Free plan.`,
        };
      case 'max_photos_per_session':
        return {
          title: 'Photo Limit Reached',
          description: `You can add up to ${maxLimit} photos per session on the Free plan.`,
        };
      default:
        return {
          title: 'Limit Reached',
          description: `You've reached your limit of ${maxLimit} for this feature.`,
        };
    }
  };

  const { title, description } = getLimitMessage();

  return (
    <UpgradePrompt
      customTitle={title}
      customDescription={description}
      onClose={onClose}
      inline={false}
    />
  );
}

/**
 * PremiumBadge Component
 * Small badge to indicate premium features
 */
export function PremiumBadge({ className = '' }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${className}`}
      style={{ backgroundColor: 'var(--accent)', color: 'white', opacity: 0.9 }}
    >
      <Crown className="w-3 h-3" />
      Premium
    </span>
  );
}

/**
 * BetaBadge Component
 * Badge for lifetime premium beta users
 */
export function BetaBadge({ className = '' }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${className}`}
      style={{ backgroundColor: 'var(--accent)', color: 'white' }}
    >
      <Crown className="w-3 h-3" />
      Beta
    </span>
  );
}
