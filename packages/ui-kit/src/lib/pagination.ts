/** Where a table page sits within the rows loaded so far. */
export interface PageWindow {
  /** Index of the page's first row. */
  start: number;
  /** One past the page's last loaded row. */
  end: number;
  hasPrevious: boolean;
  hasNext: boolean;
  /** The page reaches past the loaded rows and the source has more to give. */
  needsLoad: boolean;
}

export interface PageWindowInput {
  /** 1-based. */
  page: number;
  pageSize: number;
  loadedCount: number;
  /** The source can still load more rows. */
  hasMore: boolean;
}

/** Table paging over loaded rows, independent of however the source loads them. */
export function pageWindow({
  page,
  pageSize,
  loadedCount,
  hasMore,
}: PageWindowInput): PageWindow {
  const start = (page - 1) * pageSize;
  const pageEnd = start + pageSize;
  return {
    start,
    end: Math.min(pageEnd, loadedCount),
    hasPrevious: page > 1,
    hasNext: loadedCount > pageEnd || hasMore,
    needsLoad: pageEnd > loadedCount && hasMore,
  };
}
