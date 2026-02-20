import { vi } from 'vitest';

export function createMockToast() {
  return {
    useToast: () => ({
      showToast: vi.fn(),
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    }),
  };
}

export function createMockAuth(overrides?: {
  user?: Record<string, unknown>;
  isLoading?: boolean;
}) {
  return {
    useAuth: () => ({
      user: {
        id: 1,
        email: 'test@example.com',
        first_name: 'Ruby',
        last_name: 'Test',
        subscription_tier: 'beta',
        is_beta_user: true,
        ...overrides?.user,
      },
      isLoading: overrides?.isLoading ?? false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    }),
  };
}

export function createMockPageTitle() {
  return {
    usePageTitle: vi.fn(),
  };
}

export function createMockLogger() {
  return {
    logger: {
      log: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    },
  };
}

export function createMockInsightRefresh() {
  return {
    refreshIfStale: vi.fn(),
    triggerInsightRefresh: vi.fn(),
  };
}

export function createMockTier(overrides?: {
  tier?: string;
  isFree?: boolean;
  isBeta?: boolean;
  isPro?: boolean;
  label?: string;
}) {
  return {
    useTier: () => ({
      tier: overrides?.tier ?? 'beta',
      isFree: overrides?.isFree ?? false,
      isBeta: overrides?.isBeta ?? true,
      isPro: overrides?.isPro ?? false,
      label: overrides?.label ?? 'Beta',
    }),
  };
}
