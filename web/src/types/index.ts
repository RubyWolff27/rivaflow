export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: number;
  session_date: string;
  class_time?: string;
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
  instructor_id?: number;
  instructor_name?: string;
  detailed_rolls?: SessionRoll[];  // Populated when fetched with /with-rolls endpoint
  session_techniques?: SessionTechnique[];  // Detailed technique tracking
  whoop_strain?: number;
  whoop_calories?: number;
  whoop_avg_hr?: number;
  whoop_max_hr?: number;
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
  weight_kg?: number;
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
  readiness: Readiness[];
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
  weight_tracking: {
    has_data: boolean;
    start_weight: number | null;
    end_weight: number | null;
    weight_change: number | null;
    min_weight: number | null;
    max_weight: number | null;
    avg_weight: number | null;
    entries: { date: string; weight_kg: number }[];
  };
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
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  age?: number; // Calculated from date_of_birth
  sex?: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  city?: string;
  state?: string;
  default_gym?: string;
  default_location?: string;
  current_grade?: string;
  current_professor?: string;
  current_instructor_id?: number;
  height_cm?: number;
  target_weight_kg?: number;
  weekly_sessions_target?: number;
  weekly_hours_target?: number;
  weekly_rolls_target?: number;
  show_streak_on_dashboard?: boolean;
  show_weekly_goals?: boolean;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Grading {
  id: number;
  grade: string;
  date_graded: string;
  professor?: string;
  notes?: string;
  created_at?: string;
}

export interface Movement {
  id: number;
  name: string;
  category: 'position' | 'submission' | 'sweep' | 'pass' | 'takedown' | 'escape' | 'movement' | 'concept' | 'defense';
  subcategory?: string;
  points: number;
  description?: string;
  aliases: string[];
  gi_applicable: boolean;
  nogi_applicable: boolean;
  ibjjf_legal_white: boolean;
  ibjjf_legal_blue: boolean;
  ibjjf_legal_purple: boolean;
  ibjjf_legal_brown: boolean;
  ibjjf_legal_black: boolean;
  custom: boolean;
  gi_video_url?: string;
  nogi_video_url?: string;
  custom_videos?: CustomVideo[];
  created_at?: string;
}

export interface CustomVideo {
  id: number;
  movement_id: number;
  title?: string;
  url: string;
  video_type: 'gi' | 'nogi' | 'general';
  created_at: string;
}

export interface Friend {
  id: number;
  name: string;
  friend_type: 'instructor' | 'training-partner' | 'both';
  belt_rank?: 'white' | 'blue' | 'purple' | 'brown' | 'black';
  belt_stripes?: number;
  instructor_certification?: string;
  phone?: string;
  email?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SessionRoll {
  id: number;
  session_id: number;
  partner_id?: number;
  partner_name?: string;
  roll_number: number;
  duration_mins?: number;
  submissions_for?: number[];  // Movement IDs from glossary
  submissions_against?: number[];  // Movement IDs from glossary
  notes?: string;
  created_at?: string;
}

export interface MediaUrl {
  type: 'video' | 'image';
  url: string;
  title?: string;
}

export interface SessionTechnique {
  id?: number;
  session_id?: number;
  movement_id: number;
  movement_name?: string;  // Populated from glossary
  technique_number: number;
  notes?: string;
  media_urls?: MediaUrl[];
  created_at?: string;
}

export interface CustomVideo {
  id: number;
  movement_id: number;
  title?: string;
  url: string;
  video_type: 'gi' | 'nogi' | 'general';
  created_at: string;
}
export interface WeeklyGoalProgress {
  week_start: string;
  week_end: string;
  targets: {
    sessions: number;
    hours: number;
    rolls: number;
  };
  actual: {
    sessions: number;
    hours: number;
    rolls: number;
  };
  progress: {
    sessions_pct: number;
    hours_pct: number;
    rolls_pct: number;
    overall_pct: number;
  };
  completed: boolean;
  days_remaining: number;
}

export interface TrainingStreaks {
  current_streak: number;
  longest_streak: number;
  last_updated: string;
}

export interface GoalCompletionStreak {
  current_streak: number;
  longest_streak: number;
}

export interface GoalsSummary {
  current_week: WeeklyGoalProgress;
  training_streaks: TrainingStreaks;
  goal_streaks: GoalCompletionStreak;
  recent_trend: {
    week_start: string;
    week_end: string;
    completion_pct: number;
    completed: boolean;
    targets: { sessions: number; hours: number; rolls: number };
    actual: { sessions: number; hours: number; rolls: number };
  }[];
}

// Engagement features (v0.2)
export interface DailyCheckin {
  id: number;
  check_date: string;
  checkin_type: 'session' | 'rest' | 'readiness_only';
  rest_type?: string;
  rest_note?: string;
  session_id?: number;
  readiness_id?: number;
  tomorrow_intention?: string;
  insight_shown?: string; // JSON string
  created_at: string;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  streak_started_date?: string;
  last_checkin_date?: string;
  grace_days_used?: number;
}

export interface StreakStatus {
  checkin: Streak;
  training: Streak;
  readiness: Streak;
  any_at_risk: boolean;
}

export interface Milestone {
  id: number;
  milestone_type: 'hours' | 'sessions' | 'rolls' | 'partners' | 'techniques' | 'streak';
  milestone_value: number;
  milestone_label: string;
  achieved_at: string;
  celebrated: boolean;
}

export interface MilestoneProgress {
  type: string;
  current: number;
  next_value: number;
  next_label: string;
  percentage: number;
  remaining: number;
}

export interface Insight {
  type: 'stat' | 'streak' | 'milestone' | 'recovery' | 'trend' | 'encouragement';
  title: string;
  message: string;
  action?: string;
  icon?: string;
}

// Social features
export interface UserBasic {
  id: number;
  first_name: string;
  last_name: string;
  email?: string;
}

export interface ActivityLike {
  id: number;
  user_id: number;
  activity_type: 'session' | 'readiness' | 'rest';
  activity_id: number;
  created_at: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface ActivityComment {
  id: number;
  user_id: number;
  activity_type: 'session' | 'readiness' | 'rest';
  activity_id: number;
  comment_text: string;
  parent_comment_id?: number;
  edited_at?: string;
  created_at: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface FeedItem {
  type: 'session' | 'readiness' | 'rest';
  date: string;
  id: number;
  data: any;
  summary: string;
  like_count?: number;
  comment_count?: number;
  has_liked?: boolean;
  owner_user_id?: number;
}

export interface UserRelationship {
  relationship_id: number;
  follower_user_id?: number;
  following_user_id?: number;
  followed_at: string;
  first_name: string;
  last_name: string;
  email: string;
}
