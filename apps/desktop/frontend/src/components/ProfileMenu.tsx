import { cn, UserIcon } from '@armada/ui-kit';
import { type ToggleEvent, useId, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { session, signOut } from '../ipc/session';
import { routePaths } from '../routes';
import { RailLabel, railItemClass } from './RailLabel';

const menuItem =
  'block rounded-md px-3 py-2 text-sm hover:bg-secondary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

const menuRoutes = [routePaths.account, routePaths.about];

// A native popover gives light dismiss, Escape to close and focus return without a dependency.
export function ProfileMenu({ expanded }: { expanded: boolean }) {
  const menuId = useId();
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [signedIn, setSignedIn] = useState(false);
  const close = () => menuRef.current?.hidePopover();
  // Read on every open, so the menu matches a sign-in or sign-out made anywhere since.
  const refreshSession = (event: ToggleEvent<HTMLDivElement>) => {
    if (event.newState !== 'open') return;
    session()
      .then((current) => setSignedIn(current.session !== undefined))
      .catch(() => setSignedIn(false));
  };
  const logOut = () => {
    close();
    setSignedIn(false);
    // The backend clears the session even when the provider is unreachable, so always leave.
    void signOut()
      .catch(() => undefined)
      .finally(() => navigate(routePaths.login.path));
  };

  return (
    <>
      <RailLabel expanded={expanded} label="Profile">
        {(labelNode) => (
          <button
            type="button"
            popoverTarget={menuId}
            className={cn(
              railItemClass(expanded),
              'text-muted-foreground hover:bg-secondary-hover hover:text-foreground',
            )}
          >
            <span className="flex size-8 items-center justify-center rounded-full border border-border bg-background">
              <UserIcon className="size-5" />
            </span>
            {labelNode}
          </button>
        )}
      </RailLabel>
      <div
        id={menuId}
        ref={menuRef}
        popover="auto"
        onToggle={refreshSession}
        className="inset-auto bottom-20 left-2 m-0 w-48 rounded-lg border border-border bg-card p-1 text-card-foreground shadow-lg"
      >
        <ul className="grid gap-1">
          {menuRoutes.map((route) => (
            <li key={route.path}>
              <Link to={route.path} onClick={close} className={menuItem}>
                {route.label}
              </Link>
            </li>
          ))}
          <li className="border-t border-border pt-1">
            {signedIn ? (
              <button
                type="button"
                onClick={logOut}
                className={`${menuItem} w-full text-left`}
              >
                Log out
              </button>
            ) : (
              <Link
                to={routePaths.login.path}
                onClick={close}
                className={menuItem}
              >
                {routePaths.login.label}
              </Link>
            )}
          </li>
        </ul>
      </div>
    </>
  );
}
