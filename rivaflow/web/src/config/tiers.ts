/**
 * Tier System Configuration
 * Defines feature limits and permissions for each subscription tier
 */

export type TierName = 'free' | 'premium' | 'lifetime_premium' | 'admin';

export interface TierLimits {
  max_friends: number;
  max_photos_per_session: number;
  analytics_history_days: number;
  export_format: number;
}

export interface TierConfig {
  name: TierName;
  displayName: string;
  description: string;
  features: string[];
  limits: TierLimits;
}

// Tier configurations
export const TIERS: Record<TierName, TierConfig> = {
  free: {
    name: 'free',
    displayName: 'Free',
    description: 'Basic training tracking',
    features: [
      'session_tracking',
      'basic_analytics',
      'technique_tracking',
      'basic_dashboard',
    ],
    limits: {
      max_friends: 10,
      max_photos_per_session: 3,
      analytics_history_days: 90,
      export_format: 1, // Only CSV
    },
  },
  premium: {
    name: 'premium',
    displayName: 'Premium',
    description: 'Advanced features and unlimited tracking',
    features: [
      'session_tracking',
      'basic_analytics',
      'technique_tracking',
      'basic_dashboard',
      'advanced_analytics',
      'advanced_dashboard',
      'friend_suggestions',
      'unlimited_friends',
      'unlimited_photos',
      'export_all_formats',
      'priority_support',
    ],
    limits: {
      max_friends: -1, // -1 = unlimited
      max_photos_per_session: -1,
      analytics_history_days: -1,
      export_format: -1,
    },
  },
  lifetime_premium: {
    name: 'lifetime_premium',
    displayName: 'Lifetime Premium',
    description: 'Beta user - lifetime access to all premium features',
    features: [
      'session_tracking',
      'basic_analytics',
      'technique_tracking',
      'basic_dashboard',
      'advanced_analytics',
      'advanced_dashboard',
      'friend_suggestions',
      'unlimited_friends',
      'unlimited_photos',
      'export_all_formats',
      'priority_support',
      'beta_badge',
    ],
    limits: {
      max_friends: -1,
      max_photos_per_session: -1,
      analytics_history_days: -1,
      export_format: -1,
    },
  },
  admin: {
    name: 'admin',
    displayName: 'Admin',
    description: 'Full administrative access',
    features: [
      'session_tracking',
      'basic_analytics',
      'technique_tracking',
      'basic_dashboard',
      'advanced_analytics',
      'advanced_dashboard',
      'friend_suggestions',
      'unlimited_friends',
      'unlimited_photos',
      'export_all_formats',
      'priority_support',
      'admin_panel',
      'verify_gyms',
      'moderate_content',
    ],
    limits: {
      max_friends: -1,
      max_photos_per_session: -1,
      analytics_history_days: -1,
      export_format: -1,
    },
  },
};

// Helper functions
export function getTierConfig(tier: TierName): TierConfig | undefined {
  return TIERS[tier];
}

export function hasFeature(tier: TierName, feature: string): boolean {
  const config = TIERS[tier];
  if (!config) return false;
  return config.features.includes(feature);
}

export function getLimit(tier: TierName, limitName: keyof TierLimits): number {
  const config = TIERS[tier];
  if (!config) return 0;
  return config.limits[limitName];
}

export function isPremiumTier(tier: TierName): boolean {
  return ['premium', 'lifetime_premium', 'admin'].includes(tier);
}

// Feature descriptions for upgrade prompts
export const FEATURE_DESCRIPTIONS: Record<string, { title: string; description: string }> = {
  advanced_analytics: {
    title: 'Advanced Analytics',
    description: 'Filter by activity type, view detailed metrics, and track long-term progress',
  },
  advanced_dashboard: {
    title: 'Advanced Dashboard',
    description: 'Enhanced dashboard with comprehensive insights and personalized recommendations',
  },
  friend_suggestions: {
    title: 'Friend Suggestions',
    description: 'Get personalized suggestions based on your gym, location, and training partners',
  },
  unlimited_friends: {
    title: 'Unlimited Friends',
    description: 'Connect with unlimited training partners and track your network',
  },
  unlimited_photos: {
    title: 'Unlimited Photos',
    description: 'Add unlimited photos to your sessions to document techniques and progress',
  },
  export_all_formats: {
    title: 'Export All Formats',
    description: 'Export your training data in CSV, JSON, and PDF formats',
  },
};
