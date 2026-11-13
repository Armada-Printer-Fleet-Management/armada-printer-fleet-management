/**
 * The engine adapter: the only file that knows CuraEngine's JavaScript API is its command line.
 * Replacing that API, for example with a typed binding from the sister repository, means
 * replacing this file and nothing else.
 *
 *   CuraJob { definitions, global, extruder0, meshes }
 *        │
 *        ▼
 *   register four global callbacks ── the engine evaluates globalThis["<name>"](value),
 *        │   <id>_progress      ◀── a number, 0 to 1 ──▶ onProgress(fraction, engine memory)
 *        │   <id>_slice_info    ◀── its JSON report of the slice
 *        │   <id>_engine_info   ◀── its version (ignored)
 *        │   <id>_gcode_header  ◀── the header again (ignored; the file already has it)
 *        ▼
 *   write into the engine's in-memory file system (it shares the engine's 4 GB memory):
 *        /defs/fdmprinter.def.json, /defs/fdmextruder.def.json
 *        /in/model_<i>.stl
 *        │
 *        ▼
 *   callMain([ 'slice', '-j', definition,     machine settings:   -s key=value ...
 *              '-e0',                          extruder settings:  -s key=value ...
 *                 └─ every limit_to_extruder setting too, which the engine reads only here:
 *                    the job's extruder value, else its machine value, else the default
 *              '-l', model, -s mesh_position_*, ...  one per model
 *              '-o', '/out/out.gcode', callback names ])
 *        │
 *        ├── exit 0 ──────▶ read /out/out.gcode ──▶ CuraOutput { gcode, sliceInfo }
 *        ├── exit ≠ 0 ────▶ SlicerJobError ENGINE_FAILED (last lines of stderr)
 *        └── abort ───────▶ SlicerJobError OUT_OF_MEMORY or ENGINE_FAILED
 *        │
 *        ▼
 *   remove the global callbacks, whatever happened
 */
import type { SlicerEngine } from '@armada/slicer-engine';
import { SlicerViolationCode } from '../../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../../validation/violations';
import type { Settings } from '../types';

/** The parts of the engine module used here. Its generated types call them `any`. */
interface CuraModule {
  callMain(args: string[]): number;
  FS: {
    mkdirTree(path: string): void;
    writeFile(path: string, data: string | Uint8Array): void;
    readFile(path: string): Uint8Array;
  };
  HEAP8: Int8Array;
}

export interface CuraJob {
  /** Definition file contents by file name; the first named in printerDefinition is loaded. */
  definitions: Record<string, string>;
  printerDefinition: string;
  global: Settings;
  extruder0: Settings;
  meshes: { data: Uint8Array; settings: Settings }[];
}

export interface CuraOutput {
  gcode: Uint8Array;
  /** The engine's report of the slice, as it gave it. */
  sliceInfo?: unknown;
}

/** The parts of a CuraEngine definition file read here. */
interface DefinitionNode {
  default_value?: unknown;
  limit_to_extruder?: string;
  settings?: Record<string, DefinitionNode>;
  children?: Record<string, DefinitionNode>;
}

let callbackSerial = 0;

/**
 * Slices once. The engine runs its command line once per instance, so each job brings a fresh
 * engine. `errors` collects what the engine prints to stderr.
 */
