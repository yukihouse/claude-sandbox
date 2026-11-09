import type { Point, River } from '../types';

export interface XY {
  x: number;
  y: number;
}

export const dist = (a: XY, b: XY): number => Math.hypot(a.x - b.x, a.y - b.y);

/** Consecutive point pairs of a polyline. */
export function* segments<T>(pts: readonly T[]): Generator<[T, T]> {
  for (let k = 1; k < pts.length; k++) yield [pts[k - 1] as T, pts[k] as T];
}

/** Distance from (x, y) to the segment a–b. */
export function segmentDistance(x: number, y: number, [ax, ay]: Point, [bx, by]: Point): number {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / len2));
  return Math.hypot(x - (ax + dx * t), y - (ay + dy * t));
}

/** True when (x, y) lies inside a crevasse field, widened on each side by `extra`. */
export function inRiver(rivers: readonly River[], x: number, y: number, extra = 0): boolean {
  for (const r of rivers) {
    for (const [a, b] of segments(r.pts)) {
      if (segmentDistance(x, y, a, b) < r.w / 2 + extra) return true;
    }
  }
  return false;
}
