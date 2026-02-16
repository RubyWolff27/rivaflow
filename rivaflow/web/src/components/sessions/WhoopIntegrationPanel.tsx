import { CheckCircle, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

interface WhoopData {
  whoop_strain: string;
  whoop_calories: string;
  whoop_avg_hr: string;
  whoop_max_hr: string;
}

interface WhoopIntegrationPanelProps {
  whoopConnected: boolean;
  whoopSyncing: boolean;
  whoopSynced: boolean;
  whoopManualMode: boolean;
  showWhoop: boolean;
  classTime: string;
  whoopData: WhoopData;
  onWhoopDataChange: (field: string, value: string) => void;
  onSync: () => void;
  onClear: () => void;
  onToggleManualMode: (manual: boolean) => void;
  onToggleShow: () => void;
}

export default function WhoopIntegrationPanel({
  whoopConnected,
  whoopSyncing,
  whoopSynced,
  whoopManualMode,
  showWhoop,
  classTime,
  whoopData,
  onWhoopDataChange,
  onSync,
  onClear,
  onToggleManualMode,
  onToggleShow,
}: WhoopIntegrationPanelProps) {
  return (
    <div>
      {whoopConnected && !whoopManualMode ? (
        <>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-lg">WHOOP Stats</h3>
            <button
              type="button"
              onClick={() => { onToggleManualMode(true); onToggleShow(); }}
              className="text-xs text-[var(--accent)] hover:opacity-80"
            >
              Enter manually
            </button>
          </div>

          {whoopSynced ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: 'var(--success)' }}>
                  <CheckCircle className="w-3 h-3" /> Synced from WHOOP
                </span>
                <button type="button" onClick={onClear} className="text-xs text-[var(--muted)] hover:opacity-80 underline">
                  Clear
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {whoopData.whoop_strain && (
                  <div className="p-2 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)]">Strain</p>
                    <p className="text-lg font-bold">{whoopData.whoop_strain}</p>
                  </div>
                )}
                {whoopData.whoop_calories && (
                  <div className="p-2 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)]">Calories</p>
                    <p className="text-lg font-bold">{whoopData.whoop_calories}</p>
                  </div>
                )}
                {whoopData.whoop_avg_hr && (
                  <div className="p-2 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)]">Avg HR</p>
                    <p className="text-lg font-bold">{whoopData.whoop_avg_hr}</p>
                  </div>
                )}
                {whoopData.whoop_max_hr && (
                  <div className="p-2 bg-[var(--surfaceElev)] rounded-lg text-center">
                    <p className="text-xs text-[var(--muted)]">Max HR</p>
                    <p className="text-lg font-bold">{whoopData.whoop_max_hr}</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>
              {classTime ? (
                <button
                  type="button"
                  onClick={onSync}
                  disabled={whoopSyncing}
                  className="w-full py-3 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2"
                  style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
                >
                  <RefreshCw className={`w-4 h-4 ${whoopSyncing ? 'animate-spin' : ''}`} />
                  {whoopSyncing ? 'Syncing from WHOOP...' : 'Sync from WHOOP'}
                </button>
              ) : (
                <div className="text-center py-3 text-sm text-[var(--muted)]">
                  Add a class time above to sync from WHOOP
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <>
          <button
            type="button"
            onClick={onToggleShow}
            className="flex items-center justify-between w-full text-left"
          >
            <h3 className="font-semibold text-lg">Whoop Stats <span className="text-sm font-normal" style={{ color: 'var(--muted)' }}>optional</span></h3>
            {showWhoop ? <ChevronUp className="w-5 h-5" style={{ color: 'var(--muted)' }} /> : <ChevronDown className="w-5 h-5" style={{ color: 'var(--muted)' }} />}
          </button>
          {showWhoop && (
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <label className="label">Activity Strain</label>
                <input
                  type="number"
                  inputMode="decimal"
                  className="input"
                  value={whoopData.whoop_strain}
                  onChange={(e) => onWhoopDataChange('whoop_strain', e.target.value)}
                  placeholder="0-21"
                  min="0"
                  max="21"
                  step="0.1"
                />
              </div>
              <div>
                <label className="label">Calories</label>
                <input
                  type="number"
                  className="input"
                  value={whoopData.whoop_calories}
                  onChange={(e) => onWhoopDataChange('whoop_calories', e.target.value)}
                  placeholder="e.g., 500"
                  min="0"
                />
              </div>
              <div>
                <label className="label">Avg HR (bpm)</label>
                <input
                  type="number"
                  className="input"
                  value={whoopData.whoop_avg_hr}
                  onChange={(e) => onWhoopDataChange('whoop_avg_hr', e.target.value)}
                  placeholder="e.g., 140"
                  min="0"
                  max="250"
                />
              </div>
              <div>
                <label className="label">Max HR (bpm)</label>
                <input
                  type="number"
                  className="input"
                  value={whoopData.whoop_max_hr}
                  onChange={(e) => onWhoopDataChange('whoop_max_hr', e.target.value)}
                  placeholder="e.g., 185"
                  min="0"
                  max="250"
                />
              </div>
            </div>
          )}
          {whoopConnected && whoopManualMode && (
            <button
              type="button"
              onClick={() => onToggleManualMode(false)}
              className="text-xs text-[var(--accent)] hover:opacity-80 mt-2"
            >
              Switch to WHOOP sync
            </button>
          )}
        </>
      )}
    </div>
  );
}
