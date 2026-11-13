/**
 * G-code parser: turns a G-code file, from our engine or a student's own slicer, into toolpaths
 * to draw and a summary that means the same whichever slicer made it.
 *
 *   text chunks (streamed, never the whole file in one string)
 *        │
 *        ▼
 *   split into lines ──────────────── a partial last line waits for the next chunk
 *        │
 *        ▼
 *   header? ── first move or 300 lines ──▶ detectDialect(header)
 *        │                                   Cura ─▶ ;TYPE: and ;LAYER: comments are read
 *        │                                   none ─▶ extrusion vs travel, layers from Z
 *        ▼
 *   each line ──┬── ;comment ──────▶ dialect: set the current feature, or mark a new layer
 *               │
 *               ├── G90/G91, M82/M83, G20/G21, G92 ──▶ positioning, extrusion and unit modes
 *               │
 *               └── G0–G3 move ──▶ new position, extruded length (E delta > 0)
 *                                     │
 *                                     ├── extruding ──▶ feature = current feature
 *                                     │                 filament, bounds, layer start
 *                                     └── not ────────▶ feature = TRAVEL
 *                                     │
 *                                     ▼
 *                     ToolpathBuilder.add(from, to, feature)   (stops at the segment budget)
 *                     distance and time per feature            (time = length ÷ feed rate)
 *        │
 *        ▼
 *   finish ──▶ Toolpaths: typed arrays, drawn in the browser, never sent anywhere
 *          └─▶ SliceSummary: layer count, print time (the header's if stated, else the
 *              estimate), filament, bounds of extruded moves, per-feature totals
 * Reference: https://reprap.org/wiki/G-code for the G-code commands.
 */
import { create } from '@bufbuild/protobuf';
import { DurationSchema } from '@bufbuild/protobuf/wkt';
import {
  BoundingBoxMmSchema,
  Vector3MmSchema,
} from '../../gen/print_preparation/v1/geometry_pb';
import {
  FeatureStatSchema,
  type SliceSummary,
  SliceSummarySchema,
  ToolpathFeature,
} from '../../gen/print_preparation/slicing/v1/slice_summary_pb';
import { SlicerViolationCode } from '../../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../../validation/violations';
import type { Toolpaths } from '../types';
import { detectDialect, type GcodeDialect } from './dialects';
import { ToolpathBuilder } from './toolpath-builder';

export interface ParsedGcode {
  summary: SliceSummary;
  toolpaths: Toolpaths;
}

export interface ParseOptions {
  segmentBudget: number;
  /** Called with how many characters have been read so far. */
  onRead?: (characters: number) => void;
}

// The header is everything before the first move; this many lines is enough to name the slicer.
const HEADER_LINES = 300;
const MM_PER_INCH = 25.4;
const DEFAULT_FEED_MM_PER_MIN = 1500;
const SECONDS_PER_MINUTE = 60;
// Z moves smaller than this are noise, not a new layer.
const LAYER_EPSILON_MM = 1e-4;

type Vector = [number, number, number];

/** Reads G-code, streamed as text, into toolpaths to draw and a slicer-independent summary. */
export async function parseGcodeText(
  chunks: AsyncIterable<string> | Iterable<string>,
  options: ParseOptions,
): Promise<ParsedGcode> {
  const state = new GcodeState(options.segmentBudget);
  const header: string[] = [];
  let read = 0;
  let remainder = '';

  const feed = (line: string) => {
    if (state.dialectDecided) {
      state.line(line);
      return;
    }
    header.push(line);
    if (header.length >= HEADER_LINES || /^\s*G[01]\s/.test(line)) {
      state.decide(header.join('\n'));
      header.forEach((each) => state.line(each));
    }
  };

  for await (const chunk of chunks) {
    read += chunk.length;
    const lines = (remainder + chunk).split('\n');
    remainder = lines.pop() ?? '';
    lines.forEach(feed);
    options.onRead?.(read);
  }
  if (remainder) {
    feed(remainder);
  }
  if (!state.dialectDecided) {
    state.decide(header.join('\n'));
    header.forEach((each) => state.line(each));
  }
  return state.finish();
}

