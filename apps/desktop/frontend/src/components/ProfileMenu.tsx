import { cn, UserIcon } from '@armada/ui-kit';
import { useId, useRef } from 'react';
import { Link } from 'react-router';

import { routePaths } from '../routes';
import { RailLabel, railItemClass } from './RailLabel';

const menuItem =
  'block rounded-md px-3 py-2 text-sm hover:bg-foreground/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

const menuRoutes = [routePaths.account, routePaths.about];

// A native popover gives light dismiss, Escape to close and focus return without a dependency.
export function ProfileMenu({ expanded }: { expanded: boolean }) {
  const menuId = useId();
  const menuRef = useRef<HTMLDivElement>(null);
  const close = () => menuRef.current?.hidePopover();

  return (
    <>
      <RailLabel expanded={expanded} label="Profile">
        {(labelNode) => (
          <button
            type="button"
            popoverTarget={menuId}
            className={cn(
              railItemClass(expanded),
              'text-foreground/70 hover:bg-foreground/5 hover:text-foreground',
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
            <Link
              to={routePaths.login.path}
              onClick={close}
              className={menuItem}
            >
              Log out
            </Link>
          </li>
        </ul>
      </div>
    </>
  );
}
