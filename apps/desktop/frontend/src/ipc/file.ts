import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  ListFilesRequestSchema,
  ListFilesResponseSchema,
} from '../gen/server/v1/file_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    file: {
      list_files(request: JsonValue): Promise<JsonValue>;
    };
  }
}

export async function listFiles(
  request: MessageInitShape<typeof ListFilesRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.file.list_files(
    toJson(ListFilesRequestSchema, create(ListFilesRequestSchema, request)),
  );
  return fromJson(ListFilesResponseSchema, raw);
}
