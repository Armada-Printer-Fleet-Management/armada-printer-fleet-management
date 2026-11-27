import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  ListUsersRequestSchema,
  ListUsersResponseSchema,
} from '../gen/server/v1/user_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    user: {
      list_users(request: JsonValue): Promise<JsonValue>;
    };
  }
}

export async function listUsers(
  request: MessageInitShape<typeof ListUsersRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.user.list_users(
    toJson(ListUsersRequestSchema, create(ListUsersRequestSchema, request)),
  );
  return fromJson(ListUsersResponseSchema, raw);
}
