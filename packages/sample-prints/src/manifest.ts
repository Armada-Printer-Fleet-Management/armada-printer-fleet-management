/** What a file in a print folder is for. */
export type SamplePrintFileKind = 'model' | 'gcode';

export interface SamplePrintFile {
  name: string;
  kind: SamplePrintFileKind;
  sizeBytes: number;
  sha256: string;
  /** For G-code: the printer model it was sliced for. */
  printer?: string;
  /** For G-code: the slicer and settings that produced it, so it can be regenerated. */
  generator?: string;
}

export interface SamplePrintLicense {
  /** SPDX identifier, such as CC0-1.0. */
  spdx: string;
  /** Where the original was taken from. */
  source: string;
  attribution: string;
}

/** One copy of a model file placed on the bed, its footprint centred this far from the bed centre. */
export interface SamplePrintPlacement {
  file: string;
  xMm: number;
  yMm: number;
}

/** A print folder's `print.json`, plus its folder name as `id`. */
export interface SamplePrint {
  id: string;
  title: string;
  description: string;
  license: SamplePrintLicense;
  files: SamplePrintFile[];
  arrangement?: SamplePrintPlacement[];
}

const FILE_KINDS: readonly string[] = [
  'model',
  'gcode',
] satisfies SamplePrintFileKind[];

/** Checks a parsed `print.json` against the manifest shape, naming the first field that is wrong. */
export function parsePrint(id: string, json: unknown): SamplePrint {
  const where = `${id}/print.json`;
  const root = record(json, where);
  const license = record(root.license, `${where} license`);
  const files = array(root.files, `${where} files`).map((value, index) => {
    const at = `${where} files[${index}]`;
    const file = record(value, at);
    const kind = text(file.kind, `${at}.kind`);
    if (!FILE_KINDS.includes(kind)) {
      throw new Error(`${at}.kind must be one of ${FILE_KINDS.join(', ')}`);
    }
    return {
      name: text(file.name, `${at}.name`),
      kind: kind as SamplePrintFileKind,
      sizeBytes: count(file.sizeBytes, `${at}.sizeBytes`),
      sha256: sha256(file.sha256, `${at}.sha256`),
      ...optionalText(file, 'printer', at),
      ...optionalText(file, 'generator', at),
    };
  });
  const names = new Set(files.map((file) => file.name));
  const arrangement =
    root.arrangement === undefined
      ? undefined
      : array(root.arrangement, `${where} arrangement`).map((value, index) => {
          const at = `${where} arrangement[${index}]`;
          const placement = record(value, at);
          const file = text(placement.file, `${at}.file`);
          if (!names.has(file)) {
            throw new Error(`${at}.file names ${file}, which is not in files`);
          }
          return {
            file,
            xMm: finite(placement.xMm, `${at}.xMm`),
            yMm: finite(placement.yMm, `${at}.yMm`),
          };
        });
  return {
    id,
    title: text(root.title, `${where} title`),
    description: text(root.description, `${where} description`),
    license: {
      spdx: text(license.spdx, `${where} license.spdx`),
      source: text(license.source, `${where} license.source`),
      attribution: text(license.attribution, `${where} license.attribution`),
    },
    files,
    ...(arrangement ? { arrangement } : {}),
  };
}

function record(value: unknown, at: string): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error(`${at} must be an object`);
  }
  return value as Record<string, unknown>;
}

function array(value: unknown, at: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`${at} must be an array`);
  }
  return value;
}

function text(value: unknown, at: string): string {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`${at} must be a non-empty string`);
  }
  return value;
}

function optionalText(
  source: Record<string, unknown>,
  key: 'printer' | 'generator',
  at: string,
): { printer?: string; generator?: string } {
  return source[key] === undefined
    ? {}
    : { [key]: text(source[key], `${at}.${key}`) };
}

function finite(value: unknown, at: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`${at} must be a number`);
  }
  return value;
}

function count(value: unknown, at: string): number {
  const number = finite(value, at);
  if (!Number.isInteger(number) || number <= 0) {
    throw new Error(`${at} must be a positive whole number`);
  }
  return number;
}

function sha256(value: unknown, at: string): string {
  const hash = text(value, at);
  if (!/^[0-9a-f]{64}$/.test(hash)) {
    throw new Error(`${at} must be a lowercase hex SHA-256`);
  }
  return hash;
}
