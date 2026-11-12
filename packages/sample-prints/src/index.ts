import benchyArmada from '../bundled/benchy-armada/print.json';
import { parsePrint, type SamplePrint, type SamplePrintFile } from './manifest';

export type {
  SamplePrint,
  SamplePrintFile,
  SamplePrintFileKind,
  SamplePrintLicense,
  SamplePrintPlacement,
} from './manifest';

/** The folder the apps serve bundled prints from, beside the app. */
export const SAMPLE_PRINTS_FOLDER = 'sample-prints';

// Every folder under bundled/ is listed here, so the apps can import its manifest.
const BUNDLED: readonly SamplePrint[] = [
  parsePrint('benchy-armada', benchyArmada),
];

/** The prints that ship inside the apps. Test prints are never listed. */
export function bundledPrints(): readonly SamplePrint[] {
  return BUNDLED;
}

export function bundledPrint(id: string): SamplePrint | undefined {
  return BUNDLED.find((print) => print.id === id);
}

/**
 * Where a bundled print's file is served: `<base>/sample-prints/<print id>/<file name>`. Main thread
 * only, because it resolves against the page.
 */
export function samplePrintUrl(
  base: string,
  print: SamplePrint,
  file: SamplePrintFile,
): URL {
  return new URL(
    `${SAMPLE_PRINTS_FOLDER}/${print.id}/${encodeURIComponent(file.name)}`,
    new URL(base, document.baseURI),
  );
}
