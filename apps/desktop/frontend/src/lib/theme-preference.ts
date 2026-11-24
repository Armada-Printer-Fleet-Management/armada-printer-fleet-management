import type { ThemePreference } from '@armada/ui-kit';

import { ThemePreference as ThemePreferenceMessage } from '../gen/desktop/v1/theme_settings_pb';
import * as ipc from '../ipc/theme';

const TO_PROTO: Record<ThemePreference, ThemePreferenceMessage> = {
  system: ThemePreferenceMessage.SYSTEM,
  light: ThemePreferenceMessage.LIGHT,
  dark: ThemePreferenceMessage.DARK,
};

function fromProto(preference: ThemePreferenceMessage): ThemePreference {
  if (preference === ThemePreferenceMessage.LIGHT) return 'light';
  if (preference === ThemePreferenceMessage.DARK) return 'dark';
  return 'system';
}

/** The stored choice, or "system" when the backend cannot answer, which only follows the OS. */
export async function themePreference(): Promise<ThemePreference> {
  try {
    return fromProto((await ipc.themePreference()).preference);
  } catch {
    return 'system';
  }
}

export function setThemePreference(preference: ThemePreference) {
  ipc
    .setThemePreference({ preference: TO_PROTO[preference] })
    .catch((error: unknown) => {
      console.error('Could not save the theme choice', error);
    });
}
