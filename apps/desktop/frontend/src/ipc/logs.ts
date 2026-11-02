import { type JsonValue, fromJson } from '@bufbuild/protobuf';
import { EmptySchema } from '@bufbuild/protobuf/wkt';
import { LogExportSchema } from '../gen/common/v1/log_export_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    logs: {
      write_test_log(): Promise<JsonValue>;
      export_logs(): Promise<JsonValue>;
    };
  }
}

export async function writeTestLog() {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.logs.write_test_log();
  return fromJson(EmptySchema, raw);
}

export async function exportLogs() {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.logs.export_logs();
  return fromJson(LogExportSchema, raw);
}
