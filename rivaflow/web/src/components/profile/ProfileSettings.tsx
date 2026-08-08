import { useState, useEffect } from 'react';
import { Settings, Eye, EyeOff, Sun, Moon, Monitor } from 'lucide-react';
import { Link } from 'react-router-dom';
import { profileApi } from '../../api/client';
import { getThemePref, setThemePref } from '../../utils/theme';
import type { ThemePref } from '../../utils/theme';
import { logger } from '../../utils/logger';

export default function ProfileSettings() {
  const [themePref, setThemePrefState] = useState<ThemePref>(getThemePref());

  const changeTheme = (pref: ThemePref) => {
    setThemePref(pref);
    setThemePrefState(pref);
  };

  const [partnerStatsPublic, setPartnerStatsPublic] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await profileApi.get();
        if (!cancelled) {
          const data = res.data as unknown as Record<string, unknown>;
          const privacy = data?.privacy_settings as Record<string, unknown> | undefined;
          if (privacy) {
            setPartnerStatsPublic(privacy.partner_stats_public !== false);
          }
        }
      } catch {
        // Default to public if settings not available
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const togglePartnerStats = async () => {
    const newValue = !partnerStatsPublic;
    setPartnerStatsPublic(newValue);
    setSaving(true);
    try {
      await profileApi.update({
        privacy_settings: { partner_stats_public: newValue },
      } as Record<string, unknown>);
    } catch (err) {
      logger.error('Failed to save privacy setting', err);
      setPartnerStatsPublic(!newValue); // revert
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Appearance (DES-F6) */}
      <div className="card">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-lg font-semibold">Appearance</h2>
            <p className="text-sm text-[var(--muted)]">Light, dark, or follow your device</p>
          </div>
          <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }} role="group" aria-label="Theme">
            {([
              { key: 'light', label: 'Light', icon: Sun },
              { key: 'dark', label: 'Dark', icon: Moon },
              { key: 'system', label: 'Auto', icon: Monitor },
            ] as const).map(({ key, label, icon: ThemeIcon }) => (
              <button
                key={key}
                type="button"
                onClick={() => changeTheme(key)}
                aria-pressed={themePref === key}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors"
                style={{
                  backgroundColor: themePref === key ? 'var(--accent)' : 'var(--surface)',
                  color: themePref === key ? '#FFFFFF' : 'var(--muted)',
                }}
              >
                <ThemeIcon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <Link to="/coach-settings" className="card block hover:border-[var(--accent)] transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-[var(--accent)]" />
            <div>
              <h2 className="text-lg font-semibold">Grapple AI Coach Settings</h2>
              <p className="text-sm text-[var(--muted)]">
                Personalize how Grapple coaches you — training mode, style, injuries, and more
              </p>
            </div>
          </div>
          <span className="text-[var(--muted)]">&rarr;</span>
        </div>
      </Link>

      {/* Privacy Controls */}
      <div className="card">
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
          Privacy
        </h3>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {partnerStatsPublic ? (
              <Eye className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            ) : (
              <EyeOff className="w-5 h-5" style={{ color: 'var(--muted)' }} />
            )}
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                Partner Stats Visibility
              </p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                {partnerStatsPublic ? 'Friends can see your partner stats' : 'Partner stats hidden from friends'}
              </p>
            </div>
          </div>
          <button
            onClick={togglePartnerStats}
            disabled={saving}
            className="relative w-11 h-6 rounded-full transition-colors"
            style={{
              backgroundColor: partnerStatsPublic ? 'var(--accent)' : 'var(--surfaceElev)',
            }}
            aria-label="Toggle partner stats visibility"
          >
            <div
              className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform"
              style={{
                transform: partnerStatsPublic ? 'translateX(22px)' : 'translateX(2px)',
              }}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
