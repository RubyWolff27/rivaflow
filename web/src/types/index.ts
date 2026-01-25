export interface Session {
  id: number;
  session_date: string;
  class_type: string;
  gym_name: string;
  location?: string;
  duration_mins: number;
  intensity: number;
  rolls: number;
  submissions_for: number;
  submissions_against: number;
  partners?: string[];
  techniques?: string[];
  notes?: string;
  created_at: string;
}

export interface Readiness {
  id: number;
  check_date: string;
  sleep: number;
  stress: number;
  soreness: number;
  energy: number;
  hotspot_note?: string;
  composite_score: number;
  created_at: string;
}

export interface Technique {
  id: number;
  name: string;
  category?: string;
  last_trained_date?: string;
  created_at: string;
}

export interface Video {
  id: number;
  url: string;
  title?: string;
  timestamps?: { time: string; label: string }[];
  technique_id?: number;
  created_at: string;
}

export interface Report {
  start_date: string;
  end_date: string;
  sessions: Session[];
  summary: {
    total_classes: number;
    total_hours: number;
    total_rolls: number;
    unique_partners: number;
    submissions_for: number;
    submissions_against: number;
    avg_intensity: number;
    subs_per_class: number;
    subs_per_roll: number;
    taps_per_roll: number;
    sub_ratio: number;
  };
  breakdown_by_type: Record<string, { classes: number; hours: number; rolls: number }>;
  breakdown_by_gym: Record<string, number>;
}

export interface Suggestion {
  date: string;
  suggestion: string;
  triggered_rules: {
    name: string;
    recommendation: string;
    explanation: string;
    priority: number;
  }[];
  readiness?: Readiness;
  session_context: {
    consecutive_gi_sessions: number;
    consecutive_nogi_sessions: number;
    stale_techniques: Technique[];
  };
}

export interface Profile {
  id: number;
  date_of_birth?: string;
  age?: number; // Calculated from date_of_birth
  sex?: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  default_gym?: string;
  current_grade?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Grading {
  id: number;
  grade: string;
  date_graded: string;
  notes?: string;
  created_at?: string;
}
