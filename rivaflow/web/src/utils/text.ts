/**
 * Text formatting utilities
 */

/**
 * Pluralize a word based on count
 * @param count - The number to check
 * @param singular - Singular form of the word
 * @param plural - Plural form (defaults to singular + 's')
 * @returns The appropriate form based on count
 */
export function pluralize(count: number, singular: string, plural?: string): string {
  if (count === 1) {
    return singular;
  }
  return plural || `${singular}s`;
}

/**
 * Format a count with its unit (properly pluralized)
 * @param count - The number
 * @param unit - The unit name (singular form)
 * @param plural - Optional custom plural form
 * @returns Formatted string like "1 day" or "5 days"
 */
export function formatCount(count: number, unit: string, plural?: string): string {
  return `${count} ${pluralize(count, unit, plural)}`;
}

/**
 * Format duration in a human-readable way
 * @param minutes - Duration in minutes
 * @returns Formatted string like "1 hour" or "90 minutes"
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return formatCount(minutes, 'minute');
  }

  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (mins === 0) {
    return formatCount(hours, 'hour');
  }

  return `${hours}h ${mins}m`;
}
