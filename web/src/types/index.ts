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
  session_score?: number;
  score_breakdown?: SessionScoreBreakdown;
  score_version?: number;
  source?: 'manual' | 'whoop';
  needs_review?: boolean;
  created_at: string;
}

export interface SessionScorePillar {
  score: number;
  max: number;
  pct: number;
}

export interface SessionScoreBreakdown {
  version: number;
  rubric: 'bjj' | 'competition' | 'supplementary';
  total: number;
  label: string;
  pillars: Record<string, SessionScorePillar>;
  data_completeness: number;
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
  hrv_ms?: number;
  resting_hr?: number;
  spo2?: number;
  whoop_recovery_score?: number;
  whoop_sleep_score?: number;
  data_source?: string;
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

export interface TrainedMovement extends Movement {
  last_trained_date?: string;
  train_count?: number;
}

export interface Video {
  id: number;
  url: string;
  title?: string;
  timestamps?: { time: string; label: string }[];
  technique_id?: number;
  movement_id?: number;
  movement_name?: string;
  video_type?: string;
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
  primary_training_type?: string;
  height_cm?: number;
  target_weight_kg?: number;
  target_weight_date?: string;
  weekly_sessions_target?: number;
  weekly_hours_target?: number;
  weekly_rolls_target?: number;
  weekly_bjj_sessions_target?: number;
  weekly_sc_sessions_target?: number;
  weekly_mobility_sessions_target?: number;
  show_streak_on_dashboard?: boolean;
  show_weekly_goals?: boolean;
  timezone?: string;
  avatar_url?: string;
  primary_gym_id?: number;
  activity_visibility?: 'friends' | 'private';
  // Journey progress fields
  belt_rank?: string; // Deprecated, use current_grade
  belt_stripes?: number; // Deprecated, use current_grade
  total_sessions?: number; // Total all-time sessions
  total_hours?: number; // Total all-time hours
  sessions_since_promotion?: number; // Sessions at current belt
  hours_since_promotion?: number; // Hours at current belt
  promotion_date?: string; // Date of last belt promotion
  created_at?: string;
  updated_at?: string;
}

export interface Grading {
  id: number;
  grade: string;
  date_graded: string;
  professor?: string;
  instructor_id?: number;
  notes?: string;
  photo_url?: string;
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

export interface WeeklyGoalProgress {
  week_start: string;
  week_end: string;
  targets: {
    sessions: number;
    hours: number;
    rolls: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
  };
  actual: {
    sessions: number;
    hours: number;
    rolls: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
  };
  progress: {
    sessions_pct: number;
    hours_pct: number;
    rolls_pct: number;
    overall_pct: number;
    bjj_sessions_pct?: number;
    sc_sessions_pct?: number;
    mobility_sessions_pct?: number;
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
  checkin_type: 'session' | 'rest' | 'readiness_only' | 'midday' | 'evening';
  checkin_slot: 'morning' | 'midday' | 'evening';
  rest_type?: string;
  rest_note?: string;
  session_id?: number;
  readiness_id?: number;
  tomorrow_intention?: string;
  insight_shown?: string; // JSON string
  energy_level?: number;
  midday_note?: string;
  training_quality?: number;
  recovery_note?: string;
  created_at: string;
}

export interface DayCheckins {
  date: string;
  checked_in: boolean;
  morning: DailyCheckin | null;
  midday: DailyCheckin | null;
  evening: DailyCheckin | null;
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

export interface FeedItemData {
  // Session fields
  class_type?: string;
  class_time?: string;
  gym_name?: string;
  location?: string;
  duration_mins?: number;
  intensity?: number;
  rolls?: number;
  submissions_for?: number;
  submissions_against?: number;
  partners?: string[];
  techniques?: string[];
  notes?: string;
  instructor_name?: string;
  // Rest fields
  rest_type?: string;
  rest_note?: string;
  // Shared fields
  tomorrow_intention?: string;
  visibility?: string;
  visibility_level?: string;
}

export interface FeedItem {
  type: 'session' | 'rest';
  date: string;
  id: number;
  data: FeedItemData;
  summary: string;
  thumbnail?: string;
  photo_count?: number;
  like_count?: number;
  comment_count?: number;
  has_liked?: boolean;
  owner_user_id?: number;
  owner?: {
    first_name?: string;
    last_name?: string;
  };
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


// Events & Competition Prep (v0.3)
export interface CompEvent {
  id: number;
  name: string;
  event_type: string;
  event_date: string;
  location?: string;
  weight_class?: string;
  target_weight?: number;
  division?: string;
  notes?: string;
  status: string;
  created_at: string;
}

export interface WeightLog {
  id: number;
  weight: number;
  logged_date: string;
  time_of_day?: string;
  notes?: string;
  created_at?: string;
}

export interface WeightAverage {
  period: string;
  avg_weight: number;
  min_weight: number;
  max_weight: number;
  entries: number;
}


// Groups (v0.3)
export interface Group {
  id: number;
  name: string;
  description?: string;
  group_type: 'training_crew' | 'comp_team' | 'study_group' | 'gym_class';
  privacy: 'open' | 'invite_only';
  gym_id?: number;
  created_by: number;
  avatar_url?: string;
  created_at: string;
  member_count?: number;
  member_role?: string;
  members?: GroupMember[];
  user_role?: string;
}

export interface GroupMember {
  id: number;
  group_id: number;
  user_id: number;
  role: 'admin' | 'member';
  joined_at: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

// Game Plans (My Game)
export interface GamePlan {
  id: number;
  user_id: number;
  belt_level: string;
  archetype: string;
  style: string;
  title?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  nodes?: GamePlanNode[];
  flat_nodes?: GamePlanNode[];
  edges?: GamePlanEdge[];
  focus_nodes?: GamePlanNode[];
}

export interface GamePlanNode {
  id: number;
  plan_id: number;
  parent_id?: number;
  name: string;
  node_type: string;
  glossary_id?: number;
  confidence: number;
  priority: string;
  is_focus: boolean;
  attempts: number;
  successes: number;
  last_used_date?: string;
  sort_order: number;
  notes?: string;
  children?: GamePlanNode[];
  created_at: string;
  updated_at: string;
}

export interface GamePlanEdge {
  id: number;
  plan_id: number;
  from_node_id: number;
  to_node_id: number;
  edge_type: string;
  label?: string;
  created_at: string;
}

// Monthly Training Goals
export interface TrainingGoal {
  id: number;
  goal_type: 'frequency' | 'technique';
  metric: 'sessions' | 'hours' | 'rolls' | 'submissions' | 'technique_count';
  target_value: number;
  month: string;
  movement_id: number | null;
  movement_name?: string;
  class_type_filter: string | null;
  is_active: boolean;
  actual_value: number;
  progress_pct: number;
  completed: boolean;
}

// AI Insights
export interface AIInsight {
  id: number;
  user_id: number;
  session_id?: number;
  insight_type: string;
  title: string;
  content: string;
  category: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

// WHOOP Integration
export interface WhoopConnectionStatus {
  connected: boolean;
  whoop_user_id?: string;
  connected_at?: string;
  last_synced_at?: string;
  auto_create_sessions?: boolean;
  auto_fill_readiness?: boolean;
}

export interface WhoopWorkout {
  id: number;
  whoop_workout_id: string;
  sport_id?: number;
  sport_name?: string;
  start_time: string;
  end_time: string;
  strain?: number;
  avg_heart_rate?: number;
  max_heart_rate?: number;
  kilojoules?: number;
  calories?: number;
  score_state?: string;
  zone_durations?: Record<string, number>;
  session_id?: number;
}

export interface WhoopWorkoutMatch extends WhoopWorkout {
  overlap_pct: number;
}

export interface WhoopRecovery {
  recovery_score: number | null;
  resting_hr: number | null;
  hrv_ms: number | null;
  spo2: number | null;
  sleep_performance: number | null;
  sleep_duration_ms: number | null;
  cycle_start: string;
  cycle_end?: string;
}

export interface WhoopScopeCheck {
  current_scopes: string[];
  required_scopes: string[];
  needs_reauth: boolean;
  missing_scopes: string[];
}

export interface WhoopReadinessAutoFill {
  sleep: number;
  energy: number;
  hrv_ms: number | null;
  resting_hr: number | null;
  spo2: number | null;
  whoop_recovery_score: number | null;
  whoop_sleep_score: number | null;
  data_source: string;
}

// WHOOP Session Context
export interface WhoopSessionContext {
  recovery: {
    score: number | null;
    hrv_ms: number | null;
    resting_hr: number | null;
    sleep_performance: number | null;
    sleep_duration_hours: number | null;
    rem_pct: number | null;
    sws_pct: number | null;
  } | null;
  workout: {
    zone_durations: Record<string, number> | null;
    score_state?: string | null;
    strain?: number | null;
    avg_heart_rate?: number | null;
    max_heart_rate?: number | null;
    calories?: number | null;
    kilojoules?: number | null;
    sport_name?: string | null;
  } | null;
}

// Extracted Session
export interface ExtractedSession {
  session_date?: string;
  class_type?: string;
  gym_name?: string;
  duration_mins?: number;
  intensity?: number;
  rolls?: number;
  submissions_for?: number;
  submissions_against?: number;
  partners?: string[];
  techniques?: string[];
  notes?: string;
  events?: ExtractedEvent[];
  parse_error?: boolean;
}

export interface ExtractedEvent {
  event_type: string;
  technique_name?: string;
  position?: string;
  outcome?: string;
  partner_name?: string;
}

// Auth user (extends base User with auth-specific fields)
export interface AuthUser extends User {
  is_admin?: boolean;
  subscription_tier?: string;
  is_beta_user?: boolean;
  tier_expires_at?: string;
  beta_joined_at?: string;
}

// Week stats (used by dashboard components)
export interface WeekStats {
  total_sessions: number;
  total_hours: number;
  total_rolls: number;
  class_types: Record<string, number>;
}

// Gym class for timetable
export interface GymClass {
  id: number;
  gym_id: number;
  day_of_week: number;
  day_name: string;
  start_time: string;
  end_time: string;
  class_name: string;
  class_type: string | null;
  level: string | null;
  is_active: number;
}
