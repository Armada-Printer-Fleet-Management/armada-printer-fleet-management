import {
  ChevronLeftIcon,
  cn,
  DevToolsIcon,
  type IconProps,
} from '@armada/ui-kit';
import { type ComponentType, useState } from 'react';
import { NavLink } from 'react-router';

import { devToolsEnabled } from '../lib/dev-tools';
import { navRoutes, routePaths } from '../routes';
import { ProfileMenu } from './ProfileMenu';
import { focusRing, RailLabel, railItemClass } from './RailLabel';

interface RailLinkProps {
  path: string;
  label: string;
  icon: ComponentType<IconProps>;
  expanded: boolean;
  className: (isActive: boolean) => string;
}

function RailLink({
  path,
  label,
  icon: Icon,
  expanded,
  className,
}: RailLinkProps) {
  return (
    <li>
      <RailLabel expanded={expanded} label={label}>
        {(labelNode) => (
          <NavLink
            end
            to={path}
            className={({ isActive }) =>
              cn(railItemClass(expanded), className(isActive))
            }
          >
            <Icon />
            {labelNode}
          </NavLink>
        )}
      </RailLabel>
    </li>
  );
}

function standardItem(isActive: boolean) {
  return isActive
    ? 'bg-primary text-primary-foreground'
    : 'text-foreground/70 hover:bg-foreground/5 hover:text-foreground';
}

function devItem(isActive: boolean) {
  return cn(
    'bg-dev-highlight text-dev-highlight-foreground',
    isActive && 'ring-2 ring-dev-highlight-foreground ring-inset',
  );
}

export function DesktopNavRail() {
  const [expanded, setExpanded] = useState(true);

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        'flex shrink-0 flex-col border-r border-border bg-card p-2',
        expanded ? 'w-48' : 'w-16 items-center',
      )}
    >
      <button
        type="button"
        aria-expanded={expanded}
        aria-label="Navigation labels"
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'mb-2 flex size-12 items-center justify-center self-end rounded-md text-foreground/70 hover:bg-foreground/5 hover:text-foreground',
          focusRing,
          !expanded && 'self-center',
        )}
      >
        <ChevronLeftIcon className={cn(!expanded && 'rotate-180')} />
      </button>
      <ul className="flex flex-col gap-1">
        {navRoutes
          .filter((route) => route.nav === 'main')
          .map((route) => (
            <RailLink
              key={route.path}
              {...route}
              expanded={expanded}
              className={standardItem}
            />
          ))}
      </ul>
      <ul className="mt-auto flex flex-col gap-1">
        {devToolsEnabled() && (
          <RailLink
            path={routePaths.temp.path}
            label={routePaths.temp.label}
            icon={DevToolsIcon}
            expanded={expanded}
            className={devItem}
          />
        )}
        {navRoutes
          .filter((route) => route.nav === 'footer')
          .map((route) => (
            <RailLink
              key={route.path}
              {...route}
              expanded={expanded}
              className={standardItem}
            />
          ))}
        <li className="mt-2">
          <ProfileMenu expanded={expanded} />
        </li>
      </ul>
    </nav>
  );
}
