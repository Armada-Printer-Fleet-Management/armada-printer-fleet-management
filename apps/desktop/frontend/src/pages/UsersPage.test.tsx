// @vitest-environment jsdom

import { create, type MessageInitShape } from '@bufbuild/protobuf';
import { timestampFromDate } from '@bufbuild/protobuf/wkt';
import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';

import { requestFailureMessage } from '@armada/ui-kit';
import { UserRole, UserSchema, UserStatus } from '../gen/auth/v1/user_pb';
import { ListUsersResponseSchema } from '../gen/server/v1/user_service_pb';
import { listUsers } from '../ipc/user';
import { UsersPage } from './UsersPage';

vi.mock('../ipc/user', () => ({ listUsers: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.mocked(listUsers).mockReset();
});

function user(init: MessageInitShape<typeof UserSchema>) {
  return create(UserSchema, {
    firstName: 'An',
    lastName: 'Operator',
    role: UserRole.STAFF,
    status: UserStatus.ACTIVE,
    ...init,
  });
}

function page(
  users: ReturnType<typeof user>[],
  nextPageToken = '',
): ReturnType<typeof create<typeof ListUsersResponseSchema>> {
  return create(ListUsersResponseSchema, { users, page: { nextPageToken } });
}

function failure(name: string): Error {
  const error = new Error('backend error');
  error.name = name;
  return error;
}

it('says so when there are no users', async () => {
  vi.mocked(listUsers).mockResolvedValue(page([]));
  render(<UsersPage />);

  expect(await screen.findByText('No users yet.')).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
});

it('explains an unreachable server and loads on retry', async () => {
  vi.mocked(listUsers)
    .mockRejectedValueOnce(failure('Unavailable'))
    .mockResolvedValueOnce(page([user({ email: 'back@example.edu' })]));
  render(<UsersPage />);

  const alert = await screen.findByRole('alert');
  expect(alert.textContent).toContain(requestFailureMessage('unreachable'));
  await userEvent.click(within(alert).getByRole('button', { name: 'Retry' }));

  expect(await screen.findByText('back@example.edu')).toBeTruthy();
  expect(screen.queryByRole('alert')).toBeNull();
});

it('shows readable labels, marks inactive users and never-signed-in users', async () => {
  vi.mocked(listUsers).mockResolvedValue(
    page([
      user({
        email: 'active@example.edu',
        role: UserRole.ADMIN,
        lastLoginAt: timestampFromDate(new Date(2026, 9, 1, 9, 0)),
      }),
      user({
        email: 'suspended@example.edu',
        role: UserRole.STUDENT,
        status: UserStatus.SUSPENDED,
      }),
    ]),
  );
  render(<UsersPage />);

  const active = (await screen.findByText('active@example.edu')).closest('tr');
  const suspended = screen.getByText('suspended@example.edu').closest('tr');
  if (!active || !suspended) throw new Error('rows not rendered');

  expect(within(active).getByText('Admin')).toBeTruthy();
  expect(within(active).getByText('Active').tagName).toBe('TD');
  expect(within(active).queryByText('Never')).toBeNull();
  expect(within(suspended).getByText('Student')).toBeTruthy();
  expect(within(suspended).getByText('Suspended').tagName).toBe('SPAN');
  expect(within(suspended).getByText('Never')).toBeTruthy();
});

type Page = ReturnType<typeof page>;

// A request the test resolves itself, so it can look at the page while it waits.
function pending() {
  let resolve: (value: Page) => void = () => undefined;
  const promise = new Promise<Page>((settle) => {
    resolve = settle;
  });
  return { promise, resolve };
}

it('shows a table skeleton while the first page loads', async () => {
  const first = pending();
  vi.mocked(listUsers).mockReturnValueOnce(first.promise);
  render(<UsersPage />);

  expect(screen.getByRole('status').textContent).toContain('Loading users');
  expect(screen.queryByRole('table')).toBeNull();
  expect(screen.queryByText('Loading users…')).toBeNull();

  first.resolve(page([user({ email: 'first@example.edu' })]));

  expect(await screen.findByText('first@example.edu')).toBeTruthy();
  expect(screen.queryByRole('status')).toBeNull();
});

it('shows the skeleton again while a retry loads', async () => {
  const retry = pending();
  vi.mocked(listUsers)
    .mockRejectedValueOnce(failure('Unavailable'))
    .mockReturnValueOnce(retry.promise);
  render(<UsersPage />);
  await userEvent.click(
    within(await screen.findByRole('alert')).getByRole('button', {
      name: 'Retry',
    }),
  );

  expect(screen.getByRole('status').textContent).toContain('Loading users');

  retry.resolve(page([user({ email: 'back@example.edu' })]));

  expect(await screen.findByText('back@example.edu')).toBeTruthy();
  expect(screen.queryByRole('status')).toBeNull();
});

// count users, emailed u<from>@ … u<from + count - 1>@, so each table page's rows are known.
function users(count: number, from = 1) {
  return Array.from({ length: count }, (_, index) =>
    user({ email: `u${from + index}@example.edu` }),
  );
}

function nextButton() {
  return screen.getByRole('button', { name: 'Next' });
}

it('moves between loaded pages without asking the server again', async () => {
  vi.mocked(listUsers).mockResolvedValueOnce(page(users(50)));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');

  await userEvent.click(nextButton());
  expect(screen.getByText('u11@example.edu')).toBeTruthy();
  expect(screen.queryByText('u1@example.edu')).toBeNull();

  await userEvent.click(screen.getByRole('button', { name: 'Previous' }));
  expect(screen.getByText('u1@example.edu')).toBeTruthy();
  expect(vi.mocked(listUsers)).toHaveBeenCalledOnce();
});

it('fetches the next server page once when a table page goes past what is loaded', async () => {
  const next = pending();
  vi.mocked(listUsers)
    .mockResolvedValueOnce(page(users(10), 'p2'))
    .mockReturnValueOnce(next.promise);
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');

  await userEvent.click(nextButton());

  expect(vi.mocked(listUsers)).toHaveBeenLastCalledWith({
    page: { pageToken: 'p2' },
  });
  expect(screen.queryByText('u1@example.edu')).toBeNull();
  expect(screen.getAllByRole('row')).toHaveLength(1);
  expect(nextButton().hasAttribute('disabled')).toBe(true);
  expect(
    screen.getByRole('button', { name: 'Previous' }).hasAttribute('disabled'),
  ).toBe(true);

  next.resolve(page(users(10, 11)));

  expect(await screen.findByText('u11@example.edu')).toBeTruthy();
  expect(vi.mocked(listUsers)).toHaveBeenCalledTimes(2);
});

it('fetches server pages until a large table page is full', async () => {
  vi.mocked(listUsers)
    .mockResolvedValueOnce(page(users(30), 'p2'))
    .mockResolvedValueOnce(page(users(30, 31), 'p3'))
    .mockResolvedValueOnce(page(users(50, 61)));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');

  await userEvent.selectOptions(screen.getByLabelText('Rows per page'), '100');

  expect(await screen.findByText('Showing 1–100 of 110')).toBeTruthy();
  expect(vi.mocked(listUsers)).toHaveBeenCalledTimes(3);
});

it('keeps the first row on screen when the page size changes', async () => {
  vi.mocked(listUsers).mockResolvedValueOnce(page(users(50)));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');
  await userEvent.click(nextButton());
  await userEvent.click(nextButton());
  expect(screen.getByText('Showing 21–30 of 50')).toBeTruthy();

  await userEvent.selectOptions(screen.getByLabelText('Rows per page'), '20');

  expect(screen.getByText('Showing 21–40 of 50')).toBeTruthy();
  expect(screen.getByText('Page 2')).toBeTruthy();
});

it('stays put and stops offering Next when the server has nothing more', async () => {
  vi.mocked(listUsers)
    .mockResolvedValueOnce(page(users(10), 'p2'))
    .mockResolvedValueOnce(page([]));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');

  await userEvent.click(nextButton());

  expect(await screen.findByText('u1@example.edu')).toBeTruthy();
  expect(screen.getByText('Page 1')).toBeTruthy();
  expect(nextButton().hasAttribute('disabled')).toBe(true);
});

it('keeps the current rows when a page fails to load, and retries that move', async () => {
  vi.mocked(listUsers)
    .mockResolvedValueOnce(page(users(10), 'p2'))
    .mockRejectedValueOnce(failure('Unavailable'))
    .mockResolvedValueOnce(page(users(10, 11)));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');

  await userEvent.click(nextButton());

  const alert = await screen.findByRole('alert');
  expect(screen.getByText('u1@example.edu')).toBeTruthy();
  await userEvent.click(within(alert).getByRole('button', { name: 'Retry' }));

  expect(await screen.findByText('u11@example.edu')).toBeTruthy();
  expect(screen.queryByRole('alert')).toBeNull();
  expect(vi.mocked(listUsers)).toHaveBeenLastCalledWith({
    page: { pageToken: 'p2' },
  });
});

it('clears the failure once the operator moves to a loaded page', async () => {
  vi.mocked(listUsers)
    .mockResolvedValueOnce(page(users(20), 'p2'))
    .mockRejectedValueOnce(failure('Unavailable'));
  render(<UsersPage />);
  await screen.findByText('u1@example.edu');
  await userEvent.click(nextButton());
  await userEvent.click(nextButton());
  await screen.findByRole('alert');

  await userEvent.click(screen.getByRole('button', { name: 'Previous' }));

  expect(screen.queryByRole('alert')).toBeNull();
  expect(screen.getByText('u1@example.edu')).toBeTruthy();
});
