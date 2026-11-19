import { create } from '@bufbuild/protobuf';
import { Code, ConnectError } from '@connectrpc/connect';
import { describe, expect, it, vi } from 'vitest';
import { createApiClient, type AccessToken } from './client';
import { FileUploadSlotSchema } from './gen/content_asset/v1/file_upload_pb';

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

describe('createApiClient access token', () => {
  function okFetch() {
    return vi.fn<typeof globalThis.fetch>(() =>
      Promise.resolve(
        new Response('{}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
  }

  function authorization(
    requestFetch: ReturnType<typeof okFetch>,
    call: number,
  ): string | null {
    const [, init] = requestFetch.mock.calls[call] ?? [];
    return new Headers(init?.headers).get('Authorization');
  }

  const slot = create(FileUploadSlotSchema, { uploadUrl: '/api/files/1' });

  it('sends the token as a Bearer header on RPCs', async () => {
    const requestFetch = okFetch();
    const api = createApiClient({
      fetch: requestFetch,
      accessToken: () => Promise.resolve('abc'),
    });

    await api.printJobs.createPrintJob({ userNotes: 'A test job' });

    expect(authorization(requestFetch, 0)).toBe('Bearer abc');
  });

  it.each<[string, AccessToken | undefined]>([
    ['no accessToken option', undefined],
    ['a getter with no token', () => Promise.resolve(undefined)],
  ])('sends no Authorization header with %s', async (_case, accessToken) => {
    const requestFetch = okFetch();
    const api = createApiClient({ fetch: requestFetch, accessToken });

    await api.printJobs.createPrintJob({ userNotes: 'A test job' });
    await api.printJobs.uploadPrintJobFile(slot, new Blob(['G1']));

    expect(authorization(requestFetch, 0)).toBeNull();
    expect(authorization(requestFetch, 1)).toBeNull();
  });

  it('sends the token on the file upload and keeps the PUT intact', async () => {
    const requestFetch = okFetch();
    const api = createApiClient({
      fetch: requestFetch,
      accessToken: () => Promise.resolve('abc'),
    });
    const file = new Blob(['G1 X10']);

    await api.printJobs.uploadPrintJobFile(slot, file);

    const [url, init] = requestFetch.mock.calls[0] ?? [];
    expect(url).toBe('/api/files/1');
    expect(init?.method).toBe('PUT');
    expect(init?.body).toBe(file);
    expect(authorization(requestFetch, 0)).toBe('Bearer abc');
  });

  it('asks for the token again on every request', async () => {
    const requestFetch = okFetch();
    const accessToken = vi
      .fn<AccessToken>()
      .mockResolvedValueOnce('one')
      .mockResolvedValueOnce('two');
    const api = createApiClient({ fetch: requestFetch, accessToken });

    await api.printJobs.createPrintJob({ userNotes: 'First' });
    await api.printJobs.createPrintJob({ userNotes: 'Second' });

    expect(authorization(requestFetch, 0)).toBe('Bearer one');
    expect(authorization(requestFetch, 1)).toBe('Bearer two');
  });
});
