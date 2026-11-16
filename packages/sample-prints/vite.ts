import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Plugin } from 'vite';
import { BUNDLED_DIR, isLfsPointer, readPrints } from './src/files';
import { SAMPLE_PRINTS_FOLDER } from './src/index';

/** Every bundled file as `<print id>/<file name>` beside its path on disk. Never includes test/. */
export function bundledFiles(): { servedAs: string; path: string }[] {
  return readPrints(BUNDLED_DIR).flatMap((print) =>
    print.files.map((file) => ({
      servedAs: `${print.id}/${file.name}`,
      path: join(BUNDLED_DIR, print.id, file.name),
    })),
  );
}

/**
 * Serves the bundled sample prints in development and copies them to <outDir>/sample-prints/ in a
 * build. Only files a bundled print.json lists are shipped, so test prints never reach a build.
 */
export function samplePrints(): Plugin {
  return {
    name: 'armada-sample-prints',
    buildStart() {
      for (const { servedAs, path } of bundledFiles()) {
        if (!existsSync(path)) {
          this.error(
            `Sample print file ${servedAs} is listed in print.json but missing.`,
          );
        }
        if (isLfsPointer(path)) {
          this.error(
            `Sample print file ${servedAs} is a Git LFS pointer. Run: git lfs install && git lfs pull`,
          );
        }
      }
    },
    configureServer(server) {
      const served = new Map(
        bundledFiles().map((file) => [file.servedAs, file.path]),
      );
      server.middlewares.use(
        `/${SAMPLE_PRINTS_FOLDER}`,
        (request, response, next) => {
          const name = decodeURIComponent(
            (request.url ?? '').split('?')[0]?.replace(/^\//, '') ?? '',
          );
          const path = served.get(name);
          if (!path) {
            next();
            return;
          }
          response.setHeader('Content-Type', 'application/octet-stream');
          response.end(readFileSync(path));
        },
      );
    },
    generateBundle() {
      for (const { servedAs, path } of bundledFiles()) {
        this.emitFile({
          type: 'asset',
          fileName: `${SAMPLE_PRINTS_FOLDER}/${servedAs}`,
          source: readFileSync(path),
        });
      }
    },
  };
}
