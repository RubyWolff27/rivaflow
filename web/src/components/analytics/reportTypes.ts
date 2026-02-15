export interface PerformanceOverview {
  summary?: {
    total_sessions?: number;
    avg_intensity?: number;
    total_rolls?: number;
    total_submissions_for?: number;
    total_hours?: number;
    top_class_type?: string;
    [key: string]: unknown;
  };
  daily_timeseries?: {
    sessions?: number[];
    intensity?: number[];
    rolls?: number[];
    submissions?: number[];
    [key: string]: unknown;
  };
  deltas?: {
    sessions?: number;
    intensity?: number;
    rolls?: number;
    submissions?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface PartnersData {
  top_partners?: Array<{
    id?: number;
    name?: string;
    belt_rank?: string;
    total_rolls?: number;
    submissions_for?: number;
    submissions_against?: number;
    sub_ratio?: number;
    [key: string]: unknown;
  }>;
  diversity_metrics?: { active_partners?: number; [key: string]: unknown };
  summary?: {
    total_rolls?: number;
    total_submissions_for?: number;
    total_submissions_against?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface TechniquesData {
  summary?: {
    total_unique_techniques_used?: number;
    stale_count?: number;
    [key: string]: unknown;
  };
  category_breakdown?: Array<{
    category?: string;
    count?: number;
    [key: string]: unknown;
  }>;
  gi_top_techniques?: Array<{
    id?: number;
    name?: string;
    count?: number;
    [key: string]: unknown;
  }>;
  nogi_top_techniques?: Array<{
    id?: number;
    name?: string;
    count?: number;
    [key: string]: unknown;
  }>;
  all_techniques?: Array<{ name: string; category: string; count: number }>;
  stale_techniques?: Array<{
    id?: number;
    name?: string;
    [key: string]: unknown;
  }>;
  top_submissions?: Array<{ name: string; category: string; count: number }>;
  submission_stats?: {
    total_submissions_for: number;
    total_submissions_against: number;
    sessions_with_submissions: number;
  };
  [key: string]: unknown;
}

export interface CalendarData {
  calendar?: Array<{ date: string; count: number; intensity: number }>;
  total_active_days?: number;
  activity_rate?: number;
  [key: string]: unknown;
}

export interface DurationData {
  overall_avg?: number;
  by_class_type?: Array<{
    class_type?: string;
    avg_duration?: number;
    sessions?: number;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

export interface TimeOfDayData {
  patterns?: Array<{
    time_slot?: string;
    sessions?: number;
    avg_intensity?: number;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

export interface GymData {
  gyms?: Array<{
    gym?: string;
    sessions?: number;
    avg_duration?: number;
    avg_intensity?: number;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

export interface ClassTypeData {
  class_types?: Array<{
    class_type?: string;
    sessions?: number;
    avg_rolls?: number;
    sub_rate?: number;
    total_subs_for?: number;
    total_subs_against?: number;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

export interface BeltDistData {
  distribution?: Array<{
    belt?: string;
    count?: number;
    [key: string]: unknown;
  }>;
  total_partners?: number;
  [key: string]: unknown;
}
