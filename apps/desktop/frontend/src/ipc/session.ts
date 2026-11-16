import { type JsonValue, fromJson } from '@bufbuild/protobuf';
import { CurrentSessionSchema } from '../gen/desktop/v1/current_session_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    session: {
      sign_in(): Promise<JsonValue>;
      sign_out(): Promise<JsonValue>;
      session(): Promise<JsonValue>;
    };
  }
}

// Resolves once the operator has signed in in their browser. Calling it again while one is
// waiting restarts sign-in, and the earlier call rejects.
export async function signIn() {
  const ipc = await waitForPywebviewIpc();
  return fromJson(CurrentSessionSchema, await ipc.session.sign_in());
}

export async function signOut() {
  const ipc = await waitForPywebviewIpc();
  return fromJson(CurrentSessionSchema, await ipc.session.sign_out());
}

export async function session() {
  const ipc = await waitForPywebviewIpc();
  return fromJson(CurrentSessionSchema, await ipc.session.session());
}
