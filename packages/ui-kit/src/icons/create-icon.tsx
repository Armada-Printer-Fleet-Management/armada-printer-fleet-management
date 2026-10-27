import * as React from 'react';

import { cn } from '../lib/utils';

export type IconProps = React.ComponentPropsWithoutRef<'svg'>;

// Icons are decorative by default: the control they sit in carries the accessible name.
export function createIcon(displayName: string, shapes: React.ReactNode) {
  const Icon = React.forwardRef<SVGSVGElement, IconProps>(
    ({ className, ...props }, ref) => (
      <svg
        ref={ref}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className={cn('size-6 shrink-0', className)}
        {...props}
      >
        {shapes}
      </svg>
    ),
  );
  Icon.displayName = displayName;
  return Icon;
}