class GcodeState {
  private dialect: GcodeDialect | undefined;
  private headerText = '';
  dialectDecided = false;

  private readonly builder: ToolpathBuilder;
  private position: Vector = [0, 0, 0];
  private extruder = 0;
  private absolutePositions = true;
  private absoluteExtrusion = true;
  private unitScale = 1;
  private feedMmPerMin = DEFAULT_FEED_MM_PER_MIN;
  private feature: ToolpathFeature = ToolpathFeature.EXTRUSION_UNKNOWN;
  private layerPending = false;
  private lastLayerZ = -Infinity;
  private moves = 0;

  private filamentMm = 0;
  private readonly min: Vector = [Infinity, Infinity, Infinity];
  private readonly max: Vector = [-Infinity, -Infinity, -Infinity];
  private readonly distance = new Map<ToolpathFeature, number>();
  private readonly seconds = new Map<ToolpathFeature, number>();

  constructor(segmentBudget: number) {
    this.builder = new ToolpathBuilder(segmentBudget);
  }

  decide(header: string): void {
    this.headerText = header;
    this.dialect = detectDialect(header);
    this.dialectDecided = true;
  }

  line(raw: string): void {
    const semicolon = raw.indexOf(';');
    const code = (semicolon === -1 ? raw : raw.slice(0, semicolon)).trim();
    if (semicolon !== -1) {
      this.comment(raw.slice(semicolon + 1).trim());
    }
    if (!code) {
      return;
    }
    const [command = '', ...words] = code.toUpperCase().split(/\s+/);
    const value = (letter: string): number | undefined => {
      const word = words.find((each) => each.startsWith(letter));
      const number = word === undefined ? NaN : Number(word.slice(1));
      return Number.isFinite(number) ? number : undefined;
    };

    switch (command) {
      case 'G0':
      case 'G1':
      case 'G2':
      case 'G3':
        // Arcs are drawn as a straight line to their end point.
        this.move(value('X'), value('Y'), value('Z'), value('E'), value('F'));
        break;
      case 'G20':
        this.unitScale = MM_PER_INCH;
        break;
      case 'G21':
        this.unitScale = 1;
        break;
      case 'G90':
        this.absolutePositions = true;
        this.absoluteExtrusion = true;
        break;
      case 'G91':
        this.absolutePositions = false;
        this.absoluteExtrusion = false;
        break;
      case 'M82':
        this.absoluteExtrusion = true;
        break;
      case 'M83':
        this.absoluteExtrusion = false;
        break;
      case 'G92':
        this.setPosition(value('X'), value('Y'), value('Z'), value('E'));
        break;
    }
  }

  finish(): ParsedGcode {
    if (this.moves === 0) {
      throw new SlicerJobError([
        slicerViolation(
          SlicerViolationCode.UNREADABLE_GCODE,
          'This file has no printer moves, so it is not G-code that can be printed. Check that you chose the sliced file.',
        ),
      ]);
    }
    const estimated = [...this.seconds.values()].reduce((a, b) => a + b, 0);
    const stated = this.dialect?.printTimeSeconds(this.headerText);
    const extruded = this.min.every(Number.isFinite);
    return {
      toolpaths: this.builder.build(),
      summary: create(SliceSummarySchema, {
        slicer:
          this.dialect?.slicer(this.headerText) ??
          unknownSlicer(this.headerText),
        layerCount: this.builder.layerCount,
        printTime: duration(stated ?? estimated),
        filamentLengthMm: this.filamentMm,
        bounds: extruded
          ? create(BoundingBoxMmSchema, {
              min: create(Vector3MmSchema, {
                x: this.min[0],
                y: this.min[1],
                z: this.min[2],
              }),
              max: create(Vector3MmSchema, {
                x: this.max[0],
                y: this.max[1],
                z: this.max[2],
              }),
            })
          : undefined,
        featureStats: [...this.distance.entries()].map(
          ([feature, distanceMm]) =>
            create(FeatureStatSchema, {
              feature,
              distanceMm,
              time: duration(this.seconds.get(feature) ?? 0),
            }),
        ),
      }),
    };
  }

