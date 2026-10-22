import { cn } from '@armada/ui-kit';
import { NavLink } from 'react-router';

import { routePaths } from '../routes';

export function StudentNavBar() {
  return (
    <nav aria-label="Student navigation">
      <ul className="flex flex-wrap gap-2">
        {Object.entries(routePaths)
          .filter(([, route]) => route.showInNav)
          .map(([key, route]) => (
            <li key={key}>
              <NavLink
                end
                to={route.path}
                className={({ isActive }) =>
                  cn(
                    'inline-flex rounded-md px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted',
                  )
                }
              >
                {route.label}
              </NavLink>
            </li>
          ))}
      </ul>
    </nav>
  );
}
