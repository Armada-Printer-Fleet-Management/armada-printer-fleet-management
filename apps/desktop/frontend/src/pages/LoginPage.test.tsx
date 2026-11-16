// @vitest-environment jsdom

import { create } from '@bufbuild/protobuf';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, expect, it, vi } from 'vitest';

import { CurrentSessionSchema } from '../gen/desktop/v1/current_session_pb';
import { signIn } from '../ipc/session';
import { routePaths } from '../routes';
import { LoginPage } from './LoginPage';

vi.mock('../ipc/session', () => ({ signIn: vi.fn() }));

afterEach(cleanup);

function renderLogin() {
  render(
    <MemoryRouter initialEntries={[routePaths.login.path]}>
      <Routes>
        <Route path={routePaths.login.path} element={<LoginPage />} />
        <Route
          path={routePaths.dashboard.path}
          element={<p>dashboard page</p>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

it('lands on the dashboard after signing in', async () => {
  vi.mocked(signIn).mockResolvedValue(
    create(CurrentSessionSchema, {
      session: { email: 'operator@example.edu' },
    }),
  );
  renderLogin();

  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  expect(await screen.findByText('dashboard page')).toBeTruthy();
});

it('shows why sign-in failed and lets the operator try again', async () => {
  vi.mocked(signIn).mockRejectedValue(new Error('Sign-in was cancelled.'));
  renderLogin();

  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  expect((await screen.findByRole('alert')).textContent).toBe(
    'Sign-in was cancelled.',
  );
  expect(
    screen.getByRole('button', { name: 'Sign in' }).hasAttribute('disabled'),
  ).toBe(false);
});