  private comment(text: string): void {
    if (!this.dialect) {
      return;
    }
    if (this.dialect.startsLayer(text)) {
      this.layerPending = true;
    }
    this.feature = this.dialect.feature(text) ?? this.feature;
  }

  private move(
    x: number | undefined,
    y: number | undefined,
    z: number | undefined,
    e: number | undefined,
    f: number | undefined,
  ): void {
    if (f !== undefined) {
      this.feedMmPerMin = f * this.unitScale;
    }
    const from: Vector = [...this.position];
    const to: Vector = [this.axis(0, x), this.axis(1, y), this.axis(2, z)];
    let extruded = 0;
    if (e !== undefined) {
      const next = this.absoluteExtrusion
        ? e * this.unitScale
        : this.extruder + e * this.unitScale;
      extruded = next - this.extruder;
      this.extruder = next;
    }
    this.position = to;
    const length = Math.hypot(
      to[0] - from[0],
      to[1] - from[1],
      to[2] - from[2],
    );
    if (length === 0) {
      return;
    }
    this.moves++;
    const extruding = extruded > 0;
    if (extruding) {
      this.filamentMm += extruded;
      this.startLayerIfNeeded(to[2]);
      for (const point of [from, to]) {
        for (let axis = 0; axis < 3; axis++) {
          this.min[axis] = Math.min(
            this.min[axis] ?? Infinity,
            point[axis] ?? 0,
          );
          this.max[axis] = Math.max(
            this.max[axis] ?? -Infinity,
            point[axis] ?? 0,
          );
        }
      }
    }
    const feature = extruding ? this.feature : ToolpathFeature.TRAVEL;
    this.builder.add(from, to, feature);
    this.distance.set(feature, (this.distance.get(feature) ?? 0) + length);
    const seconds = length / (this.feedMmPerMin / SECONDS_PER_MINUTE);
    this.seconds.set(feature, (this.seconds.get(feature) ?? 0) + seconds);
  }

  private startLayerIfNeeded(z: number): void {
    // A slicer that marks its layers starts one at its marker; otherwise a layer starts
    // wherever extrusion first reaches a new height.
    const marked = this.dialect !== undefined;
    if (marked ? this.layerPending : z > this.lastLayerZ + LAYER_EPSILON_MM) {
      this.builder.startLayer(z);
      this.lastLayerZ = z;
      this.layerPending = false;
    }
  }

  private axis(index: 0 | 1 | 2, value: number | undefined): number {
    const current = this.position[index];
    if (value === undefined) {
      return current;
    }
    const scaled = value * this.unitScale;
    return this.absolutePositions ? scaled : current + scaled;
  }

  private setPosition(
    x: number | undefined,
    y: number | undefined,
    z: number | undefined,
    e: number | undefined,
  ): void {
    const scale = this.unitScale;
    this.position = [
      x === undefined ? this.position[0] : x * scale,
      y === undefined ? this.position[1] : y * scale,
      z === undefined ? this.position[2] : z * scale,
    ];
    if (e !== undefined) {
      this.extruder = e * scale;
    }
  }
}

function duration(seconds: number) {
  const whole = Math.floor(seconds);
  return create(DurationSchema, {
    seconds: BigInt(whole),
    nanos: Math.round((seconds - whole) * 1e9),
  });
}

function unknownSlicer(header: string): string {
  return (
    /generated (?:by|with) ([^\r\n]+)/i.exec(header)?.[1]?.trim() ?? 'unknown'
  );
}
