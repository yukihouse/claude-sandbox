import { H, W } from '../config';
import { inRiver, segments } from '../game/geometry';
import { mulberry } from '../game/rng';
import type { Point, River, StageDef } from '../types';
import { DISPLAY_FONT, type Palette, UI_FONT } from './palette';
import { toS, type View } from './view';

const SEA = '#a9c3d3';
const ICE = '#f2f6f8';
const SEA_ICE = '#e4eef3';
const LINE = 'rgba(24,36,46,0.13)';

type Ctx = CanvasRenderingContext2D;
type At = (x: number, y: number) => [number, number];

/** Trace a closed polygon given in world coordinates. */
function trace(g: Ctx, at: At, pts: readonly Point[]): void {
  g.beginPath();
  pts.forEach(([x, y], k) => {
    const [px, py] = at(x, y);
    if (k) g.lineTo(px, py);
    else g.moveTo(px, py);
  });
  g.closePath();
}

/** An irregular round outline (ice floe, rock outcrop) around (cx, cy). */
function blob(rnd: () => number, cx: number, cy: number, r: number, n = 9): Point[] {
  const ph = rnd() * 6;
  return Array.from({ length: n }, (_, k) => {
    const a = (k / n) * Math.PI * 2 + ph;
    const rr = r * (0.78 + rnd() * 0.32);
    return [cx + Math.cos(a) * rr, cy + Math.sin(a) * rr] as const;
  });
}

/** Wavy contour rings around a few random hills. */
function hills(g: Ctx, at: At, rnd: () => number, count: number): void {
  for (let k = 0; k < count; k++) {
    const hx = rnd() * W;
    const hy = rnd() * H;
    const base = 0.06 + rnd() * 0.09;
    const ph = rnd() * 6;
    for (let ring = 0; ring < 4; ring++) {
      const rr = base * (1 - ring * 0.22);
      const pts: Point[] = [];
      for (let p = 0; p < 36; p++) {
        const a = (p / 36) * Math.PI * 2;
        const wob = 1 + 0.16 * Math.sin(a * 3 + ph) + 0.08 * Math.sin(a * 5 + ph * 2);
        pts.push([hx + Math.cos(a) * rr * wob * 1.2, hy + Math.sin(a) * rr * wob]);
      }
      trace(g, at, pts);
      if (ring === 3) {
        g.fillStyle = 'rgba(24,36,46,0.05)';
        g.fill();
      }
      g.strokeStyle = LINE;
      g.lineWidth = 1;
      g.stroke();
    }
  }
}

