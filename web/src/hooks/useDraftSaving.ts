import { useEffect, useRef, useCallback } from 'react';
import { logger } from '../utils/logger';

/**
 * Saves form data to localStorage as the user types, and restores it on mount.
 * Clears the draft on successful submit.
 */
export function useDraftSaving<T>(
  key: string,
  data: T,
  setData: (updater: (prev: T) => T) => void,
  options?: { debounceMs?: number }
) {
  const debounceMs = options?.debounceMs ?? 1000;
  const storageKey = `draft:${key}`;
  const hasRestored = useRef(false);

  // Restore draft on mount (once)
  useEffect(() => {
    if (hasRestored.current) return;
    hasRestored.current = true;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved) as Partial<T>;
        setData(prev => ({ ...prev, ...parsed }));
      }
    } catch (err) {
      logger.debug('Draft restore failed — invalid JSON', err);
    }
  }, [storageKey, setData]);

  // Debounced save on data change
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        localStorage.setItem(storageKey, JSON.stringify(data));
      } catch (err) {
        logger.debug('Draft save failed — localStorage unavailable', err);
      }
    }, debounceMs);
    return () => clearTimeout(timer);
  }, [data, storageKey, debounceMs]);

  // Clear draft (call on successful submit)
  const clearDraft = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  return { clearDraft };
}
