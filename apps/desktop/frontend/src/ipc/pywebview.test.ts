// @vitest-environment jsdom
// The IPC root that waitForPywebviewIpc() returns announces SignInRequired for every call.

import { afterEach, expect, it, vi } from 'vitest';

import { SIGN_IN_REQUIRED_EVENT, waitForPywebviewIpc } from './pywebview';

type Probe = { probe: { call(...args: unknown[]): Promise<unknown> } };

function installApi(call: (...args: unknown[]) => Promise<unknown>) {
  window.pywebview = { api: { probe: { call } } as unknown as PywebviewIpc };
}

async function ipc() {
  return (await waitForPywebviewIpc()) as unknown as Probe;
}

afterEach(() => {
  delete window.pywebview;
});

it('announces SignInRequired with its message and still rejects', async () => {
  const error = Object.assign(new Error('Your session has ended.'), {
    name: 'SignInRequired',
  });
  installApi(vi.fn().mockRejectedValue(error));
  const listener = vi.fn();
  window.addEventListener(SIGN_IN_REQUIRED_EVENT, listener);

  await expect((await ipc()).probe.call()).rejects.toBe(error);

  window.removeEventListener(SIGN_IN_REQUIRED_EVENT, listener);
  expect(listener).toHaveBeenCalledOnce();
  const event: unknown = listener.mock.calls[0]?.[0];
  expect(event).toBeInstanceOf(CustomEvent);
  expect((event as CustomEvent).detail).toBe('Your session has ended.');
});

it('passes arguments and results through unchanged', async () => {
  const call = vi.fn().mockResolvedValue({ value: 1 });
  installApi(call);
  const listener = vi.fn();
  window.addEventListener(SIGN_IN_REQUIRED_EVENT, listener);

  await expect((await ipc()).probe.call('a', 2)).resolves.toEqual({
    value: 1,
  });

  window.removeEventListener(SIGN_IN_REQUIRED_EVENT, listener);
  expect(call).toHaveBeenCalledWith('a', 2);
  expect(listener).not.toHaveBeenCalled();
});
