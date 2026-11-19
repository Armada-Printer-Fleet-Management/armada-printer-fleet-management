// @vitest-environment node
import { join, relative, sep } from 'node:path';
import { expect, test } from 'vitest';
import { bundledFiles } from '../vite';
import { BUNDLED_DIR, PACKAGE_ROOT, readPrints } from './files';

test('only files under bundled/ are shipped, never test/', () => {
  const folders = bundledFiles().map(
    ({ path }) => relative(PACKAGE_ROOT, path).split(sep)[0],
  );

  expect(folders.length).toBeGreaterThan(0);
  expect(new Set(folders)).toEqual(new Set(['bundled']));
});

test('every file a bundled print.json lists is shipped as <id>/<name>', () => {
  const listed = readPrints(BUNDLED_DIR).flatMap((print) =>
    print.files.map((file) => ({
      servedAs: `${print.id}/${file.name}`,
      path: join(BUNDLED_DIR, print.id, file.name),
    })),
  );

  expect(bundledFiles()).toEqual(expect.arrayContaining(listed));
  expect(bundledFiles()).toHaveLength(listed.length);
});
