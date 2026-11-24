import { isThemePreference, type ThemePreference } from '@armada/ui-kit';

// index.html reads the same key before the app loads, so the first paint is in the right theme.
const KEY = 'armada.theme-preference';

/** This browser's stored choice, or "system" when there is none or storage is unavailable. */
export function themePreference(): ThemePreference {
  try {
    const stored = window.localStorage.getItem(KEY);
    return isThemePreference(stored) ? stored : 'system';
  } catch {
    return 'system';
  }
}

export function setThemePreference(preference: ThemePreference) {
  try {
    window.localStorage.setItem(KEY, preference);
  } catch {
    // Storage blocked, such as in a private window: the choice lasts until the tab closes.
  }
}
