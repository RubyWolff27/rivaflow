import { Edit2, Trash2, Check, XCircle, MapPin, Globe, ExternalLink, Map, Building2 } from 'lucide-react';
import { Card } from '../ui';

interface Gym {
  id: number;
  name: string;
  city?: string;
  state?: string;
  country: string;
  address?: string;
  website?: string;
  email?: string;
  phone?: string;
  head_coach?: string;
  head_coach_belt?: string;
  google_maps_url?: string;
  verified: boolean;
  added_by_user_id?: number;
  created_at: string;
  updated_at: string;
  first_name?: string;
  last_name?: string;
}

interface GymTableProps {
  gyms: Gym[];
  loading: boolean;
  activeTab: 'all' | 'pending';
  onEdit: (gym: Gym) => void;
  onDelete: (gym: Gym) => void;
  onVerify: (gym: Gym) => void;
  onReject: (gym: Gym) => void;
}

export default function GymTable({ gyms, loading, activeTab, onEdit, onDelete, onVerify, onReject }: GymTableProps) {
  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (gyms.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
            No Gyms Found
          </h3>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {activeTab === 'pending' ? 'No pending gyms to verify' : 'Start by adding a gym'}
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {gyms.map((gym) => (
        <Card key={gym.id}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                  {gym.name}
                </h3>
                {gym.verified && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
                  >
                    Verified
                  </span>
                )}
                {!gym.verified && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{ backgroundColor: 'var(--warning-bg)', color: 'var(--warning)' }}
                  >
                    Pending
                  </span>
                )}
              </div>

              <div className="space-y-1">
                {(gym.city || gym.state || gym.country) && (
                  <div className="flex items-center gap-1 text-sm" style={{ color: 'var(--muted)' }}>
                    <MapPin className="w-4 h-4" />
                    <span>
                      {[gym.city, gym.state, gym.country].filter(Boolean).join(', ')}
                    </span>
                  </div>
                )}

                {gym.website && (
                  <div className="flex items-center gap-1 text-sm" style={{ color: 'var(--muted)' }}>
                    <Globe className="w-4 h-4" />
                    <a
                      href={gym.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline"
                      style={{ color: 'var(--primary)' }}
                    >
                      {gym.website}
                    </a>
                  </div>
                )}

                {gym.google_maps_url && (
                  <div className="flex items-center gap-1 text-sm" style={{ color: 'var(--muted)' }}>
                    <Map className="w-4 h-4" />
                    <a
                      href={gym.google_maps_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline flex items-center gap-1"
                      style={{ color: 'var(--primary)' }}
                    >
                      View on Google Maps
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}

                {gym.head_coach && (
                  <div className="text-sm" style={{ color: 'var(--muted)' }}>
                    Head Coach: {gym.head_coach}
                    {gym.head_coach_belt && (
                      <span className="ml-2 px-2 py-0.5 text-xs rounded-full capitalize" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}>
                        {gym.head_coach_belt} belt
                      </span>
                    )}
                  </div>
                )}

                {gym.first_name && gym.last_name && (
                  <div className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
                    Added by: {gym.first_name} {gym.last_name} ({gym.email})
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              {!gym.verified && (
                <>
                  <button
                    onClick={() => onVerify(gym)}
                    className="p-2 rounded-lg hover:bg-green-500/10 transition-colors"
                    title="Verify gym"
                  >
                    <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                  </button>
                  <button
                    onClick={() => onReject(gym)}
                    className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                    title="Reject gym"
                  >
                    <XCircle className="w-4 h-4" style={{ color: 'var(--danger)' }} />
                  </button>
                </>
              )}
              <button
                onClick={() => onEdit(gym)}
                className="p-2 rounded-lg hover:bg-blue-500/10 transition-colors"
                title="Edit gym"
              >
                <Edit2 className="w-4 h-4" style={{ color: 'var(--primary)' }} />
              </button>
              <button
                onClick={() => onDelete(gym)}
                className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                title="Delete gym"
                aria-label={`Delete ${gym.name}`}
              >
                <Trash2 className="w-4 h-4" style={{ color: 'var(--danger)' }} />
              </button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

export type { Gym };
