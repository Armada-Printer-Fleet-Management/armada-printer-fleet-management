/**
 * Writes the G-code test prints in packages/sample-prints/test/: each model sliced for one printer
 * type with the pinned engine and the dev server's slice profile, the summary the parser reads back
 * from that G-code, and a print.json with each file's real size and SHA-256.
 *
 *   dev server ── ListPrinterTypes, GetSliceSettings ──▶ the printer type's settings
 *                                                              │
 *   each print's model ──────────────────────────────┐         │
 *   slicer-engine/gen/ (the pinned engine) ──────────┴──▶ runJob, in Node
 *                                                              │
 *                 test/<print>/ <model>, <model>_MK4S.gcode, ◀─┘
 *                               expected-summary.json, print.json
 *
 * Tests compare the parser against each expected-summary.json, so rerun this after changing the
 * engine, the slice profile or the parser, and review the summaries' diff.
 */
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { toJson } from '@bufbuild/protobuf';
import { SLICER_DEFINITION_FILES } from '@armada/slicer-engine';
import { SliceSummarySchema } from '../src/gen/print_preparation/slicing/v1/slice_summary_pb';
import { DEFAULT_SEGMENT_BUDGET } from '../src/slicing/jobs';
import type { Settings } from '../src/slicing/types';
import { runJob } from '../src/slicing/worker/run-job';

const PRINTER_MODEL = 'Original Prusa MK4S';
const PRINTER_SUFFIX = 'MK4S';
export const DEFAULT_SERVER_URL = 'http://localhost:8000/api';

const PACKAGES = fileURLToPath(new URL('../../', import.meta.url));
const ENGINE_DIR = join(PACKAGES, 'slicer-engine', 'gen');
const PRINTS_DIR = join(PACKAGES, 'sample-prints');

interface TestPrint {
  id: string;
  /** The model to slice, relative to packages/sample-prints. Copied into the print's folder. */
  model: string;
  title: string;
  description: string;
  license: { spdx: string; source: string; attribution: string };
}

const BENCHY_LICENSE = {
  spdx: 'CC0-1.0',
  source: 'https://github.com/CreativeTools/3DBenchy',
  attribution: '#3DBenchy by CreativeTools, 3DBenchy.com',
};

const PRINTS: TestPrint[] = [
  {
    id: 'benchy-mk4s',
    model: 'bundled/benchy-armada/3DBenchy.stl',
    title: `Benchy sliced for the ${PRINTER_MODEL}`,
    description:
      'One #3DBenchy at the bed centre and its G-code. The happy path for slicing and parsing tests.',
    license: BENCHY_LICENSE,
  },
  {
    id: 'voron-cube',
    model: 'test/voron-cube/Voron_Design_Cube_v7.stl',
    title: 'Voron Design Cube v7',
    description:
      "The Voron project's calibration cube and its G-code: walls, embossed text, holes and chamfers.",
    license: {
      spdx: 'GPL-3.0-only',
      source:
        'https://github.com/VoronDesign/Voron-2/blob/7b32e405f0719881cca782500c822e01e3b16bf2/STLs/Test_Prints/Voron_Design_Cube_v7.stl',
      attribution: 'Voron Design Cube by the Voron Design team',
    },
  },
  {
    id: 'extruder-idler',
    model: 'test/extruder-idler/extruder_idler.stl',
    title: 'Extruder idler',
    description:
      "A real printer part and its G-code: holes, curves and infill. Converted to binary STL, unchanged, from PrusaSlicer's test OBJ.",
    license: {
      spdx: 'AGPL-3.0-only',
      source:
        'https://github.com/prusa3d/PrusaSlicer/blob/e6c85c50dcc56f9968a61dfdd7a3b695e1004037/tests/data/extruder_idler.obj',
      attribution: 'PrusaSlicer test data by Prusa Research',
    },
  },
];

export async function main(serverUrl: string): Promise<void> {
  const settings = await sliceSettings(serverUrl);
  for (const print of PRINTS) {
    await generate(print, settings);
  }
}

