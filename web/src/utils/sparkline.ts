/**
 * Generate placeholder sparkline data
 * @param length - Number of data points
 * @param seedKey - Seed key for consistent randomization
 * @returns Array of numbers
 */
export function generateSeries(length: number, seedKey: string): number[] {
  // Simple seeded random generator
  const seed = seedKey.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  let random = seed;

  const seededRandom = () => {
    random = (random * 9301 + 49297) % 233280;
    return random / 233280;
  };

  const series: number[] = [];
  let base = 50;

  for (let i = 0; i < length; i++) {
    const variance = (seededRandom() - 0.5) * 30;
    base = Math.max(10, Math.min(90, base + variance));
    series.push(Math.round(base));
  }

  return series;
}
