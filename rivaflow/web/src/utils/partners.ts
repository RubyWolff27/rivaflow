import type { Friend } from '../types';

interface SocialFriend {
  id: number;
  first_name?: string;
  last_name?: string;
  display_name?: string;
}

/**
 * Convert social API friend objects into Friend[] objects with a 1_000_000 ID offset
 * to avoid collisions with manual partner IDs.
 */
export function mapSocialFriendsToPartners(friends: SocialFriend[]): Friend[] {
  return friends.map((sf) => ({
    id: sf.id + 1000000,
    name: sf.display_name || `${sf.first_name || ''} ${sf.last_name || ''}`.trim(),
    friend_type: 'training-partner' as const,
  }));
}
