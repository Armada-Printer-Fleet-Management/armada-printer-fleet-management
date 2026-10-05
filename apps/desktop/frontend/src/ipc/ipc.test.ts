/// <reference types="vite/client" />
// Every export under ipc/ must be a function that decodes its IPC reply through protobuf.

import { isMessage } from '@bufbuild/protobuf';
import { afterAll, beforeAll, expect, it, vi } from 'vitest';

const modules = import.meta.glob<Record<string, unknown>>(
  ['./**/*.ts', '!./**/*.test.ts', '!./**/*.d.ts', '!./pywebview.ts'],
  { eager: true },
);

const ipcExports = Object.entries(modules).flatMap(([path, module]) =>
  Object.entries(module).map(([name, value]) => ({
    id: `${path} ${name}`,
    value,
  })),
);

function isCallable(value: unknown): value is () => unknown {
  return typeof value === 'function';
}

const ipcStub = new Proxy(
  {},
  { get: () => new Proxy({}, { get: () => () => Promise.resolve({}) }) },
);

beforeAll(() => {
  vi.stubGlobal('window', { pywebview: { api: ipcStub } });
});

afterAll(() => {
  vi.unstubAllGlobals();
});

it('finds IPC modules and their exports', () => {
  expect(Object.keys(modules).length).toBeGreaterThan(0);
  expect(ipcExports.length).toBeGreaterThan(0);
});

it.each(ipcExports)('$id returns a protobuf message', async ({ value }) => {
  expect(isCallable(value), 'IPC modules may only export functions').toBe(true);
  if (!isCallable(value)) return;
  expect(
    isMessage(await value()),
    'must decode the IPC reply with fromJson',
  ).toBe(true);
});
