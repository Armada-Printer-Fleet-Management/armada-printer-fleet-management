import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import type { Plugin } from 'vite';

const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const ORGANIZATION = fileURLToPath(
  new URL('./organization.json', import.meta.url),
);
const MODULE = 'virtual:legal-documents';
const RESOLVED = `\0${MODULE}`;

interface LegalDocumentEntry {
  path: string;
  sha256: string;
}

function entries(): LegalDocumentEntry[] {
  const organization = JSON.parse(readFileSync(ORGANIZATION, 'utf8')) as {
    legalDocuments?: LegalDocumentEntry[];
  };
  return organization.legalDocuments ?? [];
}

function sha256(path: string): string {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

/**
 * Refuses to build when a legal document no longer matches its SHA-256 in organization.json, the
 * same check as scripts/check_legal_documents.py. Also provides `virtual:legal-documents`: each
 * document's text, keyed by its SHA-256, so a client shows exactly the version the server asks for.
 */
export function legalDocuments(): Plugin {
  return {
    name: 'armada-legal-documents',
    buildStart() {
      const problems = entries().flatMap(({ path, sha256: pinned }) => {
        const file = `${ROOT}${path}`;
        if (!existsSync(file)) return [`${path}: missing`];
        const actual = sha256(file);
        return actual === pinned
          ? []
          : [`${path}: changed; its SHA-256 is now ${actual}`];
      });
      if (problems.length > 0) {
        this.error(
          `Legal documents do not match packages/organization-info/organization.json:\n  ${problems.join('\n  ')}\n` +
            'For each changed document, set effectiveDate to the day the new text takes effect and ' +
            'sha256 to the value above, so users are asked to accept it again.',
        );
      }
    },
    resolveId(id) {
      return id === MODULE ? RESOLVED : undefined;
    },
    load(id) {
      if (id !== RESOLVED) return undefined;
      const texts = Object.fromEntries(
        entries().map(({ path, sha256: pinned }) => [
          pinned,
          readFileSync(`${ROOT}${path}`, 'utf8'),
        ]),
      );
      return `export default ${JSON.stringify(texts)};`;
    },
  };
}
