import { Card } from '../ui';

interface TechniqueEntry {
  name: string;
  category: string;
  count: number;
}

interface TechniqueHeatmapProps {
  techniques: TechniqueEntry[];
}

export default function TechniqueHeatmap({ techniques }: TechniqueHeatmapProps) {
  if (!techniques || techniques.length === 0) return null;

  // Group by category, limit to top 30 techniques
  const sorted = [...techniques].sort((a, b) => b.count - a.count).slice(0, 30);
  const maxCount = sorted[0]?.count ?? 1;

  const categories = new Map<string, TechniqueEntry[]>();
  for (const t of sorted) {
    const cat = t.category || 'Other';
    if (!categories.has(cat)) categories.set(cat, []);
    categories.get(cat)!.push(t);
  }

  const getOpacity = (count: number) => {
    return 0.15 + (count / maxCount) * 0.85;
  };

  return (
    <Card>
      <div className="mb-4">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Technique Heatmap</h3>
        <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Frequency of techniques by category</p>
      </div>

      <div className="space-y-4">
        {Array.from(categories.entries()).map(([category, techs]) => (
          <div key={category}>
            <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>
              {category}
            </p>
            <div className="flex flex-wrap gap-2">
              {techs.map((tech) => (
                <div
                  key={tech.name}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium cursor-default"
                  style={{
                    backgroundColor: `rgba(var(--accent-rgb), ${getOpacity(tech.count)})`,
                    color: tech.count / maxCount > 0.5 ? '#FFFFFF' : 'var(--accent)',
                  }}
                  title={`${tech.name}: ${tech.count} uses`}
                >
                  {tech.name} ({tech.count})
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
