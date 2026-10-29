import { read } from '@armada/organization-info';
import { OrganizationInfoSchema } from '@armada/api-client/gen/common/v1/organization_info_pb';
import { cn, DevToolsIcon, LogOutIcon, type IconProps } from '@armada/ui-kit';
import { type ComponentType } from 'react';
import { Link, NavLink } from 'react-router';

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
        <li>
          {/* STUB: renders the Sign out entry from the design. Wire it to the sign-in flow once authentication exists. */}
          <button
            type="button"
            disabled
            className={cn(
              itemClass,
              'w-full text-foreground/70 disabled:cursor-not-allowed',
            )}
          >
            <LogOutIcon className="size-[18px]" />
            Sign out
          </button>
        </li>
      </ul>
    </nav>
  );
}
