/**
 * The Cura dialect: how G-code from CuraEngine (ours, or the Cura app's) is read.
 *
 *   ;FLAVOR:Marlin                       ─┐
 *   ;TIME:5821                            ├─ header: detects() and printTimeSeconds() read it
 *   ;Filament used: 4.2m                  │
 *   ;Generated with Cura_SteamEngine 5.13 ┘─ slicer() names it
 *   ...
 *   ;LAYER:0          ─▶ startsLayer()            a new layer begins at the next extrusion
 *   ;TYPE:SKIRT       ─▶ feature() = SKIRT_BRIM    every move after it draws this feature
 *   G1 X.. Y.. E..                                 until the next ;TYPE:
 *   ;TYPE:WALL-OUTER  ─▶ feature() = OUTER_WALL
 *   ;TYPE:FILL        ─▶ feature() = INFILL
 *   ;TYPE:<other>     ─▶ feature() = EXTRUSION_UNKNOWN
 *   ;LAYER:1          ─▶ startsLayer()
 */
import { ToolpathFeature } from '../../../gen/print_preparation/slicing/v1/slice_summary_pb';
import type { GcodeDialect } from './dialect';

const FEATURES: Record<string, ToolpathFeature> = {
  'WALL-OUTER': ToolpathFeature.OUTER_WALL,
  'WALL-INNER': ToolpathFeature.INNER_WALL,
  SKIN: ToolpathFeature.SKIN,
  FILL: ToolpathFeature.INFILL,
  SUPPORT: ToolpathFeature.SUPPORT,
  'SUPPORT-INTERFACE': ToolpathFeature.SUPPORT_INTERFACE,
  SKIRT: ToolpathFeature.SKIRT_BRIM,
  'PRIME-TOWER': ToolpathFeature.PRIME_TOWER,
};

const GENERATED_BY = /^;Generated with (Cura_SteamEngine[^\r\n]*)/m;

export const cura: GcodeDialect = {
  id: 'cura',
  name: 'Cura / CuraEngine',
  detects: (header) => GENERATED_BY.test(header) || /^;FLAVOR:/m.test(header),
  slicer: (header) =>
    GENERATED_BY.exec(header)?.[1]?.trim() ?? 'Cura_SteamEngine',
  feature: (comment) =>
    comment.startsWith('TYPE:')
      ? (FEATURES[comment.slice('TYPE:'.length).trim()] ??
        ToolpathFeature.EXTRUSION_UNKNOWN)
      : undefined,
  startsLayer: (comment) => /^LAYER:-?\d+\s*$/.test(comment),
  printTimeSeconds: (header) => {
    const seconds = /^;TIME:(\d+(?:\.\d+)?)/m.exec(header)?.[1];
    return seconds === undefined ? undefined : Number(seconds);
  },
};
