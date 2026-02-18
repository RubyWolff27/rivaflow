import type { Group } from '../../types';
import { Users, Shield, ChevronRight } from 'lucide-react';

const GROUP_TYPE_LABELS: Record<string, string> = {
  training_crew: 'Training Crew',
  comp_team: 'Comp Team',
  study_group: 'Study Group',
  gym_class: 'Gym Class',
};

const GROUP_TYPE_COLORS: Record<string, string> = {
  training_crew: 'var(--accent)',
  comp_team: '#3B82F6',
  study_group: '#8B5CF6',
  gym_class: '#10B981',
};

interface GroupCardProps {
  group: Group;
  onClick: () => void;
}

export default function GroupCard({ group, onClick }: GroupCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-[14px] p-5 transition-colors"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-sm truncate" style={{ color: 'var(--text)' }}>
              {group.name}
            </h3>
            <span
              className="px-2 py-0.5 rounded-full text-[10px] font-semibold shrink-0"
              style={{
                backgroundColor: `${GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)'}20`,
                color: GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)',
              }}
            >
              {GROUP_TYPE_LABELS[group.group_type] || group.group_type}
            </span>
          </div>
          {group.description && (
            <p className="text-xs mb-2 line-clamp-1" style={{ color: 'var(--muted)' }}>
              {group.description}
            </p>
          )}
          <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
            <span className="flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {group.member_count || 0} member{(group.member_count || 0) !== 1 ? 's' : ''}
            </span>
            {group.member_role === 'admin' && (
              <span className="flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                <Shield className="w-3 h-3" />
                Admin
              </span>
            )}
          </div>
        </div>
        <ChevronRight className="w-5 h-5 shrink-0 mt-1" style={{ color: 'var(--muted)' }} />
      </div>
    </button>
  );
}

interface DiscoverGroupCardProps {
  group: Group;
  onJoin: () => void;
}

export function DiscoverGroupCard({ group, onJoin }: DiscoverGroupCardProps) {
  return (
    <div
      className="rounded-[14px] p-5 flex items-start justify-between"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="font-semibold text-sm truncate" style={{ color: 'var(--text)' }}>
            {group.name}
          </h3>
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-semibold shrink-0"
            style={{
              backgroundColor: `${GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)'}20`,
              color: GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)',
            }}
          >
            {GROUP_TYPE_LABELS[group.group_type] || group.group_type}
          </span>
        </div>
        {group.description && (
          <p className="text-xs mb-2 line-clamp-2" style={{ color: 'var(--muted)' }}>
            {group.description}
          </p>
        )}
        <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {group.member_count || 0} member{(group.member_count || 0) !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
      <button
        onClick={onJoin}
        className="shrink-0 ml-3 px-4 py-2 rounded-lg text-sm font-medium"
        style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
      >
        Join
      </button>
    </div>
  );
}

export { GROUP_TYPE_LABELS, GROUP_TYPE_COLORS };
