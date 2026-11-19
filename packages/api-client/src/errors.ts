import { Code, ConnectError } from '@connectrpc/connect';

export class PrintJobUploadError extends Error {
  constructor(readonly status: number) {
    super(`Print job file upload failed with HTTP ${status}.`);
    this.name = 'PrintJobUploadError';
  }
}

/** Why a request failed, in the terms a person can act on. */
export type RequestFailure = 'unreachable' | 'signed-out' | 'other';

/** Sorts an error a client call threw, so an app can explain it in its own words. */
export function requestFailure(error: unknown): RequestFailure {
  const { code } = ConnectError.from(error);
  if (code === Code.Unavailable || code === Code.DeadlineExceeded) {
    return 'unreachable';
  }
  if (code === Code.Unauthenticated) return 'signed-out';
  return 'other';
}
