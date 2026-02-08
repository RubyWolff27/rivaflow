interface Technique {
  id: number;
  name: string;
  category: string;
  submissions: number;
  training_count: number;
  quadrant: string;
}

interface TechniqueQuadrantProps {
  techniques: Technique[];
  gameBreadth: number;
  moneyMoves: Technique[];
  insight: string;
}

export default function TechniqueQuadrant({ techniques, gameBreadth, moneyMoves, insight }: TechniqueQuadrantProps) {
  if (!techniques || techniques.length === 0) {
    return (
      <p className="text-sm py-4" style={{ color: 'var(--muted)' }}>
        Not enough technique data yet.
      </p>
    );
  }

  const quadrantColors: Record<string, { bg: string; text: string; label: string }> = {
    money_move: { bg: 'rgba(34, 197, 94, 0.15)', text: '#22C55E', label: 'Money Moves' },
    developing: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3B82F6', label: 'Developing' },
    natural: { bg: 'rgba(234, 179, 8, 0.15)', text: '#EAB308', label: 'Natural Talent' },
    untested: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9CA3AF', label: 'Untested' },
  };

  const grouped = techniques.reduce<Record<string, Technique[]>>((acc, t) => {
    if (!acc[t.quadrant]) acc[t.quadrant] = [];
    acc[t.quadrant].push(t);
    return acc;
  }, {});

  return (
    <div>
      {/* Game Breadth Score */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>Game Breadth</span>
        <div className="flex-1 rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{ width: `${gameBreadth}%`, backgroundColor: 'var(--accent)' }}
          />
        </div>
        <span className="text-sm font-semibold" style={{ color: 'var(--accent)' }}>{gameBreadth}/100</span>
      </div>

      {/* 2x2 Quadrant Grid */}
      <div className="grid grid-cols-2 gap-3">
        {['money_move', 'natural', 'developing', 'untested'].map(q => {
          const config = quadrantColors[q];
          const items = grouped[q] || [];
          return (
            <div
              key={q}
              className="p-3 rounded-[14px]"
              style={{ backgroundColor: config.bg, border: '1px solid var(--border)' }}
            >
              <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: config.text }}>
                {config.label} ({items.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {items.slice(0, 5).map(t => (
                  <span
                    key={t.id}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
                    title={`Subs: ${t.submissions}, Trained: ${t.training_count}x`}
                  >
                    {t.name}
                  </span>
                ))}
                {items.length > 5 && (
                  <span className="text-xs px-2 py-0.5" style={{ color: 'var(--muted)' }}>
                    +{items.length - 5} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Money Moves Highlight */}
      {moneyMoves && moneyMoves.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Money Moves:</span>
          {moneyMoves.map(m => (
            <span
              key={m.id}
              className="text-xs px-2 py-1 rounded-full font-medium"
              style={{ backgroundColor: 'rgba(34, 197, 94, 0.2)', color: '#22C55E' }}
            >
              {m.name} ({m.submissions} subs)
            </span>
          ))}
        </div>
      )}

      <p className="text-sm mt-3" style={{ color: 'var(--muted)' }}>{insight}</p>
    </div>
  );
}
