import * as React from 'react';

import { cn } from '../lib/utils';

export interface PaginationProps extends React.HTMLAttributes<HTMLElement> {
  /** 1-based. */
  page: number;
  pageSize: number;
  pageSizeOptions: readonly number[];
  /** 1-based index of the first row shown, and of the last. */
  rangeStart: number;
  rangeEnd: number;
  loadedCount: number;
  /** More rows exist than are loaded, so the count is a lower bound. */
  hasMore: boolean;
  hasPrevious: boolean;
  hasNext: boolean;
  /** A page is loading: the controls wait for it. */
  busy?: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onPageSizeChange: (pageSize: number) => void;
}

const BUTTON_CLASS =
  'inline-flex h-9 items-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50';

const Pagination = React.forwardRef<HTMLElement, PaginationProps>(
  (
    {
      className,
      page,
      pageSize,
      pageSizeOptions,
      rangeStart,
      rangeEnd,
      loadedCount,
      hasMore,
      hasPrevious,
      hasNext,
      busy = false,
      onPrevious,
      onNext,
      onPageSizeChange,
      ...props
    },
    ref,
  ) => {
    const sizeId = React.useId();
    return (
      <nav
        ref={ref}
        aria-label="Pagination"
        aria-busy={busy}
        className={cn(
          'flex flex-wrap items-center justify-between gap-4 text-sm',
          className,
        )}
        {...props}
      >
        <div className="flex items-center gap-2">
          <label htmlFor={sizeId}>Rows per page</label>
          <select
            id={sizeId}
            value={pageSize}
            disabled={busy}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            className="h-9 rounded-lg border border-input bg-card px-2 text-card-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:opacity-50"
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <p className="text-muted-foreground">
          Showing {rangeStart}–{rangeEnd} of {loadedCount}
          {hasMore ? '+' : ''}
        </p>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className={BUTTON_CLASS}
            disabled={busy || !hasPrevious}
            onClick={onPrevious}
          >
            Previous
          </button>
          <span aria-current="page">Page {page}</span>
          <button
            type="button"
            className={BUTTON_CLASS}
            disabled={busy || !hasNext}
            onClick={onNext}
          >
            Next
          </button>
        </div>
      </nav>
    );
  },
);
Pagination.displayName = 'Pagination';

export { Pagination };
