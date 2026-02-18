import type { Friend } from '../../types';
import { Edit2, Trash2, Award } from 'lucide-react';

const BELT_STYLES: Record<string, React.CSSProperties> = {
  white: { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', borderColor: 'var(--border)' },
  blue: { backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'rgb(96, 165, 250)', borderColor: 'rgba(59, 130, 246, 0.3)' },
  purple: { backgroundColor: 'rgba(168, 85, 247, 0.15)', color: 'rgb(192, 132, 252)', borderColor: 'rgba(168, 85, 247, 0.3)' },
  brown: { backgroundColor: 'rgba(180, 120, 60, 0.15)', color: 'rgb(200, 150, 80)', borderColor: 'rgba(180, 120, 60, 0.3)' },
  black: { backgroundColor: 'rgba(0, 0, 0, 0.6)', color: '#fff', borderColor: 'rgba(100, 100, 100, 0.5)' },
};

function BeltBadge({ friend }: { friend: Friend }) {
  if (!friend.belt_rank) return null;

  const style = BELT_STYLES[friend.belt_rank];
  const stripes = friend.belt_stripes || 0;

  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border" style={style}>
      {friend.belt_rank.charAt(0).toUpperCase() + friend.belt_rank.slice(1)} Belt
      {stripes > 0 && (
        <span className="flex gap-0.5 ml-1">
          {Array.from({ length: stripes }).map((_, i) => (
            <div key={i} className="w-1 h-3 bg-current opacity-70" />
          ))}
        </span>
      )}
    </span>
  );
}

interface FriendCardProps {
  friend: Friend;
  onEdit: (friend: Friend) => void;
  onDelete: (friendId: number) => void;
}

export default function FriendCard({ friend, onEdit, onDelete }: FriendCardProps) {
  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg text-[var(--text)]">
            {friend.name}
          </h3>
          <p className="text-sm text-[var(--muted)] capitalize">
            {friend.friend_type.replace('-', ' ')}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(friend)}
            className="text-[var(--accent)] hover:opacity-80"
            title="Edit friend"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(friend.id)}
            className="text-[var(--error)] hover:opacity-80"
            title="Delete friend"
            aria-label="Delete friend"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <BeltBadge friend={friend} />

        {friend.instructor_certification && (
          <div className="flex items-center gap-1 text-sm text-[var(--muted)]">
            <Award className="w-4 h-4" />
            <span>{friend.instructor_certification}</span>
          </div>
        )}

        {friend.phone && (
          <p className="text-sm text-[var(--muted)]">
            {'\u{1F4F1}'} {friend.phone}
          </p>
        )}

        {friend.email && (
          <p className="text-sm text-[var(--muted)]">
            {'\u{1F4E7}'} {friend.email}
          </p>
        )}

        {friend.notes && (
          <p className="text-sm text-[var(--muted)] italic">
            {friend.notes}
          </p>
        )}
      </div>
    </div>
  );
}
