import type { Client } from '@connectrpc/connect';
import { PrinterService } from './gen/server/v1/printer_service_pb';

type PrinterRpcClient = Pick<Client<typeof PrinterService>, 'listPrinterTypes'>;

/** The kinds of printer a student can slice for. Students never see individual printers. */
export function createPrinterApi(client: PrinterRpcClient) {
  return {
    listPrinterTypes: () => client.listPrinterTypes({}),
  };
}
