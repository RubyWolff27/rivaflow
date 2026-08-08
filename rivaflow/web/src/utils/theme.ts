/** Theme preference (DES-F6): light / dark / system, persisted locally.
 *  index.html sets data-theme pre-paint; this module owns changes after load. */

export type ThemePref = 'light' | 'dark' | 'system';

const KEY = 'rf-theme';
// jsdom (tests) has no matchMedia — degrade to light without it.
const media: MediaQueryList | null =
  typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

function resolve(pref: ThemePref): 'light' | 'dark' {
  if (pref === 'system') return media?.matches ? 'dark' : 'light';
  return pref;
}

function apply(pref: ThemePref): void {
  document.documentElement.setAttribute('data-theme', resolve(pref));
}

export function getThemePref(): ThemePref {
  const stored = localStorage.getItem(KEY);
  return stored === 'light' || stored === 'dark' ? stored : 'system';
}

export function setThemePref(pref: ThemePref): void {
  localStorage.setItem(KEY, pref);
  apply(pref);
}

// Follow OS changes while in system mode.
media?.addEventListener('change', () => {
  if (getThemePref() === 'system') apply('system');
});
