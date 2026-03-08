import { useState, useEffect } from 'react';
import { Trophy, Share2, X, Heart, PartyPopper } from 'lucide-react';

const BELT_COLORS: Record<string, { from: string; to: string; text: string; glow: string }> = {
  white: { from: '#E5E7EB', to: '#9CA3AF', text: '#1F2937', glow: 'rgba(229,231,235,0.3)' },
  blue: { from: '#1E40AF', to: '#3B82F6', text: '#FFFFFF', glow: 'rgba(59,130,246,0.3)' },
  purple: { from: '#6B21A8', to: '#A855F7', text: '#FFFFFF', glow: 'rgba(168,85,247,0.3)' },
  brown: { from: '#78350F', to: '#A16207', text: '#FFFFFF', glow: 'rgba(161,98,7,0.3)' },
  black: { from: '#1F2937', to: '#374151', text: '#FFFFFF', glow: 'rgba(55,65,81,0.3)' },
};

function getBeltKey(grade: string): string {
  const lower = grade.toLowerCase();
  for (const key of Object.keys(BELT_COLORS)) {
    if (lower.includes(key)) return key;
  }
  return 'blue';
}

function formatBeltName(grade: string): string {
  return grade.split(/[\s_-]+/).map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
}

interface BeltCelebrationProps {
  isOpen: boolean;
  onClose: () => void;
  grade: string;
  date: string;
  professor?: string;
  sessionsSincePromotion?: number;
  hoursSincePromotion?: number;
  rollsSincePromotion?: number;
  userName?: string;
  onCongratulate?: () => void;
  congratulated?: boolean;
}

export default function BeltCelebration({
  isOpen,
  onClose,
  grade,
  date,
  professor,
  sessionsSincePromotion,
  hoursSincePromotion,
  rollsSincePromotion,
  userName,
  onCongratulate,
  congratulated = false,
}: BeltCelebrationProps) {
  const [showContent, setShowContent] = useState(false);
  const [showStats, setShowStats] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Stagger animations
      const t1 = setTimeout(() => setShowContent(true), 100);
      const t2 = setTimeout(() => setShowStats(true), 600);
      return () => { clearTimeout(t1); clearTimeout(t2); };
    } else {
      setShowContent(false);
      setShowStats(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const beltKey = getBeltKey(grade);
  const colors = BELT_COLORS[beltKey] || BELT_COLORS.blue;
  const beltName = formatBeltName(grade);
  const formattedDate = new Date(date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const stats = [
    sessionsSincePromotion != null && { value: sessionsSincePromotion, label: 'Sessions' },
    hoursSincePromotion != null && { value: Math.round(hoursSincePromotion), label: 'Hours' },
    rollsSincePromotion != null && { value: rollsSincePromotion, label: 'Rolls' },
  ].filter(Boolean) as { value: number; label: string }[];

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Belt Promotion!',
          text: userName
            ? `${userName} just got promoted to ${beltName} in BJJ!`
            : `I just got promoted to ${beltName} in BJJ!`,
        });
      } catch { /* cancelled */ }
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.85)' }}
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 rounded-full z-10"
        style={{ backgroundColor: 'rgba(255,255,255,0.15)', color: '#FFFFFF' }}
        aria-label="Close celebration"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Main card */}
      <div
        className={`w-full max-w-sm rounded-2xl p-8 text-center transition-all duration-700 ${
          showContent ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
        }`}
        style={{
          background: `linear-gradient(160deg, ${colors.from}, ${colors.to})`,
          color: colors.text,
          boxShadow: `0 0 80px ${colors.glow}, 0 0 160px ${colors.glow}`,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Confetti icon */}
        <PartyPopper className="w-12 h-12 mx-auto mb-3" style={{ opacity: 0.85 }} />

        {/* Header */}
        <p className="text-xs font-bold uppercase tracking-[0.25em] mb-2" style={{ opacity: 0.7 }}>
          Belt Promotion
        </p>

        {/* Belt name */}
        <h2 className="text-4xl font-black mb-1">{beltName}</h2>

        {/* User name */}
        {userName && (
          <p className="text-base font-medium mb-2" style={{ opacity: 0.85 }}>
            {userName}
          </p>
        )}

        {/* Date */}
        <p className="text-sm mb-4" style={{ opacity: 0.65 }}>
          {formattedDate}
        </p>

        {/* Professor */}
        {professor && (
          <p className="text-sm mb-4" style={{ opacity: 0.8 }}>
            Promoted by <span className="font-semibold">{professor}</span>
          </p>
        )}

        {/* Journey stats */}
        {stats.length > 0 && (
          <div
            className={`transition-all duration-700 ${
              showStats ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <p className="text-[10px] uppercase tracking-widest mb-3" style={{ opacity: 0.5 }}>
              The Journey
            </p>
            <div className="flex items-center justify-center gap-8 mb-4">
              {stats.map((stat, i) => (
                <div key={i}>
                  <p className="text-2xl font-black tabular-nums leading-tight">
                    {stat.value.toLocaleString()}
                  </p>
                  <p className="text-[10px] uppercase tracking-wider" style={{ opacity: 0.6 }}>
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
            <p className="text-xs" style={{ opacity: 0.45 }}>
              Since last promotion
            </p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center justify-center gap-3 mt-6">
          {onCongratulate && (
            <button
              onClick={onCongratulate}
              disabled={congratulated}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-opacity hover:opacity-80"
              style={{
                backgroundColor: congratulated ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.25)',
                color: colors.text,
              }}
            >
              <Heart className={`w-4 h-4 ${congratulated ? 'fill-current' : ''}`} />
              {congratulated ? 'Congratulated!' : 'Congratulate'}
            </button>
          )}
          {typeof navigator !== 'undefined' && typeof navigator.share === 'function' && (
            <button
              onClick={handleShare}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-opacity hover:opacity-80"
              style={{
                backgroundColor: 'rgba(255,255,255,0.15)',
                color: colors.text,
              }}
            >
              <Share2 className="w-4 h-4" />
              Share
            </button>
          )}
        </div>

        {/* Belt stripe decoration */}
        <div className="mt-6 flex items-center justify-center gap-1">
          <Trophy className="w-3.5 h-3.5" style={{ opacity: 0.4 }} />
          <div className="w-24 h-1 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.2)' }} />
          <Trophy className="w-3.5 h-3.5" style={{ opacity: 0.4 }} />
        </div>
      </div>
    </div>
  );
}
