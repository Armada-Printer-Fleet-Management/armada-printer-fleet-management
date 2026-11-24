import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';

import { ThemeSettingsSchema } from '../gen/desktop/v1/theme_settings_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    theme: {
      theme_preference(): Promise<JsonValue>;
      set_theme_preference(request: JsonValue): Promise<JsonValue>;
    };
  }
}

/** The theme this user chose, kept by the backend between launches. */
export async function themePreference() {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.theme.theme_preference();
  return fromJson(ThemeSettingsSchema, raw);
}

export async function setThemePreference(
  request: MessageInitShape<typeof ThemeSettingsSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.theme.set_theme_preference(
    toJson(ThemeSettingsSchema, create(ThemeSettingsSchema, request)),
  );
  return fromJson(ThemeSettingsSchema, raw);
}
