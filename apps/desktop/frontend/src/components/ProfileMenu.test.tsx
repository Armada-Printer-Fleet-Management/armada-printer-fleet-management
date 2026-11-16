// @vitest-environment jsdom

import { create } from '@bufbuild/protobuf';
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterAll, afterEach, beforeAll, expect, it, vi } from 'vitest';

import { CurrentSessionSchema } from '../gen/desktop/v1/current_session_pb';
import { session, signOut } from '../ipc/session';
import { routePaths } from '../routes';
import { ProfileMenu } from './ProfileMenu';

vi.mock('../ipc/session', () => ({ session: vi.fn(), signOut: vi.fn() }));

const SIGNED_IN = create(CurrentSessionSchema, {
  session: { email: 'operator@example.edu' },
});
const SIGNED_OUT = create(CurrentSessionSchema, {});

// jsdom has no popover API; closing the menu only needs hidePopover() to exist.
beforeAll(() => {
  HTMLElement.prototype.hidePopover = vi.fn();
});

afterAll(() => {
  Reflect.deleteProperty(HTMLElement.prototype, 'hidePopover');
});

afterEach(cleanup);

function renderMenu() {
  render(
    <MemoryRouter>
      <Routes>
        <Route
          path={routePaths.dashboard.path}
          element={<ProfileMenu expanded />}
        />
        <Route path={routePaths.login.path} element={<p>login page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

// jsdom never fires the popover's toggle event, so open it the way a browser reports it. It
// also keeps the popover display: none, so the queries below include hidden elements.
function openMenu() {
  const menu = document.querySelector('[popover]');
  if (!menu) throw new Error('ProfileMenu rendered no popover');
  act(() => {
    fireEvent(menu, Object.assign(new Event('toggle'), { newState: 'open' }));
  });
}

const logIn = { name: routePaths.login.label, hidden: true };
const logOut = { name: 'Log out', hidden: true };

it('offers Log in when nobody is signed in', async () => {
  vi.mocked(session).mockResolvedValue(SIGNED_OUT);
  renderMenu();

  openMenu();

  expect(await screen.findByRole('link', logIn)).toBeTruthy();
  expect(screen.queryByRole('button', logOut)).toBeNull();
});

it('offers Log out when the operator is signed in', async () => {
  vi.mocked(session).mockResolvedValue(SIGNED_IN);
  renderMenu();

  openMenu();

  expect(await screen.findByRole('button', logOut)).toBeTruthy();
  expect(screen.queryByRole('link', logIn)).toBeNull();
});

it('signs out and goes to the login page', async () => {
  vi.mocked(session).mockResolvedValue(SIGNED_IN);
  vi.mocked(signOut).mockResolvedValue(SIGNED_OUT);
  renderMenu();
  openMenu();

  await userEvent.click(await screen.findByRole('button', logOut));

  expect(signOut).toHaveBeenCalledOnce();
  expect(await screen.findByText('login page')).toBeTruthy();
});