export function runCuraCli(
  engine: SlicerEngine,
  job: CuraJob,
  onProgress: (fraction: number, heapBytes: number) => void,
  errors: readonly string[],
): CuraOutput {
  // The generated typings declare callMain, FS and HEAP8 as any; this narrows them to what is used.
  const cura = engine as unknown as CuraModule;
  const output: CuraOutput = { gcode: new Uint8Array() };

  // The engine reports progress by evaluating `globalThis["<name>"](value)`, so the callbacks
  // must be globals. A unique name per job keeps two engines in one realm apart.
  const id = `armada_cura_${++callbackSerial}`;
  const scope = globalThis as unknown as Record<string, unknown>;
  const callbacks = {
    [`${id}_progress`]: (fraction: number) =>
      onProgress(fraction, cura.HEAP8.buffer.byteLength),
    [`${id}_slice_info`]: (info: unknown) => {
      output.sliceInfo = info;
    },
    [`${id}_engine_info`]: () => undefined,
    // The file it writes already carries the same header, totals included.
    [`${id}_gcode_header`]: () => undefined,
  };
  Object.assign(scope, callbacks);

  try {
    cura.FS.mkdirTree('/defs');
    cura.FS.mkdirTree('/in');
    cura.FS.mkdirTree('/out');
    for (const [name, text] of Object.entries(job.definitions)) {
      cura.FS.writeFile(`/defs/${name}`, text);
    }
    const meshArgs = job.meshes.flatMap((mesh, index) => {
      const path = `/in/model_${index}.stl`;
      cura.FS.writeFile(path, mesh.data);
      return ['-l', path, ...settingArgs(mesh.settings)];
    });

    const printerDefinition = job.definitions[job.printerDefinition] ?? '{}';
    const args = [
      'slice',
      '-j',
      `/defs/${job.printerDefinition}`,
      ...settingArgs(job.global),
      '-e0',
      ...settingArgs(extruderTrainSettings(printerDefinition, job)),
      ...meshArgs,
      '-o',
      '/out/out.gcode',
      // Every callback must be named: the engine calls each one it was not given as well.
      '--progress_cb',
      `${id}_progress`,
      '--slice_info_cb',
      `${id}_slice_info`,
      '--engine_info_cb',
      `${id}_engine_info`,
      '--gcode_header_cb',
      `${id}_gcode_header`,
    ];

    let code: number;
    try {
      code = cura.callMain(args);
    } catch (error: unknown) {
      throw engineAborted(error, errors);
    }
    if (code !== 0) {
      throw new SlicerJobError([
        slicerViolation(
          SlicerViolationCode.ENGINE_FAILED,
          `The slicer stopped without slicing (exit code ${code}). ${lastLines(errors)}`.trim(),
        ),
      ]);
    }
    output.gcode = cura.FS.readFile('/out/out.gcode');
    return output;
  } finally {
    for (const name of Object.keys(callbacks)) {
      Reflect.deleteProperty(scope, name);
    }
  }
}

/**
 * The extruder's settings as the command line needs them. A setting the definition marks
 * limit_to_extruder is read from the extruder alone, never from the machine settings, and the
 * command line gives the extruder no defaults for it. So each one is set here: from the job's
 * extruder settings, else its machine settings, else the definition's default.
 */
function extruderTrainSettings(
  printerDefinition: string,
  job: CuraJob,
): Settings {
  const scoped: Settings = {};
  collectExtruderScoped(
    JSON.parse(printerDefinition) as DefinitionNode,
    scoped,
  );
  for (const key of Object.keys(scoped)) {
    const fromMachine = job.global[key];
    if (fromMachine !== undefined) {
      scoped[key] = fromMachine;
    }
  }
  return { ...scoped, ...job.extruder0 };
}

function collectExtruderScoped(node: DefinitionNode, into: Settings): void {
  for (const [key, child] of Object.entries({
    ...node.settings,
    ...node.children,
  })) {
    if (
      child.limit_to_extruder !== undefined &&
      child.default_value !== undefined
    ) {
      into[key] = engineValue(child.default_value);
    }
    collectExtruderScoped(child, into);
  }
}

/** A definition's default as the engine reads it: lists and objects as JSON. */
function engineValue(value: unknown): string {
  return typeof value === 'object' && value !== null
    ? JSON.stringify(value)
    : String(value);
}

function settingArgs(settings: Settings): string[] {
  return Object.entries(settings).flatMap(([key, value]) => [
    '-s',
    `${key}=${value}`,
  ]);
}

function engineAborted(
  error: unknown,
  errors: readonly string[],
): SlicerJobError {
  const text = `${error instanceof Error ? error.message : String(error)} ${errors.join(' ')}`;
  const outOfMemory = /memory|OOM|Cannot enlarge/i.test(text);
  return new SlicerJobError([
    outOfMemory
      ? slicerViolation(
          SlicerViolationCode.OUT_OF_MEMORY,
          'The slicer ran out of memory. Slice this model on your computer and upload the G-code instead.',
        )
      : slicerViolation(
          SlicerViolationCode.ENGINE_FAILED,
          `The slicer stopped unexpectedly. ${lastLines(errors)}`.trim(),
        ),
  ]);
}

function lastLines(errors: readonly string[]): string {
  return errors.slice(-3).join(' ');
}
