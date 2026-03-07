export const ACTIVITY_COLORS: Record<string, string> = {
  'gi': '#3B82F6',
  'no-gi': '#8B5CF6',
  's&c': '#EF4444',
  'drilling': '#F59E0B',
  'open-mat': '#10B981',
  'competition': '#EC4899',
  'cardio': '#F97316',
  'mobility': '#06B6D4',
};

export const ACTIVITY_LABELS: Record<string, string> = {
  'gi': 'Gi',
  'no-gi': 'No-Gi',
  'nogi': 'No-Gi',
  's&c': 'S&C',
  'drilling': 'Drilling',
  'open-mat': 'Open Mat',
  'open_mat': 'Open Mat',
  'competition': 'Competition',
  'cardio': 'Cardio',
  'mobility': 'Mobility',
};

/** Format a raw class_type value for display (e.g. "gi" -> "Gi", "no-gi" -> "No-Gi"). */
export function formatClassType(classType: string): string {
  return ACTIVITY_LABELS[classType] || classType;
}
