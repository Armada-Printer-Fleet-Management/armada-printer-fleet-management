import type { MessageInitShape } from '@bufbuild/protobuf';
import type { Client } from '@connectrpc/connect';
import {
  GetSliceSettingsRequestSchema,
  SlicerConfigurationService,
} from './gen/server/v1/slicer_configuration_service_pb';

type SlicerConfigurationRpcClient = Pick<
  Client<typeof SlicerConfigurationService>,
  'getSliceSettings'
>;

/** What a print may be sliced with. The server builds the settings and enforces its profile. */
export function createSlicerConfigurationApi(
  client: SlicerConfigurationRpcClient,
) {
  return {
    getSliceSettings: (
      request: MessageInitShape<typeof GetSliceSettingsRequestSchema>,
    ) => client.getSliceSettings(request),
  };
}
