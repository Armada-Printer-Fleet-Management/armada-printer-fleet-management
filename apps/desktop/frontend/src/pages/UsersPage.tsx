import * as React from 'react';
import { timestampDate } from '@bufbuild/protobuf/wkt';
import {
  type RequestFailure,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableSkeleton,
  TableSkeletonRows,
  Pagination,
  pageWindow,
  requestFailureMessage,
} from '@armada/ui-kit';
import { type User, UserRole, UserStatus } from '../gen/auth/v1/user_pb';
import { listUsers } from '../ipc/user';
import { routePaths } from '../routes';

const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.UNSPECIFIED]: 'Unknown',
  [UserRole.GUEST]: 'Guest',
  [UserRole.STUDENT]: 'Student',
  [UserRole.STAFF]: 'Staff',
  [UserRole.ADMIN]: 'Admin',
};

const STATUS_LABELS: Record<UserStatus, string> = {
  [UserStatus.UNSPECIFIED]: 'Unknown',
  [UserStatus.ACTIVE]: 'Active',
  [UserStatus.SUSPENDED]: 'Suspended',
  [UserStatus.DELETED]: 'Deleted',
};

const COLUMNS = ['Name', 'Email', 'Role', 'Status', 'Last sign-in'] as const;

const BUTTON_CLASS =
  'w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50';

const PAGE_SIZES = [10, 20, 50, 100] as const;
const DEFAULT_PAGE_SIZE = 10;

// A move to a table page, kept so a failed load can retry exactly that move.
interface PageMove {
  page: number;
  pageSize: number;
}

type State =
  | { kind: 'loading'; move: PageMove }
  | { kind: 'failed'; failure: RequestFailure; move: PageMove }
  | { kind: 'loaded' };

// The backend's exception class name arrives as the error's name.
function classifyFailure(error: unknown): RequestFailure {
  if (!(error instanceof Error)) return 'other';
  if (error.name === 'SignInRequired') return 'signed-out';
  if (error.name === 'Unavailable' || error.name === 'ServerNotConfigured') {
    return 'unreachable';
  }
  return 'other';
}

function lastSignIn(user: User): string {
  return user.lastLoginAt
    ? timestampDate(user.lastLoginAt).toLocaleString()
    : 'Never';
}

export function UsersPage() {
  // Server paging: every user loaded so far, and whether the server has more.
  const [users, setUsers] = React.useState<User[]>([]);
  const [hasMore, setHasMore] = React.useState(true);
  const usersRef = React.useRef<User[]>([]);
  const nextPageTokenRef = React.useRef('');
  const hasMoreRef = React.useRef(true);

  // Table paging over the loaded users; it never reaches the server.
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(DEFAULT_PAGE_SIZE);
  const [state, setState] = React.useState<State>({
    kind: 'loading',
    move: { page: 1, pageSize: DEFAULT_PAGE_SIZE },
  });

  // Fetches server pages until count users are loaded or the server has no more. Refs carry the
  // latest list and token between fetches, so the loop never reads stale state.
  const loadUntil = React.useCallback(async (count: number) => {
    while (usersRef.current.length < count && hasMoreRef.current) {
      const response = await listUsers({
        page: { pageToken: nextPageTokenRef.current },
      });
      usersRef.current = [...usersRef.current, ...response.users];
      nextPageTokenRef.current = response.page?.nextPageToken ?? '';
      hasMoreRef.current = nextPageTokenRef.current !== '';
      setUsers(usersRef.current);
      setHasMore(hasMoreRef.current);
    }
    return usersRef.current.length;
  }, []);

  // Lands on the page asked for, or the last page with rows when the server ran out first.
  const finishMove = React.useCallback(
    (move: PageMove) => {
      loadUntil(move.page * move.pageSize)
        .then((loaded) => {
          const lastPage = Math.max(1, Math.ceil(loaded / move.pageSize));
          setPageSize(move.pageSize);
          setPage(Math.min(move.page, lastPage));
          setState({ kind: 'loaded' });
        })
        .catch((error: unknown) => {
          setState({ kind: 'failed', failure: classifyFailure(error), move });
        });
    },
    [loadUntil],
  );

  React.useEffect(() => {
    finishMove({ page: 1, pageSize: DEFAULT_PAGE_SIZE });
  }, [finishMove]);

  const moveTo = (move: PageMove) => {
    const target = pageWindow({
      ...move,
      loadedCount: usersRef.current.length,
      hasMore: hasMoreRef.current,
    });
    if (!target.needsLoad) {
      setPageSize(move.pageSize);
      setPage(move.page);
      setState({ kind: 'loaded' });
      return;
    }
    setState({ kind: 'loading', move });
    finishMove(move);
  };

  const shown = pageWindow({
    page,
    pageSize,
    loadedCount: users.length,
    hasMore,
  });
  const loadingPage = state.kind === 'loading' && users.length > 0;

  return (
    // The page fills the window and only the table scrolls, so the heading, paging controls
    // and any alert below stay in view however many rows a page holds.
    <div className="flex h-full flex-col gap-6">
      <h1 className="text-3xl font-bold">{routePaths.users.label}</h1>

      {state.kind === 'loading' && users.length === 0 && (
        <TableSkeleton
          columns={COLUMNS.length}
          headers={COLUMNS}
          label="Loading users"
        />
      )}

      {users.length > 0 && (
        <Pagination
          page={page}
          pageSize={pageSize}
          pageSizeOptions={PAGE_SIZES}
          rangeStart={shown.start + 1}
          rangeEnd={shown.end}
          loadedCount={users.length}
          hasMore={hasMore}
          hasPrevious={shown.hasPrevious}
          hasNext={shown.hasNext}
          busy={loadingPage}
          onPrevious={() => moveTo({ page: page - 1, pageSize })}
          onNext={() => moveTo({ page: page + 1, pageSize })}
          // The first row on screen stays on screen when the size changes.
          onPageSizeChange={(size) =>
            moveTo({ page: Math.floor(shown.start / size) + 1, pageSize: size })
          }
        />
      )}

      {users.length > 0 && (
        <Table aria-label="Users" containerClassName="min-h-0">
          <TableHeader className="sticky top-0">
            <TableRow>
              {COLUMNS.map((column) => (
                <TableHead key={column}>{column}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loadingPage ? (
              <TableSkeletonRows
                rows={state.move.pageSize}
                columns={COLUMNS.length}
              />
            ) : (
              users.slice(shown.start, shown.end).map((user) => (
                <TableRow key={user.id?.value ?? user.email}>
                  <TableCell className="font-medium">
                    {user.firstName} {user.lastName}
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{ROLE_LABELS[user.role]}</TableCell>
                  <TableCell>
                    {user.status === UserStatus.ACTIVE ? (
                      STATUS_LABELS[user.status]
                    ) : (
                      <span className="rounded-md bg-accent px-2 py-0.5 text-accent-foreground">
                        {STATUS_LABELS[user.status]}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{lastSignIn(user)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}

      {state.kind === 'loaded' && users.length === 0 && <p>No users yet.</p>}

      {state.kind === 'failed' && (
        <div role="alert" className="flex flex-col gap-3">
          <p>{requestFailureMessage(state.failure)}</p>
          <button
            type="button"
            className={BUTTON_CLASS}
            onClick={() => moveTo(state.move)}
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
