// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';

import { SignInControls } from './sign-in-controls';

afterEach(cleanup);

it('offers Sign in when idle and starts it when chosen', async () => {
  const onSignIn = vi.fn();
  render(<SignInControls status="idle" onSignIn={onSignIn} />);

  const button = screen.getByRole('button', { name: 'Sign in' });
  expect(button.hasAttribute('disabled')).toBe(false);
  await userEvent.click(button);

  expect(onSignIn).toHaveBeenCalledOnce();
});

it('shows the waiting label and hint, and holds the button, while signing in', () => {
  render(
    <SignInControls
      status="waiting"
      onSignIn={vi.fn()}
      waitingLabel="Waiting for your browser…"
      waitingHint="Finish signing in in your browser."
    />,
  );

  const button = screen.getByRole('button', {
    name: 'Waiting for your browser…',
  });
  expect(button.hasAttribute('disabled')).toBe(true);
  expect(screen.getByText('Finish signing in in your browser.')).toBeTruthy();
});

it('reports a failed sign-in and lets the user try again', () => {
  render(
    <SignInControls
      status="error"
      error="Sign-in was cancelled."
      onSignIn={vi.fn()}
    />,
  );

  expect(screen.getByRole('alert').textContent).toBe('Sign-in was cancelled.');
  expect(
    screen.getByRole('button', { name: 'Sign in' }).hasAttribute('disabled'),
  ).toBe(false);
});
