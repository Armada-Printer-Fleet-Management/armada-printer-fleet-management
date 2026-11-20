// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterAll, afterEach, beforeAll, expect, it, vi } from 'vitest';

import { SignInDialog, type SignInDialogProps } from './sign-in-dialog';

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

const required: SignInDialogProps = {
  open: true,
  description: 'Your session has ended.',
  onDismiss: () => undefined,
  status: 'idle',
  onSignIn: () => undefined,
};

function dialogElement() {
  const dialog = document.querySelector('dialog');
  if (!dialog) throw new Error('SignInDialog rendered no dialog');
  return dialog;
}

it('opens with its title and description, and closes when open turns false', () => {
  const { rerender } = render(<SignInDialog {...required} />);

  expect(dialogElement().open).toBe(true);
  expect(
    screen.getByRole('heading', { name: 'Sign in to continue', hidden: true }),
  ).toBeTruthy();
  expect(dialogElement().textContent).toContain('Your session has ended.');

  rerender(<SignInDialog {...required} open={false} />);

  expect(dialogElement().open).toBe(false);
});

it('calls onDismiss from the dismiss button', async () => {
  const onDismiss = vi.fn();
  render(<SignInDialog {...required} onDismiss={onDismiss} />);

  await userEvent.click(
    screen.getByRole('button', { name: 'Not now', hidden: true }),
  );

  expect(onDismiss).toHaveBeenCalledOnce();
});

it('calls onDismiss on Escape', () => {
  const onDismiss = vi.fn();
  render(<SignInDialog {...required} onDismiss={onDismiss} />);

  // Escape reaches a modal dialog as its cancel event.
  fireEvent(dialogElement(), new Event('cancel', { cancelable: true }));

  expect(onDismiss).toHaveBeenCalledOnce();
});

it('uses a custom title and dismiss label in place of the defaults', () => {
  render(
    <SignInDialog
      {...required}
      title="Your session ended"
      dismissLabel="Later"
    />,
  );

  expect(
    screen.getByRole('heading', { name: 'Your session ended', hidden: true }),
  ).toBeTruthy();
  expect(
    screen.getByRole('button', { name: 'Later', hidden: true }),
  ).toBeTruthy();
  expect(
    screen.queryByRole('button', { name: 'Not now', hidden: true }),
  ).toBeNull();
});
