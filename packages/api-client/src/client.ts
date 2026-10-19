import { createClient } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import { PrintJobService } from './gen/server/v1/print_job_service_pb';
import { createPrintJobApi } from './print-job';

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

  return {
    printJobs: createPrintJobApi(printJobClient, requestFetch),
  };
}
