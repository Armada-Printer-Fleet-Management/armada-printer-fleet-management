import * as React from 'react';

/** What a person chose: follow the operating system, or always light (Frost) or dark (Graphite). */
export type ThemePreference = 'system' | 'light' | 'dark';
/** The theme actually shown. */
export type Theme = 'light' | 'dark';

export const themePreferences: readonly ThemePreference[] = [
  'system',
  'light',
  'dark',
];

export function isThemePreference(value: unknown): value is ThemePreference {
  return themePreferences.some((preference) => preference === value);
}

const darkQuery = '(prefers-color-scheme: dark)';

function systemTheme(): Theme {
  return window.matchMedia(darkQuery).matches ? 'dark' : 'light';
}

interface ThemeContextValue {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
  theme: Theme;
}

const ThemeContext = React.createContext<ThemeContextValue | null>(null);

export interface ThemeProviderProps {
  /** The stored choice, read by the app before rendering so the first paint is already right. */
  initialPreference: ThemePreference;
  /** Called after each change so the app can store it its own way. */
  onPreferenceChange?: (preference: ThemePreference) => void;
  children?: React.ReactNode;
}

/**
 * Sets data-theme on <html>, which switches every colour token. With "system" it follows the
 * operating system, including changes made while the app is open.
 */
export function ThemeProvider({
  initialPreference,
  onPreferenceChange,
  children,
}: ThemeProviderProps) {
  const [preference, setPreferenceState] = React.useState(initialPreference);
  const [system, setSystem] = React.useState(systemTheme);

  React.useEffect(() => {
    const query = window.matchMedia(darkQuery);
    const update = () => setSystem(query.matches ? 'dark' : 'light');
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  const theme = preference === 'system' ? system : preference;

  // Before paint, so a change never shows a frame of the old theme.
  React.useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const setPreference = React.useCallback(
    (next: ThemePreference) => {
      setPreferenceState(next);
      onPreferenceChange?.(next);
    },
    [onPreferenceChange],
  );

  const value = React.useMemo(
    () => ({ preference, setPreference, theme }),
    [preference, setPreference, theme],
  );
  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = React.useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used inside a ThemeProvider');
  return context;
}
