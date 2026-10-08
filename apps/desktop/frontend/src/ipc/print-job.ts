import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  GetPrintJobRequestSchema,
  GetPrintJobResponseSchema,
} from '../gen/server/v1/print_job_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    print_job: {
      print_job(request: JsonValue): Promise<JsonValue>;
    };
  }
}

export async function printJob(
  request: MessageInitShape<typeof GetPrintJobRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.print_job.print_job(
    toJson(GetPrintJobRequestSchema, create(GetPrintJobRequestSchema, request)),
  );
  return fromJson(GetPrintJobResponseSchema, raw);
}
