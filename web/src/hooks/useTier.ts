/**
 * React Hook for Tier Access Control
 * Provides functions to check user's tier permissions and feature access
 */

import { useAuth } from '../contexts/AuthContext';
import { hasFeature, isPremiumTier, getLimit, getTierConfig, type TierName, type TierLimits } from '../config/tiers';

export interface TierInfo {
  tier: TierName;
  displayName: string;
  isPremium: boolean;
  isBeta: boolean;
  hasFeature: (feature: string) => boolean;
  getLimit: (limitName: keyof TierLimits) => number;
  isUnlimited: (limitName: keyof TierLimits) => boolean;
}

export function useTier(): TierInfo {
  const { user } = useAuth();

  const tier = (user?.subscription_tier as TierName) || 'free';
  const config = getTierConfig(tier);

  return {
    tier,
    displayName: config?.displayName || 'Free',
    isPremium: isPremiumTier(tier),
    isBeta: user?.is_beta_user || false,
    hasFeature: (feature: string) => hasFeature(tier, feature),
    getLimit: (limitName: keyof TierLimits) => getLimit(tier, limitName),
    isUnlimited: (limitName: keyof TierLimits) => getLimit(tier, limitName) === -1,
  };
}

/**
 * Hook for checking a specific feature
 * Returns whether the user has access and metadata about the feature
 */
export function useFeatureAccess(feature: string) {
  const tierInfo = useTier();
  const hasAccess = tierInfo.hasFeature(feature);

  return {
    hasAccess,
    tier: tierInfo.tier,
    isPremium: tierInfo.isPremium,
    requiresUpgrade: !hasAccess && !tierInfo.isPremium,
  };
}

/**
 * Hook for checking usage limits
 * Returns current usage, limit, and whether user can perform action
 */
export function useUsageLimit(limitName: keyof TierLimits, currentUsage: number = 0) {
  const tierInfo = useTier();
  const limit = tierInfo.getLimit(limitName);
  const isUnlimited = limit === -1;
  const canPerformAction = isUnlimited || currentUsage < limit;
  const usagePercentage = isUnlimited ? 0 : (currentUsage / limit) * 100;

  return {
    currentUsage,
    limit,
    isUnlimited,
    canPerformAction,
    usagePercentage,
    remainingCount: isUnlimited ? -1 : Math.max(0, limit - currentUsage),
    isNearLimit: !isUnlimited && usagePercentage >= 80,
    isAtLimit: !isUnlimited && currentUsage >= limit,
  };
}
