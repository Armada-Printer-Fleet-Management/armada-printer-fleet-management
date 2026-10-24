import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  ListPrintersRequestSchema,
  ListPrintersResponseSchema,
  TransitionPrinterRequestSchema,
  TransitionPrinterResponseSchema,
} from '../gen/server/v1/printer_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    printer: {
      list_printers(request: JsonValue): Promise<JsonValue>;
      transition_printer(request: JsonValue): Promise<JsonValue>;
    };
  }
}

export async function listPrinters(
  request: MessageInitShape<typeof ListPrintersRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.printer.list_printers(
    toJson(
      ListPrintersRequestSchema,
      create(ListPrintersRequestSchema, request),
    ),
  );
  return fromJson(ListPrintersResponseSchema, raw);
}

export async function transitionPrinter(
  request: MessageInitShape<typeof TransitionPrinterRequestSchema> = {},
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.printer.transition_printer(
    toJson(
      TransitionPrinterRequestSchema,
      create(TransitionPrinterRequestSchema, request),
    ),
  );
  return fromJson(TransitionPrinterResponseSchema, raw);
}
