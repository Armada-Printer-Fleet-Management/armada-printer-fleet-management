import { read } from '@armada/organization-info';
import { OrganizationInfoSchema } from '@armada/api-client/gen/common/v1/organization_info_pb';
import {
  cn,
  DevToolsIcon,
  LogInIcon,
  LogOutIcon,
  type IconProps,
} from '@armada/ui-kit';
import { type ComponentType, useState } from 'react';
import { Link, NavLink } from 'react-router';

import { useAuth } from '../lib/auth-context';
import { devToolsEnabled } from '../lib/dev-tools';
import { navRoutes, routePaths } from '../routes';

const focusRing =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';
const itemClass = cn(
  'flex h-10 items-center gap-2.5 rounded-full px-3.5 text-sm',
  focusRing,
);

// The organization title reads "<name> - <tagline>"; the wordmark shows the name over the tagline.
function wordmarkParts(title: string) {
  const [name = title, ...rest] = title.split(' - ');
  return { name, tagline: rest.join(' - ') };
}

interface SidebarLinkProps {
  path: string;
  label: string;
  icon: ComponentType<IconProps>;
  className?: (isActive: boolean) => string;
}

function SidebarLink({ path, label, icon: Icon, className }: SidebarLinkProps) {
  return (
    <li>
      <NavLink
        end
        to={path}
        className={({ isActive }) =>
          cn(
            itemClass,
            className
              ? className(isActive)
              : isActive
                ? 'bg-background font-semibold text-foreground'
                : 'text-foreground/80 hover:bg-foreground/5 hover:text-foreground',
          )
        }
      >
        <Icon className="size-[18px]" />
        {label}
      </NavLink>
    </li>
  );
}

function AccountItem() {
  const { user, loading, signIn, signOut } = useAuth();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  // Holds the space until the stored session is read, so a signed-in user never sees "Sign in".
  if (loading) {
    return <li aria-hidden="true" className="h-10" />;
  }

  const signedIn = user !== null;
  const Icon = signedIn ? LogOutIcon : LogInIcon;
  const label = busy
    ? signedIn
      ? 'Signing out…'
      : 'Signing in…'
    : signedIn
      ? 'Sign out'
      : 'Sign in';

  // Success leaves the page for the sign-in server, so only a failure returns here.
  function start() {
    setBusy(true);
    setFailed(false);
    (signedIn ? signOut() : signIn()).catch(() => {
      setBusy(false);
      setFailed(true);
    });
  }

  return (
    <li>
      <button
        type="button"
        disabled={busy}
        onClick={start}
        className={cn(
          itemClass,
          'w-full cursor-pointer text-foreground/80 hover:bg-foreground/5 hover:text-foreground disabled:cursor-wait',
        )}
      >
        <Icon className="size-[18px]" />
        {label}
      </button>
      {failed && (
        <p role="alert" className="px-3.5 pt-1 text-xs text-foreground">
          Couldn’t reach the sign-in service. Try again in a moment.
        </p>
      )}
    </li>
  );
}

function devItem(isActive: boolean) {
  return cn(
    'bg-dev-highlight text-dev-highlight-foreground',
    isActive && 'ring-2 ring-dev-highlight-foreground ring-inset',
  );
}

export function Sidebar() {
  const { name, tagline } = wordmarkParts(read(OrganizationInfoSchema).title);

  return (
    <nav
      aria-label="Main navigation"
      className="flex w-60 shrink-0 flex-col gap-6 border-r border-border bg-card p-4"
    >
      <div className="pt-4 text-center">
        <p className="text-4xl leading-none font-black text-primary uppercase">
          {name}
        </p>
        {tagline && (
          <p className="mt-1 text-xs text-foreground/70">{tagline}</p>
        )}
      </div>
      <Link
        to={routePaths.myPrints.path}
        className={cn(
          'flex h-10 items-center justify-center gap-1.5 rounded-lg bg-primary text-sm font-semibold text-primary-foreground hover:opacity-90',
          focusRing,
        )}
      >
        <span aria-hidden="true" className="text-lg font-normal">
          +
        </span>
        New print
      </Link>
      <ul className="flex flex-col gap-1">
        {navRoutes.map((route) => (
          <SidebarLink key={route.path} {...route} />
        ))}
      </ul>
      <ul className="mt-auto flex flex-col gap-1">
        {devToolsEnabled() && (
          <SidebarLink
            path={routePaths.temp.path}
            label={routePaths.temp.label}
            icon={DevToolsIcon}
            className={devItem}
          />
        )}
        <AccountItem />
      </ul>
    </nav>
  );
}
