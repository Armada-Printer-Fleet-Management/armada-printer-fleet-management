import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * A section that opens and closes, on the native <details>: keyboard operable and announced as
 * expanded or collapsed without extra ARIA. Closed unless `open` or `defaultOpen` says otherwise.
 */
const Collapsible = React.forwardRef<
  HTMLDetailsElement,
  React.DetailsHTMLAttributes<HTMLDetailsElement>
>(({ className, ...props }, ref) => (
  <details
    ref={ref}
    className={cn('group rounded-lg border bg-card', className)}
    {...props}
  />
));
Collapsible.displayName = 'Collapsible';

/** The always-visible header that toggles the section. */
const CollapsibleTrigger = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, children, ...props }, ref) => (
  <summary
    ref={ref}
    className={cn(
      'flex cursor-pointer list-none items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary [&::-webkit-details-marker]:hidden',
      className,
    )}
    {...props}
  >
    <span
      aria-hidden="true"
      className="inline-block transition-transform group-open:rotate-90"
    >
      ▸
    </span>
    {children}
  </summary>
));
CollapsibleTrigger.displayName = 'CollapsibleTrigger';

/** What the section reveals when open. */
const CollapsibleContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('px-4 pb-4', className)} {...props} />
));
CollapsibleContent.displayName = 'CollapsibleContent';

export { Collapsible, CollapsibleContent, CollapsibleTrigger };
