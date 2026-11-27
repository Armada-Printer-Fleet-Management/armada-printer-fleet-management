import * as React from 'react';

import { cn } from '../lib/utils';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './table';

// Varied bar widths keep a placeholder table from reading as a solid grid.
const BAR_WIDTHS = ['w-3/4', 'w-1/2', 'w-2/3', 'w-5/6'] as const;

function barWidth(index: number): string {
  return BAR_WIDTHS[index % BAR_WIDTHS.length] ?? 'w-3/4';
}

const Skeleton = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    aria-hidden="true"
    className={cn(
      'rounded-md bg-secondary motion-safe:animate-pulse',
      className,
    )}
    {...props}
  />
));
Skeleton.displayName = 'Skeleton';

interface SkeletonStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  /** What is loading, announced once to screen readers. */
  label?: string;
}

interface SkeletonTextProps extends SkeletonStatusProps {
  lines?: number;
}

const SkeletonText = React.forwardRef<HTMLDivElement, SkeletonTextProps>(
  ({ className, lines = 3, label = 'Loading', ...props }, ref) => (
    <div
      ref={ref}
      role="status"
      className={cn('flex flex-col gap-2', className)}
      {...props}
    >
      <span className="sr-only">{label}</span>
      {Array.from({ length: lines }, (_, line) => (
        <Skeleton
          key={line}
          className={cn(
            'h-4',
            line === lines - 1 && lines > 1 ? 'w-3/5' : 'w-full',
          )}
        />
      ))}
    </div>
  ),
);
SkeletonText.displayName = 'SkeletonText';

interface TableSkeletonRowsProps {
  rows: number;
  columns: number;
}

/** Placeholder rows, for inside a TableBody: alone, or under real rows while more load. */
function TableSkeletonRows({ rows, columns }: TableSkeletonRowsProps) {
  return Array.from({ length: rows }, (_, row) => (
    <TableRow key={row} aria-hidden="true">
      {Array.from({ length: columns }, (_, column) => (
        <TableCell key={column}>
          <Skeleton className={cn('h-4', barWidth(row + column))} />
        </TableCell>
      ))}
    </TableRow>
  ));
}

interface TableSkeletonProps extends SkeletonStatusProps {
  columns: number;
  rows?: number;
  /** Real column names for the header row; bars when left out. */
  headers?: readonly string[];
}

const TableSkeleton = React.forwardRef<HTMLDivElement, TableSkeletonProps>(
  (
    { className, columns, rows = 5, headers, label = 'Loading', ...props },
    ref,
  ) => (
    <div ref={ref} role="status" className={className} {...props}>
      <span className="sr-only">{label}</span>
      <Table aria-hidden="true">
        <TableHeader>
          <TableRow>
            {Array.from({ length: columns }, (_, column) => (
              <TableHead key={column}>
                {headers?.[column] ?? (
                  <Skeleton className={cn('h-4', barWidth(column))} />
                )}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableSkeletonRows rows={rows} columns={columns} />
        </TableBody>
      </Table>
    </div>
  ),
);
TableSkeleton.displayName = 'TableSkeleton';

export {
  Skeleton,
  SkeletonText,
  TableSkeleton,
  TableSkeletonRows,
  type SkeletonTextProps,
  type TableSkeletonProps,
  type TableSkeletonRowsProps,
};
