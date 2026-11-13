/**
 * One slicer job, start to finish. Runs inside the job's own worker in the browser, and directly
 * in Node for tests: it touches no DOM and no worker API, only what JobEnvironment gives it.
 *
 *   slice job                                   parse job
 *   ─────────                                   ─────────
 *   engineUrl, definitionUrls, models,          gcode (a file the student uploaded)
 *   settings (built by the server)                  │
 *        │                                          │
 *        ▼                                          │
 *   instantiateSlicerEngine ── a fresh engine;      │
 *        │                    it runs once           │
 *        ▼                                          │
 *   read definitions, place each model:             │
 *   stlBounds ─▶ mesh_position, measured from the   │
 *   bed centre, centres its footprint on its spot   │
 *   and stands it on z = 0                          │
 *        │                                          │
 *        ▼                                          │
 *   runCuraCli ── progress + engine memory ──▶ report()
 *        │        (the caller stops a job over its memory budget)
 *        ▼                                          │
 *   G-code bytes; the header holds the real totals  │
 *        │                                          │
 *        └──────────────────┬───────────────────────┘
 *                           ▼
 *                parseGcodeText ── progress ──▶ report()
 *                           │
 *                           ▼
 *           SliceResult { source, gcode, summary, toolpaths, violations, engineReport }
 *
 * Any failure is thrown as a SlicerJobError whose violations say what went wrong.
 */
import { instantiateSlicerEngine } from '@armada/slicer-engine';
import { parseGcodeText } from '../gcode/parse';
import { stlBounds } from '../stl';
import type { Settings, SliceProgress, SliceResult } from '../types';
import { runCuraCli } from './cura-cli';

const PRINTER_DEFINITION = 'fdmprinter.def.json';
const DECODE_CHUNK_BYTES = 1 << 20;
// The engine reports slicing progress from 0 to 1; reading its G-code is the last tenth.
const SLICING_SHARE = 0.9;

export interface SliceJobRequest {
  kind: 'slice';
  engineUrl: string;
  /** Each definition file's URL, by file name. */
  definitionUrls: Record<string, string>;
  models: { data: Blob | Uint8Array; xMm: number; yMm: number }[];
  machineSettings: Settings;
  extruderSettings: Settings;
  segmentBudget: number;
}

export interface ParseJobRequest {
  kind: 'parse';
  gcode: Blob | Uint8Array;
  segmentBudget: number;
}

export type JobRequest = SliceJobRequest | ParseJobRequest;

export interface JobEnvironment {
  readText(url: string): Promise<string>;
}

export async function runJob(
  request: JobRequest,
  environment: JobEnvironment,
  report: (progress: SliceProgress) => void,
): Promise<SliceResult> {
  return request.kind === 'slice'
    ? slice(request, environment, report)
    : parse(request, report);
}

async function slice(
  request: SliceJobRequest,
  environment: JobEnvironment,
  report: (progress: SliceProgress) => void,
): Promise<SliceResult> {
  // The engine logs to both streams; its last lines explain a failure.
  const log: string[] = [];
  const engine = await instantiateSlicerEngine(request.engineUrl, {
    print: (line) => log.push(line),
    printErr: (line) => log.push(line),
  });
  const definitions = Object.fromEntries(
    await Promise.all(
      Object.entries(request.definitionUrls).map(
        async ([name, url]) => [name, await environment.readText(url)] as const,
      ),
    ),
  );
  // The engine measures mesh positions from the bed centre, so each footprint is centred on its
  // spot by its own offset alone.
  const meshes = await Promise.all(
    request.models.map(async (model) => {
      const data = await bytes(model.data);
      const { min, max } = stlBounds(data);
      return {
        data,
        settings: {
          mesh_position_x: String(model.xMm - (min[0] + max[0]) / 2),
          mesh_position_y: String(model.yMm - (min[1] + max[1]) / 2),
          mesh_position_z: String(-min[2]),
        },
      };
    }),
  );

  const output = runCuraCli(
    engine,
    {
      definitions,
      printerDefinition: PRINTER_DEFINITION,
      global: request.machineSettings,
      extruder0: request.extruderSettings,
      meshes,
    },
    (fraction, heapBytes) =>
      report({ fraction: fraction * SLICING_SHARE, heapBytes }),
    log,
  );

  const gcode = output.gcode;
  const parsed = await parseGcodeText(decode(gcode), {
    segmentBudget: request.segmentBudget,
    onRead: (characters) =>
      report({
        fraction:
          SLICING_SHARE + (1 - SLICING_SHARE) * (characters / gcode.byteLength),
      }),
  });
  return {
    source: 'engine',
    gcode,
    ...parsed,
    violations: [],
    engineReport: output.sliceInfo,
  };
}

async function parse(
  request: ParseJobRequest,
  report: (progress: SliceProgress) => void,
): Promise<SliceResult> {
  const gcode = await bytes(request.gcode);
  const parsed = await parseGcodeText(decode(gcode), {
    segmentBudget: request.segmentBudget,
    onRead: (characters) => report({ fraction: characters / gcode.byteLength }),
  });
  return { source: 'gcode', gcode, ...parsed, violations: [] };
}

async function bytes(data: Blob | Uint8Array): Promise<Uint8Array> {
  return data instanceof Uint8Array
    ? data
    : new Uint8Array(await data.arrayBuffer());
}

/** The file as text, a chunk at a time, so a large file is never one string. */
function* decode(data: Uint8Array): Generator<string> {
  const decoder = new TextDecoder();
  for (let at = 0; at < data.byteLength; at += DECODE_CHUNK_BYTES) {
    const end = Math.min(at + DECODE_CHUNK_BYTES, data.byteLength);
    yield decoder.decode(data.subarray(at, end), {
      stream: end < data.byteLength,
    });
  }
}
