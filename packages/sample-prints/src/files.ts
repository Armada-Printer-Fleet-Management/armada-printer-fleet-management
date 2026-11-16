// Node only: reads print folders from disk for the Vite plugin and the tests.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parsePrint, type SamplePrint } from './manifest';

export const PACKAGE_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const BUNDLED_DIR = join(PACKAGE_ROOT, 'bundled');
export const TEST_DIR = join(PACKAGE_ROOT, 'test');

const LFS_POINTER = 'version https://git-lfs.github.com/spec/v1';

/** Every print folder directly under `dir`, parsed from its `print.json`. */
export function readPrints(dir: string): SamplePrint[] {
  if (!existsSync(dir)) {
    return [];
  }
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) =>
      parsePrint(
        entry.name,
        JSON.parse(readFileSync(join(dir, entry.name, 'print.json'), 'utf8')),
      ),
    );
}

/** True when the file is still a Git LFS pointer, meaning `git lfs pull` has not been run. */
export function isLfsPointer(path: string): boolean {
  const head = readFileSync(path).subarray(0, LFS_POINTER.length);
  return head.toString('utf8') === LFS_POINTER;
}
