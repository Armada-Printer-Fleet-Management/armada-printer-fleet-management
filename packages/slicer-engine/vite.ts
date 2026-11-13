import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Plugin } from 'vite';

const GEN = fileURLToPath(new URL('./gen', import.meta.url));
const FOLDER = 'slicer-engine';
const RUNTIME_FILES: Record<string, string> = {
  'CuraEngine.js': 'text/javascript',
  'fdmprinter.def.json': 'application/json',
  'fdmextruder.def.json': 'application/json',
  'LICENSE-CuraEngine.txt': 'text/plain',
  'LICENSE-Cura-definitions.txt': 'text/plain',
  'NOTICE.txt': 'text/plain',
};

/**
 * Serves the fetched engine in development and copies it, unhashed, to <outDir>/slicer-engine/ in a
 * build. It stays a separate file the app imports at run time, so it can be replaced after a build
 * (license requirement).
 */
export function slicerEngine(): Plugin {
  return {
    name: 'armada-slicer-engine',
    buildStart() {
      const missing = Object.keys(RUNTIME_FILES).filter(
        (name) => !existsSync(join(GEN, name)),
      );
      if (missing.length > 0) {
        this.error(
          `The slicer engine has not been fetched (missing ${missing.join(', ')}). ` +
            'Run: python scripts/fetch_slicer_engine.py',
        );
      }
    },
    configureServer(server) {
      server.middlewares.use(`/${FOLDER}`, (request, response, next) => {
        const name =
          (request.url ?? '').split('?')[0]?.replace(/^\//, '') ?? '';
        const type = RUNTIME_FILES[name];
        if (!type) {
          next();
          return;
        }
        response.setHeader('Content-Type', type);
        response.end(readFileSync(join(GEN, name)));
      });
    },
    generateBundle() {
      for (const name of Object.keys(RUNTIME_FILES)) {
        this.emitFile({
          type: 'asset',
          fileName: `${FOLDER}/${name}`,
          source: readFileSync(join(GEN, name)),
        });
      }
    },
  };
}
