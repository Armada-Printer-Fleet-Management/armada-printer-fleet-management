import { createClient, type Interceptor } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import { PrintJobService } from './gen/server/v1/print_job_service_pb';
import { createPrintJobApi } from './print-job';

// Called before every request, so a token renewed in the background is picked up.
export type AccessToken = () => Promise<string | undefined>;

const noAccessToken: AccessToken = () => Promise.resolve(undefined);

function bearer(accessToken: AccessToken): Interceptor {
  return (next) => async (req) => {
    const token = await accessToken();
    if (token) {
      req.header.set('Authorization', `Bearer ${token}`);
    }
    return next(req);
  };
}

// The file upload is a plain fetch to a server endpoint, so the interceptor does not reach it.
function fetchWithBearer(
  requestFetch: typeof globalThis.fetch,
  accessToken: AccessToken,
): typeof globalThis.fetch {
  return async (input, init) => {
    const token = await accessToken();
    if (!token) {
      return requestFetch(input, init);
    }
    const headers = new Headers(init?.headers);
    headers.set('Authorization', `Bearer ${token}`);
    return requestFetch(input, { ...init, headers });
  };
}

export interface ApiClientOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
  accessToken?: AccessToken;
}

export function createApiClient(options: ApiClientOptions = {}) {
  const requestFetch = options.fetch ?? globalThis.fetch;
  const accessToken = options.accessToken ?? noAccessToken;

  const transport = createConnectTransport({
    baseUrl: options.baseUrl ?? '/api',
    fetch: requestFetch,
    interceptors: [bearer(accessToken)],
  });
  const printJobClient = createClient(PrintJobService, transport);

  return {
    printJobs: createPrintJobApi(
      printJobClient,
      fetchWithBearer(requestFetch, accessToken),
    ),
  };
}
