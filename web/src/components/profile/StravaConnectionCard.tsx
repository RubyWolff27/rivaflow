import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, RefreshCw, Unlink, History } from 'lucide-react';
import { getErrorMessage } from '../../api/client';
import { stravaApi } from '../../api/integrations';
import { useToast } from '../../contexts/ToastContext';
import { logger } from '../../utils/logger';
import type { StravaConnectionStatus, StravaSyncResult } from '../../types';

/**
 * Connect/sync/backfill card for Strava.
 *
 * Self-contained on purpose: it owns its own status state rather than threading
 * more props through useProfileData, so adding it does not touch the WHOOP flow.
 *
 * The backfill control is the point of this card. Sessions stopped when the
 * Garmin push job died, and a plain "sync last 30 days" cannot reach back far
 * enough to repair a historical gap — hence an explicit date range.
 */

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function summarise(result: StravaSyncResult): string {
  const parts = [`${result.fetched} found`];
  if (result.sessions_created) parts.push(`${result.sessions_created} sessions created`);
  if (result.created) parts.push(`${result.created} new`);
  if (result.skipped) parts.push(`${result.skipped} skipped`);
  return parts.join(' · ');
}

export default function StravaConnectionCard() {
  const toast = useToast();
  const [status, setStatus] = useState<StravaConnectionStatus | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [showBackfill, setShowBackfill] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState(todayISO());

  const refreshStatus = useCallback(async () => {
    try {
      const res = await stravaApi.getStatus();
      setStatus(res.data);
    } catch (error) {
      logger.debug('Strava status fetch failed', error);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  // The OAuth callback bounces back to /profile?strava=connected|error.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const flag = params.get('strava');
    if (!flag) return;
    if (flag === 'connected') {
      toast.success('Strava connected');
      refreshStatus();
    } else {
      toast.error('Strava connection failed — please try again');
    }
    window.history.replaceState({}, '', window.location.pathname);
  }, [refreshStatus]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const res = await stravaApi.getAuthorizeUrl();
      window.location.href = res.data.authorization_url;
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
      setConnecting(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await stravaApi.sync(30);
      toast.success(`Strava synced — ${summarise(res.data)}`);
      if (res.data.warning) toast.warning(res.data.warning);
      await refreshStatus();
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setSyncing(false);
    }
  };

  const handleBackfill = async () => {
    if (!startDate || !endDate) {
      toast.error('Pick a start and end date');
      return;
    }
    if (startDate > endDate) {
      toast.error('Start date must be before end date');
      return;
    }
    setBackfilling(true);
    try {
      const res = await stravaApi.backfill(startDate, endDate, true);
      toast.success(`Backfill complete — ${summarise(res.data)}`);
      if (res.data.warning) toast.warning(res.data.warning);
      await refreshStatus();
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setBackfilling(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await stravaApi.disconnect();
      toast.success('Strava disconnected');
      await refreshStatus();
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleToggleAutoCreate = async (enabled: boolean) => {
    try {
      await stravaApi.setAutoCreate(enabled);
      setStatus((s) => (s ? { ...s, auto_create_sessions: enabled } : s));
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    }
  };

  if (!status) return null;

  if (!status.configured) {
    return (
      <div className="p-4 rounded-lg mt-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Strava is not configured on this server. Set STRAVA_CLIENT_ID and
          STRAVA_CLIENT_SECRET to enable it.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg mt-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center"
            style={{ backgroundColor: '#FC4C02' }}
          >
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <div>
            <p className="font-semibold">Strava</p>
            {status.connected ? (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Connected
                {status.last_synced_at
                  ? ` · synced ${new Date(status.last_synced_at).toLocaleDateString()}`
                  : ''}
              </p>
            ) : (
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Not connected — connects Wahoo and any tracker that uploads to Strava
              </p>
            )}
          </div>
        </div>

        {status.connected ? (
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleSync}
              disabled={syncing}
              className="btn-secondary flex items-center gap-1.5 text-sm"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing…' : 'Sync'}
            </button>
            <button
              onClick={() => setShowBackfill((v) => !v)}
              className="btn-secondary flex items-center gap-1.5 text-sm"
            >
              <History className="w-3.5 h-3.5" />
              Backfill
            </button>
            <button
              onClick={handleDisconnect}
              className="text-sm hover:opacity-80 flex items-center gap-1"
              style={{ color: 'var(--error)' }}
            >
              <Unlink className="w-3.5 h-3.5" />
              Disconnect
            </button>
          </div>
        ) : (
          <button onClick={handleConnect} disabled={connecting} className="btn-primary text-sm">
            {connecting ? 'Connecting…' : 'Connect Strava'}
          </button>
        )}
      </div>

      {status.connected && !status.has_private_scope && (
        <div className="mt-3 flex items-start gap-2 text-sm" style={{ color: 'var(--warning, #b45309)' }}>
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            Connected without permission to read private activities, so anything marked
            private on Strava will not import. Disconnect and reconnect, allowing
            &ldquo;View data about your private activities&rdquo;.
          </span>
        </div>
      )}

      {status.connected && (
        <label className="mt-3 flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={status.auto_create_sessions}
            onChange={(e) => handleToggleAutoCreate(e.target.checked)}
          />
          <span>
            Create sessions automatically
            <span style={{ color: 'var(--muted)' }}> — flagged for review so you can confirm the details</span>
          </span>
        </label>
      )}

      {status.connected && showBackfill && (
        <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
          <p className="text-sm mb-2" style={{ color: 'var(--muted)' }}>
            Pull a specific date range — use this to fill a gap. Safe to re-run: it
            updates what is already there instead of duplicating.
          </p>
          <div className="flex items-end gap-2 flex-wrap">
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>From</label>
              <input
                type="date"
                value={startDate}
                max={endDate || todayISO()}
                onChange={(e) => setStartDate(e.target.value)}
                className="input text-sm"
              />
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ color: 'var(--muted)' }}>To</label>
              <input
                type="date"
                value={endDate}
                max={todayISO()}
                onChange={(e) => setEndDate(e.target.value)}
                className="input text-sm"
              />
            </div>
            <button
              onClick={handleBackfill}
              disabled={backfilling}
              className="btn-primary text-sm"
            >
              {backfilling ? 'Backfilling…' : 'Run backfill'}
            </button>
          </div>
        </div>
      )}

      {status.connected && status.cached_activities > 0 && (
        <p className="mt-3 text-xs" style={{ color: 'var(--muted)' }}>
          {status.cached_activities} activities cached from Strava.
        </p>
      )}
    </div>
  );
}
