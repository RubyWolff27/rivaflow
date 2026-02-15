import { Link2, CheckCircle, RefreshCw, Unlink, AlertCircle } from 'lucide-react';
import type { WhoopConnectionStatus } from '../../types';

export interface ConnectedDevicesSectionProps {
  whoopStatus: WhoopConnectionStatus;
  whoopLoading: boolean;
  whoopSyncing: boolean;
  whoopNeedsReauth: boolean;
  onConnect: () => void;
  onSync: () => void;
  onSetAutoCreate: (value: boolean) => Promise<void>;
  onSetAutoFillReadiness: (value: boolean) => Promise<void>;
  showDisconnectConfirm: boolean;
  onShowDisconnectConfirm: (show: boolean) => void;
  onDisconnect: () => void;
}

export default function ConnectedDevicesSection({
  whoopStatus,
  whoopLoading,
  whoopSyncing,
  whoopNeedsReauth,
  onConnect,
  onSync,
  onSetAutoCreate,
  onSetAutoFillReadiness,
  onShowDisconnectConfirm,
}: ConnectedDevicesSectionProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <Link2 className="w-6 h-6 text-[var(--accent)]" />
        <h2 className="text-xl font-semibold">Connected Devices</h2>
      </div>

      <div className="p-4 bg-[var(--surfaceElev)] rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center">
              <span className="text-white font-bold text-sm">W</span>
            </div>
            <div>
              <p className="font-semibold">WHOOP</p>
              {whoopStatus.connected ? (
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Connected
                </p>
              ) : (
                <p className="text-sm text-[var(--muted)]">Not connected</p>
              )}
            </div>
          </div>

          {whoopStatus.connected ? (
            <div className="flex items-center gap-2">
              <button
                onClick={onSync}
                disabled={whoopSyncing}
                className="btn-secondary flex items-center gap-1.5 text-sm"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${whoopSyncing ? 'animate-spin' : ''}`} />
                {whoopSyncing ? 'Syncing...' : 'Sync'}
              </button>
              <button
                onClick={() => onShowDisconnectConfirm(true)}
                className="text-sm text-[var(--error)] hover:opacity-80 flex items-center gap-1"
              >
                <Unlink className="w-3.5 h-3.5" />
                Disconnect
              </button>
            </div>
          ) : (
            <button
              onClick={onConnect}
              disabled={whoopLoading}
              className="btn-primary text-sm"
            >
              {whoopLoading ? 'Connecting...' : 'Connect WHOOP'}
            </button>
          )}
        </div>

        {whoopStatus.connected && whoopNeedsReauth && (
          <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                    Additional permissions needed
                  </p>
                  <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                    WHOOP needs recovery &amp; sleep permissions for auto-fill and HRV trends.
                  </p>
                </div>
              </div>
              <button
                onClick={onConnect}
                disabled={whoopLoading}
                className="text-sm font-medium px-3 py-1.5 rounded-lg whitespace-nowrap"
                style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
              >
                {whoopLoading ? 'Redirecting...' : 'Re-authorize'}
              </button>
            </div>
          </div>
        )}

        {whoopStatus.connected && whoopStatus.last_synced_at && (
          <p className="text-xs text-[var(--muted)] mt-2">
            Last synced: {new Date(whoopStatus.last_synced_at).toLocaleString()}
          </p>
        )}

        {whoopStatus.connected && (
          <>
            <div className="mt-3 flex items-center justify-between p-3 rounded-lg bg-[var(--surfaceElev)]">
              <div>
                <p className="font-medium text-sm">Auto-log BJJ sessions</p>
                <p className="text-xs text-[var(--muted)]">
                  Auto-create sessions when WHOOP detects BJJ training
                </p>
              </div>
              <button
                onClick={() => onSetAutoCreate(!whoopStatus.auto_create_sessions)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  whoopStatus.auto_create_sessions ? 'bg-[var(--accent)]' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    whoopStatus.auto_create_sessions ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="mt-3 flex items-center justify-between p-3 rounded-lg bg-[var(--surfaceElev)]">
              <div>
                <p className="font-medium text-sm">Auto-fill daily check-in</p>
                <p className="text-xs text-[var(--muted)]">
                  Pre-fill readiness with WHOOP recovery, HRV, and sleep data
                </p>
              </div>
              <button
                onClick={() => onSetAutoFillReadiness(!whoopStatus.auto_fill_readiness)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  whoopStatus.auto_fill_readiness ? 'bg-[var(--accent)]' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    whoopStatus.auto_fill_readiness ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </>
        )}

        {!whoopStatus.connected && (
          <p className="text-xs text-[var(--muted)] mt-3">
            Connect your WHOOP to auto-sync strain, heart rate, and calorie data to your sessions.
          </p>
        )}
      </div>
    </div>
  );
}
