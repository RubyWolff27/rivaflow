"""
Tier System Configuration
Defines feature limits and permissions for each subscription tier
"""

from dataclasses import dataclass


@dataclass
class TierConfig:
    """Configuration for a subscription tier"""
    name: str
    display_name: str
    features: list[str]
    limits: dict[str, int]
    description: str

# Tier definitions
TIERS = {
    'free': TierConfig(
        name='free',
        display_name='Free',
        description='Basic training tracking',
        features=[
            'session_tracking',
            'basic_analytics',
            'technique_tracking',
            'basic_dashboard'
        ],
        limits={
            'max_friends': 10,
            'max_photos_per_session': 3,
            'analytics_history_days': 90,
            'export_format': 1,  # Only CSV
        }
    ),
    'premium': TierConfig(
        name='premium',
        display_name='Premium',
        description='Advanced features and unlimited tracking',
        features=[
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
            'priority_support'
        ],
        limits={
            'max_friends': -1,  # -1 = unlimited
            'max_photos_per_session': -1,
            'analytics_history_days': -1,
            'export_format': -1,
        }
    ),
    'lifetime_premium': TierConfig(
        name='lifetime_premium',
        display_name='Lifetime Premium',
        description='Beta user - lifetime access to all premium features',
        features=[
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
            'beta_badge'
        ],
        limits={
            'max_friends': -1,
            'max_photos_per_session': -1,
            'analytics_history_days': -1,
            'export_format': -1,
        }
    ),
    'admin': TierConfig(
        name='admin',
        display_name='Admin',
        description='Full administrative access',
        features=[
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
            'moderate_content'
        ],
        limits={
            'max_friends': -1,
            'max_photos_per_session': -1,
            'analytics_history_days': -1,
            'export_format': -1,
        }
    )
}

# Feature to tier mapping (for quick lookups)
FEATURE_REQUIREMENTS = {
    'advanced_analytics': ['premium', 'lifetime_premium', 'admin'],
    'advanced_dashboard': ['premium', 'lifetime_premium', 'admin'],
    'friend_suggestions': ['premium', 'lifetime_premium', 'admin'],
    'unlimited_friends': ['premium', 'lifetime_premium', 'admin'],
    'unlimited_photos': ['premium', 'lifetime_premium', 'admin'],
    'export_all_formats': ['premium', 'lifetime_premium', 'admin'],
    'admin_panel': ['admin'],
    'verify_gyms': ['admin'],
    'moderate_content': ['admin']
}

def get_tier_config(tier: str) -> TierConfig | None:
    """Get configuration for a specific tier"""
    return TIERS.get(tier)

def has_feature(tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature"""
    config = TIERS.get(tier)
    if not config:
        return False
    return feature in config.features

def get_limit(tier: str, limit_name: str) -> int:
    """Get a specific limit for a tier. Returns -1 for unlimited, 0 if not found"""
    config = TIERS.get(tier)
    if not config:
        return 0
    return config.limits.get(limit_name, 0)

def is_premium_tier(tier: str) -> bool:
    """Check if tier has premium features"""
    return tier in ['premium', 'lifetime_premium', 'admin']
