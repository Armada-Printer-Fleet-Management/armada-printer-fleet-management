import { Code, ConnectError } from '@connectrpc/connect';
import { describe, expect, it, vi } from 'vitest';
import { createApiClient } from './client';

describe('createApiClient', () => {
  it('uses the generated Connect service at the same-origin API path', async () => {
    const requestFetch = vi.fn<typeof globalThis.fetch>(() =>
      Promise.resolve(
        new Response('{}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    const api = createApiClient({ fetch: requestFetch });

    await api.printJobs.createPrintJob({ userNotes: 'A test job' });

    const [url, init] = requestFetch.mock.calls[0] ?? [];
    if (typeof url !== 'string') {
      throw new Error('Expected the Connect transport to pass a URL string.');
    }
    expect(url).toBe('/api/server.v1.PrintJobService/CreatePrintJob');
    expect(init?.method).toBe('POST');
    expect(new Headers(init?.headers).get('Content-Type')).toBe(
      'application/json',
    );
    if (init?.body == null) {
      throw new Error('Expected a Connect request body.');
    }
    const requestBody = await new Response(init.body).text();
    expect(JSON.parse(requestBody)).toEqual({
      userNotes: 'A test job',
    });
  });

  it('preserves ConnectRPC errors from the server', async () => {
    const requestFetch = vi.fn<typeof globalThis.fetch>(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            code: 'invalid_argument',
            message: 'Bad request',
          }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    );
    const api = createApiClient({ fetch: requestFetch });

    const request = api.printJobs.createPrintJob({ userNotes: 'A test job' });
    await expect(request).rejects.toBeInstanceOf(ConnectError);
    await expect(request).rejects.toMatchObject({
      code: Code.InvalidArgument,
      rawMessage: 'Bad request',
    });
  });
});
