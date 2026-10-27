import * as React from 'react';

import { cn } from '../lib/utils';

export interface TooltipProps extends React.HTMLAttributes<HTMLSpanElement> {
  label: React.ReactNode;
}

// The bubble is hidden from assistive technology, so the wrapped control must carry its own
// accessible name. It shows on keyboard focus as well as hover.
const Tooltip = React.forwardRef<HTMLSpanElement, TooltipProps>(
  ({ label, className, children, ...props }, ref) => (
    <span
      ref={ref}
      className={cn('group/tooltip relative inline-flex', className)}
      {...props}
    >
      {children}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-full z-10 ml-2 -translate-y-1/2 rounded-md bg-foreground px-2 py-1 text-xs font-medium whitespace-nowrap text-background opacity-0 transition-opacity group-focus-within/tooltip:opacity-100 group-hover/tooltip:opacity-100"
      >
        {label}
      </span>
    </span>
  ),
);
Tooltip.displayName = 'Tooltip';

export { Tooltip };
