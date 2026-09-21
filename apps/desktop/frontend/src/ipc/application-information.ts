import { type JsonValue, fromJson } from "@bufbuild/protobuf";
import { VersionInfoSchema } from "../gen/common/v1/application_information_pb";
import { waitForPywebviewIpc } from "./pywebview";

declare global {
  interface PywebviewIpc {
    application_information: {
      version(): Promise<JsonValue>;
    };
  }
}

export async function version() {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.application_information.version();
  return fromJson(VersionInfoSchema, raw);
}