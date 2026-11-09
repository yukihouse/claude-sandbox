import { H, W } from '../config';
import { inRiver, segments } from '../game/geometry';
import { mulberry } from '../game/rng';
import type { StageDef } from '../types';
import { type Palette, UI_FONT } from './palette';
import { toS, type View } from './view';

/**
 * Draw the stage's static map (contours, crevasses, mountains, frame) once
 * into an offscreen canvas of `width` × `height` device pixels.
 */
export function buildTerrain(
  view: View,
  stageIndex: number,
  def: StageDef,
  width: number,
  height: number,
  palette: Palette,
): HTMLCanvasElement {
  const off = document.createElement('canvas');
  off.width = width;
  off.height = height;
  const g = off.getContext('2d');
  if (!g) return off;
  g.scale(view.dpr, view.dpr);
  g.fillStyle = palette.terrain;
  g.fillRect(0, 0, view.cw, view.ch);
  const rnd = mulberry(stageIndex * 977 + 13);
  const s = view.scale;
  const at = (x: number, y: number) => toS(view, x, y);

  // contour hills
  for (let k = 0; k < 7; k++) {
    const hx = rnd() * W;
    const hy = rnd() * H;
    const base = 0.06 + rnd() * 0.09;
    const ph = rnd() * 6;
    for (let ring = 0; ring < 4; ring++) {
      const rr = base * (1 - ring * 0.22);
      g.beginPath();
      for (let p = 0; p <= 36; p++) {
        const a = (p / 36) * Math.PI * 2;
        const wob = 1 + 0.16 * Math.sin(a * 3 + ph) + 0.08 * Math.sin(a * 5 + ph * 2);
        const [px, py] = at(hx + Math.cos(a) * rr * wob * 1.2, hy + Math.sin(a) * rr * wob);
        if (p) g.lineTo(px, py);
        else g.moveTo(px, py);
      }
      g.closePath();
      if (ring === 3) {
        g.fillStyle = 'rgba(24,36,46,0.05)';
        g.fill();
      }
      g.strokeStyle = 'rgba(24,36,46,0.13)';
      g.lineWidth = 1;
      g.stroke();
    }
  }

  // crevasse fields: a pale band with jagged cracks across it
  for (const r of def.rivers) {
    const pts = r.pts.map(([x, y]) => at(x, y));
    g.lineCap = 'round';
    g.lineJoin = 'round';
    g.beginPath();
    pts.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
    g.strokeStyle = 'rgba(140,178,204,0.55)';
    g.lineWidth = r.w * s;
    g.stroke();
    g.strokeStyle = 'rgba(24,60,92,0.5)';
    g.lineWidth = 1.4;
    for (const [[ax, ay], [bx, by]] of segments(pts)) {
      const len = Math.hypot(bx - ax, by - ay);
      const nx = -(by - ay) / len;
      const ny = (bx - ax) / len;
      for (let d = 6; d < len; d += 9 + rnd() * 8) {
        const cx = ax + ((bx - ax) * d) / len;
        const cy = ay + ((by - ay) * d) / len;
        const half = r.w * s * (0.15 + rnd() * 0.3);
        const off = (rnd() - 0.5) * r.w * s * 0.4;
        g.beginPath();
        g.moveTo(cx + nx * (off - half), cy + ny * (off - half));
        g.lineTo(cx + nx * off + (rnd() - 0.5) * 4, cy + ny * off + (rnd() - 0.5) * 4);
        g.lineTo(cx + nx * (off + half), cy + ny * (off + half));
        g.stroke();
      }
    }
  }

  // mountains and woods, kept clear of castles and crevasses
  const clear = (x: number, y: number, m: number) =>
    def.castles.every(([cx, cy]) => Math.hypot(cx - x, cy - y) > m) && !inRiver(def.rivers, x, y, 0.04);
  let placed = 0;
  for (let tries = 0; tries < 400 && placed < 16; tries++) {
    const x = 0.03 + rnd() * (W - 0.06);
    const y = 0.04 + rnd() * (H - 0.08);
    if (!clear(x, y, 0.11)) continue;
    placed++;
    const sz = (0.018 + rnd() * 0.014) * s;
    const [px, py] = at(x, y);
    g.beginPath();
    g.moveTo(px - sz, py);
    g.lineTo(px - sz * 0.15, py - sz * 1.25);
    g.lineTo(px + sz * 0.55, py - sz * 0.35);
    g.lineTo(px + sz * 0.9, py - sz * 0.75);
    g.lineTo(px + sz * 1.6, py);
    g.closePath();
    g.fillStyle = 'rgba(78,90,101,0.55)';
    g.fill();
    g.strokeStyle = 'rgba(24,36,46,0.5)';
    g.lineWidth = 1.2;
    g.stroke();
    g.beginPath();
    g.moveTo(px - sz * 0.45, py - sz * 0.68);
    g.lineTo(px - sz * 0.15, py - sz * 1.25);
    g.lineTo(px + sz * 0.2, py - sz * 0.75);
    g.closePath();
    g.fillStyle = '#f5f8fa';
    g.fill();
  }
  for (let k = 0; k < 22; k++) {
    const x = rnd() * W;
    const y = rnd() * H;
    if (!clear(x, y, 0.08)) continue;
    g.strokeStyle = 'rgba(24,36,46,0.16)';
    g.lineWidth = 1.2;
    g.lineCap = 'round';
    for (let d = 0; d < 4; d++) {
      const [px, py] = at(x + (rnd() - 0.5) * 0.06, y + (rnd() - 0.5) * 0.05);
      const l = 6 + rnd() * 8;
      g.beginPath();
      g.moveTo(px - l, py + l * 0.25);
      g.lineTo(px + l, py - l * 0.25);
      g.stroke();
    }
  }

  // map frame + scale bar
  const fx0 = view.ox;
  const fy0 = view.oy;
  const fw = (view.portrait ? H : W) * s;
  const fh = (view.portrait ? W : H) * s;
  g.strokeStyle = 'rgba(24,36,46,0.35)';
  g.lineWidth = 1;
  g.strokeRect(fx0 - 14, fy0 - 14, fw + 28, fh + 28);
  const bar = 0.2 * s;
  const bx = fx0 - 6;
  const by = fy0 + fh + 8;
  if (by + 4 < view.ch) {
    g.fillStyle = 'rgba(24,36,46,0.6)';
    g.fillRect(bx, by, bar / 2, 2);
    g.fillStyle = 'rgba(24,36,46,0.25)';
    g.fillRect(bx + bar / 2, by, bar / 2, 2);
    g.fillStyle = 'rgba(24,36,46,0.6)';
    g.font = `11px ${UI_FONT}`;
    g.textBaseline = 'middle';
    g.fillText('100 km', bx + bar + 6, by + 1);
  }
  return off;
}
