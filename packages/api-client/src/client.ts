import { createClient } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import { createAgreementApi } from './agreement';
import { AgreementService } from './gen/server/v1/agreement_service_pb';
import { PrintJobService } from './gen/server/v1/print_job_service_pb';
import { PrinterService } from './gen/server/v1/printer_service_pb';
import { createPrintJobApi } from './print-job';
import { createPrinterApi } from './printer';

export interface ApiClientOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
}

export function createApiClient(options: ApiClientOptions = {}) {
  const requestFetch = options.fetch ?? globalThis.fetch;
  const transport = createConnectTransport({
    baseUrl: options.baseUrl ?? '/api',
    fetch: requestFetch,
  });
  const printJobClient = createClient(PrintJobService, transport);
  const agreementClient = createClient(AgreementService, transport);
  const printerClient = createClient(PrinterService, transport);

  return {
    printJobs: createPrintJobApi(printJobClient, requestFetch),
    agreements: createAgreementApi(agreementClient),
    printers: createPrinterApi(printerClient),
  };
}
