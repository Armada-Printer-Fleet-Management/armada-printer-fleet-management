import { expect, it } from 'vitest';

import { pageWindow } from './pagination';

it('bounds a page by its size, clamped to the rows loaded', () => {
  const second = pageWindow({
    page: 2,
    pageSize: 10,
    loadedCount: 25,
    hasMore: false,
  });
  expect([second.start, second.end]).toEqual([10, 20]);

  const third = pageWindow({
    page: 3,
    pageSize: 10,
    loadedCount: 25,
    hasMore: false,
  });
  expect([third.start, third.end]).toEqual([20, 25]);
});

it('has a previous page from page two on', () => {
  const at = (page: number) =>
    pageWindow({ page, pageSize: 10, loadedCount: 25, hasMore: false });

  expect(at(1).hasPrevious).toBe(false);
  expect(at(2).hasPrevious).toBe(true);
});

it('has a next page when rows are loaded past it or the source has more', () => {
  const at = (page: number, hasMore: boolean) =>
    pageWindow({ page, pageSize: 10, loadedCount: 25, hasMore }).hasNext;

  expect(at(2, false)).toBe(true);
  expect(at(3, true)).toBe(true);
  expect(at(3, false)).toBe(false);
});

it('needs a load only past the loaded rows while the source has more', () => {
  const needsLoad = (page: number, hasMore: boolean) =>
    pageWindow({ page, pageSize: 10, loadedCount: 25, hasMore }).needsLoad;

  expect(needsLoad(3, true)).toBe(true);
  expect(needsLoad(3, false)).toBe(false);
  expect(needsLoad(2, true)).toBe(false);
});
