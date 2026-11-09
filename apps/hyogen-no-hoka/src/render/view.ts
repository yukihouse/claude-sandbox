import { H, LEVEL, W } from '../config';
import type { Castle } from '../types';

/** How the world maps onto the canvas, in CSS pixels. */
export interface View {
  cw: number;
  ch: number;
  dpr: number;
  /** Tall screens show the map rotated a quarter turn. */
  portrait: boolean;
  scale: number;
  ox: number;
  oy: number;
}

export const createView = (): View => ({ cw: 0, ch: 0, dpr: 1, portrait: false, scale: 1, ox: 0, oy: 0 });

/** Recompute orientation, scale and offset after `cw`/`ch` change. */
export function layout(view: View): void {
  const { cw, ch } = view;
  view.portrait = ch > cw * 1.05;
  const dw = view.portrait ? H : W;
  const dh = view.portrait ? W : H;
  const pad = Math.max(26, Math.min(cw, ch) * 0.07);
  view.scale = Math.max(1, Math.min((cw - pad * 2) / dw, (ch - pad * 2) / dh));
  view.ox = (cw - dw * view.scale) / 2;
  view.oy = (ch - dh * view.scale) / 2;
}

/** World → screen. */
export function toS(view: View, x: number, y: number): [number, number] {
  return view.portrait
    ? [view.ox + y * view.scale, view.oy + (W - x) * view.scale]
    : [view.ox + x * view.scale, view.oy + y * view.scale];
}

export const radius = (view: View, c: Castle): number => Math.max(16, LEVEL[c.level].r * view.scale);

/** The castle nearest to screen point (px, py) within tapping distance. */
export function hitCastle(view: View, castles: readonly Castle[], px: number, py: number): Castle | null {
  let best: Castle | null = null;
  let bd = Infinity;
  for (const c of castles) {
    const [sx, sy] = toS(view, c.x, c.y);
    const d = Math.hypot(px - sx, py - sy);
    if (d < Math.max(radius(view, c) + 12, 28) && d < bd) {
      best = c;
      bd = d;
    }
  }
  return best;
}
