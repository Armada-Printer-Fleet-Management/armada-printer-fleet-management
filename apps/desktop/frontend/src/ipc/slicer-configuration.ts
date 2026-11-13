import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  GetSliceSettingsRequestSchema,
  GetSliceSettingsResponseSchema,
} from '../gen/server/v1/slicer_configuration_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    slicer_configuration: {
      get_slice_settings(request: JsonValue): Promise<JsonValue>;
    };
  }
}

/** The engine settings to slice with for a printer type, as the application server decides them. */
export async function getSliceSettings(
  request: MessageInitShape<typeof GetSliceSettingsRequestSchema>,
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.slicer_configuration.get_slice_settings(
    toJson(
      GetSliceSettingsRequestSchema,
      create(GetSliceSettingsRequestSchema, request),
    ),
  );
  return fromJson(GetSliceSettingsResponseSchema, raw);
}
