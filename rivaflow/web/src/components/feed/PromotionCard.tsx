import { Trophy, Share2 } from 'lucide-react';

const BELT_COLORS: Record<string, { from: string; to: string; text: string }> = {
  white: { from: '#E5E7EB', to: '#9CA3AF', text: '#1F2937' },
  blue: { from: '#1E40AF', to: '#3B82F6', text: '#FFFFFF' },
  purple: { from: '#6B21A8', to: '#A855F7', text: '#FFFFFF' },
  brown: { from: '#78350F', to: '#A16207', text: '#FFFFFF' },
  black: { from: '#1F2937', to: '#374151', text: '#FFFFFF' },
};

function getBeltKey(grade: string): string {
  const lower = grade.toLowerCase();
  for (const key of Object.keys(BELT_COLORS)) {
    if (lower.includes(key)) return key;
  }
  return 'blue';
}

function formatBeltName(grade: string): string {
  return grade
    .split(/[\s_-]+/)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

interface PromotionCardProps {
  grade: string;
  date: string;
  professor?: string;
  sessionsSinceLastPromotion?: number;
  hoursSinceLastPromotion?: number;
  rollsSinceLastPromotion?: number;
}

export default function PromotionCard({
  grade,
  date,
  professor,
  sessionsSinceLastPromotion,
  hoursSinceLastPromotion,
  rollsSinceLastPromotion,
}: PromotionCardProps) {
  const beltKey = getBeltKey(grade);
  const colors = BELT_COLORS[beltKey] || BELT_COLORS.blue;

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Belt Promotion!',
          text: `I just got promoted to ${formatBeltName(grade)}!`,
        });
      } catch {
        // User cancelled or share failed
      }
    }
  };

  const formattedDate = new Date(date).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  const stats = [
    sessionsSinceLastPromotion != null && { value: sessionsSinceLastPromotion, label: 'Sessions' },
    hoursSinceLastPromotion != null && { value: Math.round(hoursSinceLastPromotion), label: 'Hours' },
    rollsSinceLastPromotion != null && { value: rollsSinceLastPromotion, label: 'Rolls' },
  ].filter(Boolean) as { value: number; label: string }[];

  return (
    <div
      className="rounded-xl p-5 text-center"
      style={{
        background: `linear-gradient(135deg, ${colors.from}, ${colors.to})`,
        color: colors.text,
      }}
    >
      <Trophy className="w-10 h-10 mx-auto mb-2" style={{ color: colors.text, opacity: 0.9 }} />

      <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ opacity: 0.8 }}>
        Belt Promotion!
      </p>

      <h3 className="text-2xl font-black mb-1">
        {formatBeltName(grade)}
      </h3>

      <p className="text-sm mb-3" style={{ opacity: 0.75 }}>
        {formattedDate}
      </p>

      {professor && (
        <p className="text-sm mb-3" style={{ opacity: 0.8 }}>
          Promoted by {professor}
        </p>
      )}

      {stats.length > 0 && (
        <div className="flex items-center justify-center gap-6 mb-3">
          {stats.map((stat, i) => (
            <div key={i}>
              <p className="text-lg font-bold tabular-nums leading-tight">
                {stat.value.toLocaleString()}
              </p>
              <p className="text-[10px] uppercase tracking-wider" style={{ opacity: 0.7 }}>
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      )}

      {stats.length > 0 && (
        <p className="text-xs mb-3" style={{ opacity: 0.6 }}>
          Since last promotion
        </p>
      )}

      {typeof navigator !== 'undefined' && typeof navigator.share === 'function' && (
        <button
          onClick={handleShare}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-opacity hover:opacity-80"
          style={{
            backgroundColor: 'rgba(255,255,255,0.2)',
            color: colors.text,
          }}
        >
          <Share2 className="w-3.5 h-3.5" />
          Share
        </button>
      )}
    </div>
  );
}
