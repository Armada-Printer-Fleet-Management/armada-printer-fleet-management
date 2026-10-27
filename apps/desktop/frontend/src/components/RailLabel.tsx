import { cn, Tooltip } from '@armada/ui-kit';
import type { ReactNode } from 'react';

export const focusRing =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

export function railItemClass(expanded: boolean) {
  return cn(
    'flex items-center rounded-md text-sm font-medium',
    focusRing,
    expanded ? 'w-full gap-3 px-3 py-2' : 'size-12 justify-center',
  );
}

// Compressed, the label stays as screen-reader text and shows visually as a tooltip.
export function RailLabel({
  expanded,
  label,
  children,
}: {
  expanded: boolean;
  label: string;
  children: (labelNode: ReactNode) => ReactNode;
}) {
  if (expanded) return children(<span>{label}</span>);
  return (
    <Tooltip label={label}>
      {children(<span className="sr-only">{label}</span>)}
    </Tooltip>
  );
}