async function generate(
  print: TestPrint,
  settings: { machineSettings: Settings; extruderSettings: Settings },
): Promise<void> {
  const outDir = join(PRINTS_DIR, 'test', print.id);
  const modelFile = basename(print.model);
  const gcodeFile = `${modelFile.replace(/\.[^.]+$/, '')}_${PRINTER_SUFFIX}.gcode`;
  const model = readFileSync(join(PRINTS_DIR, print.model));
  const result = await runJob(
    {
      kind: 'slice',
      engineUrl: pathToFileURL(join(ENGINE_DIR, 'CuraEngine.js')).href,
      definitionUrls: Object.fromEntries(
        SLICER_DEFINITION_FILES.map((name) => [name, join(ENGINE_DIR, name)]),
      ),
      models: [{ data: new Uint8Array(model), xMm: 0, yMm: 0 }],
      ...settings,
      segmentBudget: DEFAULT_SEGMENT_BUDGET,
    },
    { readText: (path) => Promise.resolve(readFileSync(path, 'utf8')) },
    () => undefined,
  );

  mkdirSync(outDir, { recursive: true });
  const modelCopy = join(outDir, modelFile);
  if (join(PRINTS_DIR, print.model) !== modelCopy) {
    copyFileSync(join(PRINTS_DIR, print.model), modelCopy);
  }
  writeFileSync(join(outDir, gcodeFile), result.gcode);
  writeJson(
    outDir,
    'expected-summary.json',
    toJson(SliceSummarySchema, result.summary),
  );
  writeJson(outDir, 'print.json', {
    title: print.title,
    description: print.description,
    license: print.license,
    files: [
      describeFile(outDir, modelFile, 'model'),
      {
        ...describeFile(outDir, gcodeFile, 'gcode'),
        printer: PRINTER_MODEL,
        generator: `${result.summary.slicer}, the development server's slice profile, by packages/slicer/scripts/generate-test-gcode.ts`,
      },
    ],
  });
  console.log(
    `Wrote test/${print.id}: ${result.summary.layerCount} layers, ${result.gcode.byteLength} bytes of G-code`,
  );
}

/** The engine settings the server builds for the printer type, as a browser client gets them. */
async function sliceSettings(
  serverUrl: string,
): Promise<{ machineSettings: Settings; extruderSettings: Settings }> {
  const types = field(
    await call(serverUrl, 'server.v1.PrinterService/ListPrinterTypes', {}),
    'printerTypes',
  );
  const listed: unknown[] = Array.isArray(types) ? types : [];
  const printerType = listed.find(
    (type) => field(type, 'model') === PRINTER_MODEL,
  );
  if (printerType === undefined) {
    throw new Error(`The server lists no ${PRINTER_MODEL}.`);
  }
  const response = await call(
    serverUrl,
    'server.v1.SlicerConfigurationService/GetSliceSettings',
    { printerType },
  );
  const settings = field(response, 'sliceSettings');
  return {
    machineSettings: stringRecord(field(settings, 'machineSettings')),
    extruderSettings: stringRecord(field(settings, 'extruderSettings')),
  };
}

async function call(
  serverUrl: string,
  method: string,
  body: unknown,
): Promise<unknown> {
  const url = `${serverUrl}/${method}`;
  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(
      `Could not reach ${url}. Start the dev stack with python scripts/compose_run.py dev.`,
      { cause: error },
    );
  }
  if (!response.ok) {
    throw new Error(
      `${method} answered ${response.status}: ${await response.text()}`,
    );
  }
  return response.json();
}

function field(value: unknown, name: string): unknown {
  return typeof value === 'object' && value !== null
    ? (value as Record<string, unknown>)[name]
    : undefined;
}

function stringRecord(value: unknown): Settings {
  if (typeof value !== 'object' || value === null) {
    throw new Error('The server sent no slice settings.');
  }
  return Object.fromEntries(
    Object.entries(value).filter(
      (entry): entry is [string, string] => typeof entry[1] === 'string',
    ),
  );
}

function describeFile(dir: string, name: string, kind: 'model' | 'gcode') {
  const data = readFileSync(join(dir, name));
  return {
    name,
    kind,
    sizeBytes: data.byteLength,
    sha256: createHash('sha256').update(data).digest('hex'),
  };
}

function writeJson(dir: string, name: string, value: unknown): void {
  writeFileSync(join(dir, name), `${JSON.stringify(value, null, 2)}\n`);
}
