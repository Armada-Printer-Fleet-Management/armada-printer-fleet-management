import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  ListPrinterQueuesRequestSchema,
  ListPrinterQueuesResponseSchema,
} from '../gen/server/v1/printer_queue_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    printer_queue: {
      list_printer_queues(request: JsonValue): Promise<JsonValue>;
    };
  }
}

export async function listPrinterQueues(
  request: MessageInitShape<typeof ListPrinterQueuesRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.printer_queue.list_printer_queues(
    toJson(
      ListPrinterQueuesRequestSchema,
      create(ListPrinterQueuesRequestSchema, request),
    ),
  );
  return fromJson(ListPrinterQueuesResponseSchema, raw);
}
