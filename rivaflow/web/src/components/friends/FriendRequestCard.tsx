import { useNavigate } from 'react-router-dom';
import { UserCheck, X } from 'lucide-react';

interface PendingRequest {
  id: number;
  requester_id: number;
  requester_first_name: string;
  requester_last_name: string;
  requester_email: string;
  requester_avatar_url?: string;
  requested_at: string;
}

interface SocialFriend {
  id: number;
  first_name: string;
  last_name: string;
  email?: string;
  avatar_url?: string;
  friends_since?: string;
}

interface FriendRequestCardProps {
  pendingRequests: PendingRequest[];
  requestActionLoading: number | null;
  onAccept: (request: PendingRequest) => void;
  onDecline: (request: PendingRequest) => void;
}

export default function FriendRequestCard({
  pendingRequests,
  requestActionLoading,
  onAccept,
  onDecline,
}: FriendRequestCardProps) {
  const navigate = useNavigate();

  if (pendingRequests.length === 0) return null;

  return (
    <div className="card bg-[var(--surface)] border border-[var(--accent)]/20">
      <h3 className="text-lg font-semibold text-[var(--text)] mb-3">
        Friend Requests ({pendingRequests.length})
      </h3>
      <div className="space-y-3">
        {pendingRequests.map((request) => (
          <div
            key={request.id}
            className="flex items-center justify-between p-3 rounded-[14px] bg-[var(--surfaceElev)]"
          >
            <div
              className="flex items-center gap-3 cursor-pointer flex-1"
              onClick={() => navigate(`/users/${request.requester_id}`)}
            >
              {request.requester_avatar_url ? (
                <img
                  src={request.requester_avatar_url}
                  alt={request.requester_first_name}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                  style={{ background: 'linear-gradient(135deg, var(--accent), #FF8C42)' }}
                >
                  {request.requester_first_name?.charAt(0) || '?'}
                </div>
              )}
              <div>
                <p className="font-medium text-[var(--text)]">
                  {request.requester_first_name} {request.requester_last_name}
                </p>
                <p className="text-xs text-[var(--muted)]">
                  Sent {new Date(request.requested_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onAccept(request)}
                disabled={requestActionLoading === request.id}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                <UserCheck className="w-4 h-4" />
                Accept
              </button>
              <button
                onClick={() => onDecline(request)}
                disabled={requestActionLoading === request.id}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--muted)] bg-[var(--surface)] hover:opacity-80 disabled:opacity-50 border border-[var(--border)]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface SocialFriendsListProps {
  socialFriends: SocialFriend[];
}

export function SocialFriendsList({ socialFriends }: SocialFriendsListProps) {
  const navigate = useNavigate();

  if (socialFriends.length === 0) return null;

  return (
    <div className="card bg-[var(--surface)]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-[var(--text)]">
          RivaFlow Friends ({socialFriends.length})
        </h3>
        <button
          onClick={() => navigate('/find-friends')}
          className="text-sm text-[var(--accent)] hover:opacity-80"
        >
          Find more
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {socialFriends.map((sf) => (
          <div
            key={sf.id}
            className="flex items-center gap-3 p-3 rounded-[14px] bg-[var(--surfaceElev)] cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/users/${sf.id}`)}
          >
            {sf.avatar_url ? (
              <img
                src={sf.avatar_url}
                alt={sf.first_name}
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                style={{ background: 'linear-gradient(135deg, var(--accent), #FF8C42)' }}
              >
                {sf.first_name?.charAt(0) || '?'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-[var(--text)] truncate">
                {sf.first_name} {sf.last_name}
              </p>
              <p className="text-xs text-[var(--muted)]">
                <UserCheck className="w-3 h-3 inline mr-1" />
                Friends
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export type { PendingRequest, SocialFriend };