/** A snow-capped peak. */
function peak(g: Ctx, px: number, py: number, sz: number): void {
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

/** Short parallel strokes: wind-carved snow ridges (sastrugi). */
function sastrugi(g: Ctx, at: At, rnd: () => number, count: number, clear: (x: number, y: number) => boolean): void {
  g.strokeStyle = 'rgba(24,36,46,0.16)';
  g.lineWidth = 1.2;
  g.lineCap = 'round';
  for (let k = 0; k < count; k++) {
    const x = rnd() * W;
    const y = rnd() * H;
    if (!clear(x, y)) continue;
    for (let d = 0; d < 4; d++) {
      const [px, py] = at(x + (rnd() - 0.5) * 0.06, y + (rnd() - 0.5) * 0.05);
      const l = 6 + rnd() * 8;
      g.beginPath();
      g.moveTo(px - l, py + l * 0.25);
      g.lineTo(px + l, py - l * 0.25);
      g.stroke();
    }
  }
}

/** Glacier crevasses: a pale band with jagged cracks across it. */
function crevasse(g: Ctx, at: At, rnd: () => number, r: River, s: number): void {
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

/** A tide crack in the sea ice: a lead of dark water with broken white edges. */
function tideCrack(g: Ctx, at: At, rnd: () => number, r: River, s: number): void {
  const pts = r.pts.map(([x, y]) => at(x, y));
  g.lineCap = 'round';
  g.lineJoin = 'round';
  const line = () => {
    g.beginPath();
    pts.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
  };
  line();
  g.strokeStyle = 'rgba(169,195,211,0.9)';
  g.lineWidth = r.w * s;
  g.stroke();
  line();
  g.strokeStyle = 'rgba(52,88,116,0.55)';
  g.lineWidth = r.w * s * 0.35;
  g.stroke();
  // slabs of broken ice drifting in the lead
  g.fillStyle = ICE;
  g.strokeStyle = 'rgba(24,60,92,0.35)';
  g.lineWidth = 1;
  for (const [[ax, ay], [bx, by]] of segments(pts)) {
    const len = Math.hypot(bx - ax, by - ay);
    for (let d = 8; d < len; d += 14 + rnd() * 12) {
      const cx = ax + ((bx - ax) * d) / len + (rnd() - 0.5) * r.w * s * 0.5;
      const cy = ay + ((by - ay) * d) / len + (rnd() - 0.5) * r.w * s * 0.5;
      const z = r.w * s * (0.08 + rnd() * 0.1);
      g.beginPath();
      g.moveTo(cx - z, cy - z * 0.6);
      g.lineTo(cx + z * 0.9, cy - z);
      g.lineTo(cx + z, cy + z * 0.7);
      g.lineTo(cx - z * 0.7, cy + z);
      g.closePath();
      g.fill();
      g.stroke();
    }
  }
}

/** A small steamship seen from the side (the 宗谷). */
function ship(g: Ctx, px: number, py: number, sz: number): void {
  g.fillStyle = 'rgba(24,36,46,0.75)';
  g.beginPath();
  g.moveTo(px - sz, py - sz * 0.2);
  g.lineTo(px + sz * 1.1, py - sz * 0.2);
  g.lineTo(px + sz * 0.8, py + sz * 0.3);
  g.lineTo(px - sz * 0.8, py + sz * 0.3);
  g.closePath();
  g.fill();
  g.fillRect(px - sz * 0.45, py - sz * 0.65, sz * 0.8, sz * 0.45);
  g.fillStyle = '#e8b04a';
  g.fillRect(px - sz * 0.1, py - sz * 1.0, sz * 0.25, sz * 0.4);
}

/**
 * Draw the stage's static map once into an offscreen canvas of
 * `width` × `height` device pixels. Each chapter's terrain kind gets its own
 * look: ice shelf by the sea, glacier and mountains, open sea with floes,
 * sea ice off an island, or the flat inland plateau.
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
  const rnd = mulberry(stageIndex * 977 + 13);
  const s = view.scale;
  const at: At = (x, y) => toS(view, x, y);
  const kind = def.terrain;
  const nearBase = (x: number, y: number, m: number) => def.castles.some(([cx, cy]) => Math.hypot(cx - x, cy - y) < m);
  const clear = (x: number, y: number, m: number) => !nearBase(x, y, m) && !inRiver(def.rivers, x, y, 0.04);

  g.fillStyle = kind === 'sea' ? SEA : kind === 'coast' ? SEA_ICE : palette.terrain;
  g.fillRect(0, 0, view.cw, view.ch);

  if (kind === 'shelf') {
    // the open Ross Sea on the left, the ice-shelf edge, and the Bay of Whales cut into it
    const edge = (y: number) => 0.09 + 0.012 * Math.sin(y * 23) + 0.06 * Math.exp(-(((y - 0.2) / 0.08) ** 2));
    const sea: Point[] = [[-0.3, -0.3]];
    for (let y = -0.05; y <= H + 0.05; y += 0.02) sea.push([edge(y), y]);
    sea.push([-0.3, H + 0.3]);
    trace(g, at, sea);
    g.fillStyle = SEA;
    g.fill();
    g.strokeStyle = 'rgba(24,36,46,0.55)';
    g.lineWidth = 2;
    g.stroke();
    for (let k = 0; k < 10; k++) {
      const y = rnd() * H;
      trace(g, at, blob(rnd, edge(y) * (0.2 + rnd() * 0.5), y, 0.008 + rnd() * 0.01, 6));
      g.fillStyle = ICE;
      g.fill();
    }
    sastrugi(g, at, rnd, 30, (x, y) => x > edge(y) + 0.04 && clear(x, y, 0.08));
  } else if (kind === 'glacier') {
    hills(g, at, rnd, 7);
    // flow lines along the glacier
    for (const r of def.rivers) {
      for (const side of [-1, 1]) {
        g.beginPath();
        r.pts.forEach(([x, y], k) => {
          const [px, py] = at(x + side * r.w * 0.9, y);
          if (k) g.lineTo(px, py);
          else g.moveTo(px, py);
        });
        g.setLineDash([10, 7]);
        g.strokeStyle = 'rgba(24,60,92,0.25)';
        g.lineWidth = 1.2;
        g.stroke();
        g.setLineDash([]);
      }
      crevasse(g, at, rnd, r, s);
    }
    let placed = 0;
    for (let tries = 0; tries < 500 && placed < 24; tries++) {
      const x = 0.03 + rnd() * (W - 0.06);
      const y = 0.04 + rnd() * (H - 0.08);
      if (!clear(x, y, 0.11)) continue;
      placed++;
      const [px, py] = at(x, y);
      peak(g, px, py, (0.018 + rnd() * 0.016) * s);
    }
    sastrugi(g, at, rnd, 14, (x, y) => clear(x, y, 0.08));
  } else if (kind === 'sea') {
    // open water of the Weddell Sea: every base sits on its own floe, with pack ice around
    g.fillStyle = ICE;
    g.strokeStyle = 'rgba(24,60,92,0.35)';
    g.lineWidth = 1;
    for (let k = 0; k < 90; k++) {
      const x = rnd() * W;
      const y = rnd() * H;
      if (nearBase(x, y, 0.1)) continue;
      trace(g, at, blob(rnd, x, y, 0.012 + rnd() * 0.025, 7));
      g.fill();
      g.stroke();
    }
    for (const [cx, cy, , level] of def.castles) {
      trace(g, at, blob(rnd, cx, cy, 0.075 + level * 0.012, 11));
      g.fillStyle = ICE;
      g.fill();
      g.strokeStyle = 'rgba(24,60,92,0.45)';
      g.lineWidth = 1.4;
      g.stroke();
    }
    // swell on the open water
    g.strokeStyle = 'rgba(255,255,255,0.45)';
    g.lineWidth = 1;
    for (let k = 0; k < 40; k++) {
      const x = rnd() * W;
      const y = rnd() * H;
      if (nearBase(x, y, 0.11)) continue;
      const [px, py] = at(x, y);
      g.beginPath();
      g.arc(px, py, 6, Math.PI * 1.15, Math.PI * 1.85);
      g.stroke();
    }
  } else if (kind === 'coast') {
    // sea ice off the island: open water where the 宗谷 waits, the island beyond the tide crack
    const river = def.rivers[0];
    const water: Point[] = [[-0.3, -0.3], [0.075, -0.3]];
    for (let y = -0.05; y <= H + 0.05; y += 0.05) water.push([0.075 + 0.01 * Math.sin(y * 17), y]);
    water.push([0.075, H + 0.3], [-0.3, H + 0.3]);
    trace(g, at, water);
    g.fillStyle = SEA;
    g.fill();
    const [sx, sy] = at(0.035, 0.52);
    ship(g, sx, sy, Math.max(9, 0.02 * s));
    // pressure ridges in the sea ice
    g.strokeStyle = 'rgba(24,60,92,0.2)';
    g.lineWidth = 1;
    for (let k = 0; k < 26; k++) {
      const x = 0.1 + rnd() * 0.6;
      const y = rnd() * H;
      if (!clear(x, y, 0.08)) continue;
      const [px, py] = at(x, y);
      g.beginPath();
      g.moveTo(px - 10, py);
      for (let j = 1; j <= 4; j++) g.lineTo(px - 10 + j * 5, py + (j % 2 ? -3 : 2));
      g.stroke();
    }
    if (river) {
      const land: Point[] = [...river.pts.map(([x, y]) => [x + river.w * 0.5, y] as const), [W + 0.3, H + 0.3], [W + 0.3, -0.3]];
      trace(g, at, land);
      g.fillStyle = palette.terrain;
      g.fill();
      g.save();
      trace(g, at, land);
      g.clip();
      hills(g, at, rnd, 4);
      // bare rock: the station sits on rock that the snow leaves uncovered
      for (let k = 0; k < 40; k++) {
        const x = 0.8 + rnd() * (W - 0.8);
        const y = rnd() * H;
        if (nearBase(x, y, 0.09)) continue;
        trace(g, at, blob(rnd, x, y, 0.01 + rnd() * 0.022, 7));
        g.fillStyle = 'rgba(110,100,88,0.5)';
        g.fill();
      }
      g.restore();
      tideCrack(g, at, rnd, river, s);
    }
  } else {
    // the inland plateau: no mountains, only the long rise to the dome and its sastrugi
    const dome = def.castles.find((c) => c[3] === 3) ?? def.castles[def.castles.length - 1];
    const [dx, dy] = dome ?? [W, H / 2];
    g.font = `10px ${UI_FONT}`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    [0.18, 0.4, 0.66, 0.95, 1.25].forEach((r, k) => {
      const pts: Point[] = [];
      for (let p = 0; p < 48; p++) {
        const a = (p / 48) * Math.PI * 2;
        const wob = 1 + 0.05 * Math.sin(a * 4 + k);
        pts.push([dx + Math.cos(a) * r * 1.3 * wob, dy + Math.sin(a) * r * wob]);
      }
      trace(g, at, pts);
      g.strokeStyle = LINE;
      g.lineWidth = 1;
      g.stroke();
      // elevation labels on the far side from the bases
      const lx = dx - r * 1.3 * 0.94;
      const ly = dy + r * 0.34;
      if (lx > 0.02 && ly < H - 0.02 && !nearBase(lx, ly, 0.08)) {
        const [px, py] = at(lx, ly);
        g.fillStyle = 'rgba(24,36,46,0.4)';
        g.fillText(`${3800 - k * 200}m`, px, py);
      }
    });
    sastrugi(g, at, rnd, 40, (x, y) => clear(x, y, 0.08));
  }

  // any crevasse fields not drawn by the terrain above
  if (kind !== 'glacier' && kind !== 'coast') for (const r of def.rivers) crevasse(g, at, rnd, r, s);

  // place names, nudged inside the map frame so they are never cut off
  const fx0 = view.ox;
  const fy0 = view.oy;
  const fw = (view.portrait ? H : W) * s;
  const fh = (view.portrait ? W : H) * s;
  g.font = `700 12px ${DISPLAY_FONT}`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.lineJoin = 'round';
  for (const [x, y, name] of def.places) {
    const half = g.measureText(name).width / 2 + 4;
    const [qx, qy] = at(x, y);
    const px = Math.min(Math.max(qx, fx0 + half), fx0 + fw - half);
    const py = Math.min(Math.max(qy, fy0 + 10), fy0 + fh - 10);
    g.strokeStyle = 'rgba(245,248,250,0.85)';
    g.lineWidth = 3;
    g.strokeText(name, px, py);
    g.fillStyle = 'rgba(24,36,46,0.62)';
    g.fillText(name, px, py);
  }
  g.textAlign = 'start';

  // keep the outside of the map plain so the frame reads clearly
  g.save();
  g.beginPath();
  g.rect(0, 0, view.cw, view.ch);
  g.rect(fx0 - 14, fy0 - 14, fw + 28, fh + 28);
  g.clip('evenodd');
  g.fillStyle = palette.terrain;
  g.fillRect(0, 0, view.cw, view.ch);
  g.restore();

  // map frame + scale bar
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
