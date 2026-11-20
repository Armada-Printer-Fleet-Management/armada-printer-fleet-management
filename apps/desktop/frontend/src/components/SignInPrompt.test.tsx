// @vitest-environment jsdom

import { create } from '@bufbuild/protobuf';
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterAll, afterEach, beforeAll, expect, it, vi } from 'vitest';

import { CurrentSessionSchema } from '../gen/desktop/v1/current_session_pb';
import { SIGN_IN_REQUIRED_EVENT } from '../ipc/pywebview';
import { signIn } from '../ipc/session';
import { SignInPrompt } from './SignInPrompt';

vi.mock('../ipc/session', () => ({ signIn: vi.fn() }));

// jsdom has no showModal() or close(); these do the part the dialog relies on.
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function (this: HTMLDialogElement) {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function (this: HTMLDialogElement) {
    this.open = false;
  };
});

afterAll(() => {
  Reflect.deleteProperty(HTMLDialogElement.prototype, 'showModal');
  Reflect.deleteProperty(HTMLDialogElement.prototype, 'close');
});

afterEach(cleanup);

function renderDialog() {
  render(
    <MemoryRouter>
      <SignInPrompt />
    </MemoryRouter>,
  );
  const dialog = document.querySelector('dialog');
  if (!dialog) throw new Error('SignInPrompt rendered no dialog');
  return dialog;
}

function requireSignIn(message: string) {
  act(() => {
    window.dispatchEvent(
      new CustomEvent(SIGN_IN_REQUIRED_EVENT, { detail: message }),
    );
  });
}

it('opens over the page with the backend message', () => {
  const dialog = renderDialog();
  expect(dialog.open).toBe(false);

  requireSignIn('Your session has ended.');

  expect(dialog.open).toBe(true);
  expect(dialog.textContent).toContain('Your session has ended.');
});

it('closes once the operator has signed in', async () => {
  vi.mocked(signIn).mockResolvedValue(
    create(CurrentSessionSchema, {
      session: { email: 'operator@example.edu' },
    }),
  );
  const dialog = renderDialog();
  requireSignIn('Your session has ended.');

  await userEvent.click(
    screen.getByRole('button', { name: 'Sign in', hidden: true }),
  );

  expect(dialog.open).toBe(false);
});
