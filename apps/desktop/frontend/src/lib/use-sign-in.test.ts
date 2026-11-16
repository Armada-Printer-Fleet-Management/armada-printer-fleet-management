// @vitest-environment jsdom

import { create } from '@bufbuild/protobuf';
import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

import {
  type CurrentSession,
  CurrentSessionSchema,
} from '../gen/desktop/v1/current_session_pb';
import { signIn } from '../ipc/session';
import { useSignIn } from './use-sign-in';

vi.mock('../ipc/session', () => ({ signIn: vi.fn() }));

const SIGNED_IN = create(CurrentSessionSchema, {
  session: { email: 'operator@example.edu' },
});

// A sign-in the test settles by hand, to see the hook's state while it is still waiting.
function pendingSignIn() {
  const settle: {
    resolve: (session: CurrentSession) => void;
    reject: (error: Error) => void;
  } = { resolve: () => undefined, reject: () => undefined };
  const promise = new Promise<CurrentSession>((resolve, reject) => {
    settle.resolve = resolve;
    settle.reject = reject;
  });
  return { promise, ...settle };
}

beforeEach(() => {
  vi.mocked(signIn).mockReset();
});

it('waits for the browser, then reports success and returns to idle', async () => {
  const pending = pendingSignIn();
  vi.mocked(signIn).mockReturnValue(pending.promise);
  const onSignedIn = vi.fn();
  const { result } = renderHook(() => useSignIn(onSignedIn));

  act(() => result.current.start());
  expect(result.current.state.status).toBe('waiting');

  act(() => pending.resolve(SIGNED_IN));
  await waitFor(() => expect(onSignedIn).toHaveBeenCalledOnce());
  expect(result.current.state.status).toBe('idle');
});

it('shows the message of a failed sign-in', async () => {
  vi.mocked(signIn).mockRejectedValue(new Error('Sign-in was cancelled.'));
  const onSignedIn = vi.fn();
  const { result } = renderHook(() => useSignIn(onSignedIn));

  act(() => result.current.start());

  await waitFor(() =>
    expect(result.current.state).toEqual({
      status: 'error',
      error: 'Sign-in was cancelled.',
    }),
  );
  expect(onSignedIn).not.toHaveBeenCalled();
});

it('ignores the result of an attempt that was restarted', async () => {
  const first = pendingSignIn();
  const second = pendingSignIn();
  vi.mocked(signIn)
    .mockReturnValueOnce(first.promise)
    .mockReturnValueOnce(second.promise);
  const onSignedIn = vi.fn();
  const { result } = renderHook(() => useSignIn(onSignedIn));

  act(() => result.current.start());
  act(() => result.current.start());
  act(() => first.reject(new Error('Sign-in was restarted.')));
  // Let the rejection reach the hook before checking that it was ignored.
  await act(() => first.promise.catch(() => undefined));
  expect(result.current.state.status).toBe('waiting');

  act(() => second.resolve(SIGNED_IN));
  await waitFor(() => expect(onSignedIn).toHaveBeenCalledOnce());
  expect(result.current.state.status).toBe('idle');
});
