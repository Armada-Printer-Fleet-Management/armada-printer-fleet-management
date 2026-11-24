import { MonitorIcon } from '../icons/monitor-icon';
import { MoonIcon } from '../icons/moon-icon';
import { SunIcon } from '../icons/sun-icon';
import { type ThemePreference, useTheme } from '../theme/theme-provider';
import {
  SegmentedControl,
  type SegmentedControlOption,
} from './segmented-control';

const options: readonly SegmentedControlOption<ThemePreference>[] = [
  { value: 'system', label: 'System', icon: MonitorIcon },
  { value: 'light', label: 'Light', icon: SunIcon },
  { value: 'dark', label: 'Dark', icon: MoonIcon },
];

export interface ThemeSwitcherProps {
  orientation?: 'horizontal' | 'vertical';
  iconOnly?: boolean;
  className?: string;
}

/** System, Light or Dark, as most desktop and web apps offer it. Needs a ThemeProvider above it. */
export function ThemeSwitcher({
  orientation,
  iconOnly,
  className,
}: ThemeSwitcherProps) {
  const { preference, setPreference } = useTheme();
  return (
    <SegmentedControl
      label="Theme"
      name="theme-preference"
      options={options}
      value={preference}
      onValueChange={setPreference}
      orientation={orientation}
      iconOnly={iconOnly}
      className={className}
    />
  );
}
