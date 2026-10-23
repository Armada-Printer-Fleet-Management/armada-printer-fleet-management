// TEMPORARY: placeholder content for routes before their feature pages are ready. Replace each
// use with its real page when the submission and status flows are implemented.

import * as React from 'react';

import { cn } from '../lib/utils';

export interface TempRoutePageProps extends React.HTMLAttributes<HTMLElement> {
  heading: string;
  description: string;
}

const TempRoutePage = React.forwardRef<HTMLElement, TempRoutePageProps>(
  ({ heading, description, className, ...props }, ref) => (
    <section ref={ref} className={cn('grid gap-3', className)} {...props}>
      <h1 className="text-3xl font-bold">{heading}</h1>
      <p className="text-sm text-foreground/70">{description}</p>
    </section>
  ),
);
TempRoutePage.displayName = 'TempRoutePage';

export { TempRoutePage };
