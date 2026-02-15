import type { MediaUrl } from '../../types';

export interface RollEntry {
  roll_number: number;
  partner_id: number | null;
  partner_name: string;
  duration_mins: number;
  submissions_for: number[];
  submissions_against: number[];
  notes: string;
}

export interface TechniqueEntry {
  technique_number: number;
  movement_id: number | null;
  movement_name: string;
  notes: string;
  media_urls: MediaUrl[];
}

export const SPARRING_TYPES = ['gi', 'no-gi', 'open-mat', 'competition'];
