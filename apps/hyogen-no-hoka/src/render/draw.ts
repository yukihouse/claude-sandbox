import { FLOATER_LIFE, LEVEL } from '../config';
import { castleAt } from '../game/rules';
import type { Castle, GameState, Level } from '../types';
import { DISPLAY_FONT, type Palette, toneColor, UI_FONT } from './palette';
import { hitCastle, radius, toS, type View } from './view';

export interface Pointer {
  x: number;
  y: number;
  inside: boolean;
}

export interface Drag {
  from: Castle | null;
  x: number;
  y: number;
  moved: boolean;
}

export interface Scene {
  ctx: CanvasRenderingContext2D;
  view: View;
  palette: Palette;
  terrain: HTMLCanvasElement | null;
  pointer: Pointer;
  drag: Drag | null;
  reduceMotion: boolean;
}

/** The little station silhouette drawn on top of each base. */
function drawKeep(ctx: CanvasRenderingContext2D, x: number, y: number, s: number, level: Level): void {
  const snow = 'rgba(245,248,250,0.96)';
  ctx.fillStyle = snow;
  ctx.strokeStyle = snow;
  const g = y + s * 0.34;
  ctx.fillRect(x - s * 0.55, g - s * 0.03, s * 1.1, s * 0.07);
  const hx = level === 1 ? x - s * 0.24 : x - s * 0.52;
  ctx.fillRect(hx, g - s * 0.42, s * 0.46, s * 0.28);
  ctx.fillRect(hx + s * 0.05, g - s * 0.14, s * 0.06, s * 0.14);
  ctx.fillRect(hx + s * 0.35, g - s * 0.14, s * 0.06, s * 0.14);
  ctx.fillStyle = 'rgba(24,36,46,0.3)';
  ctx.fillRect(hx + s * 0.1, g - s * 0.35, s * 0.1, s * 0.08);
  ctx.fillRect(hx + s * 0.26, g - s * 0.35, s * 0.1, s * 0.08);
  ctx.fillStyle = snow;
  if (level >= 2) {
    ctx.beginPath();
    ctx.arc(x + s * 0.24, g, s * 0.3, Math.PI, 0);
    ctx.closePath();
    ctx.fill();
  }
  const ax = level >= 2 ? x + s * 0.24 : x + s * 0.36;
  const top = g - s * (level === 3 ? 0.98 : 0.72);
  ctx.lineWidth = Math.max(1.2, s * 0.06);
  ctx.beginPath();
  ctx.moveTo(ax, level >= 2 ? g - s * 0.28 : g);
  ctx.lineTo(ax, top);
  ctx.stroke();
  if (level === 3) {
    ctx.beginPath();
    ctx.arc(ax, top, s * 0.09, 0, Math.PI * 2);
    ctx.fill();
  }
}

/** Draw one frame. `now` is in seconds and only drives animations. */
export function render(scene: Scene, S: GameState | null, now: number): void {
  const { ctx, view, palette, terrain, pointer, drag, reduceMotion } = scene;
  const { dpr, cw, ch } = view;
  const { ink: INK, paper: PAPER } = palette;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (terrain) ctx.drawImage(terrain, 0, 0, cw, ch);
  else {
    ctx.fillStyle = palette.terrain;
    ctx.fillRect(0, 0, cw, ch);
  }
  if (!S) return;
  const t = S.t;
  const unit = view.scale;
  const at = (x: number, y: number) => toS(view, x, y);

  // order line (drag, or hover while selected)
  const from =
    drag && drag.moved ? drag.from : S.selected !== null && pointer.inside ? castleAt(S, S.selected) : null;
  if (from) {
    const [sx, sy] = at(from.x, from.y);
    const tgt = hitCastle(view, S.castles, pointer.x, pointer.y);
    let ex = pointer.x;
    let ey = pointer.y;
    if (tgt && tgt !== from) [ex, ey] = at(tgt.x, tgt.y);
    ctx.strokeStyle = 'rgba(42,99,168,0.75)';
    ctx.lineWidth = 2.5;
    ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(ex, ey);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // castles
  for (const c of S.castles) {
    const [sx, sy] = at(c.x, c.y);
    const r = radius(view, c);
    const col = palette.owner[c.owner];
    const L = LEVEL[c.level];
    // growth ring
    ctx.lineWidth = 3;
    ctx.strokeStyle = 'rgba(24,36,46,0.12)';
    ctx.beginPath();
    ctx.arc(sx, sy, r + 5, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = col;
    ctx.beginPath();
    ctx.arc(sx, sy, r + 5, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, c.troops / L.cap));
    ctx.stroke();
    // body
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(24,36,46,0.55)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    drawKeep(ctx, sx, sy + r * 0.12, r * 0.9, c.level);
    // wall buff
    if (c.wallUntil > t) {
      ctx.strokeStyle = PAPER;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sx, sy, r - 3, 0, Math.PI * 2);
      ctx.stroke();
      ctx.strokeStyle = col;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sx, sy, r + 10, 0, Math.PI * 2);
      ctx.stroke();
    }
    // capture flash
    if (c.flash > 0) {
      ctx.strokeStyle = col;
      ctx.globalAlpha = c.flash;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(sx, sy, r + 6 + (1 - c.flash) * 26, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    // selection / targeting
    const isSel = S.selected === c.id || (drag && drag.from === c);
    if (isSel) {
      ctx.strokeStyle = INK;
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 5]);
      ctx.lineDashOffset = reduceMotion ? 0 : -now * 20;
      ctx.beginPath();
      ctx.arc(sx, sy, r + 12, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.lineDashOffset = 0;
    } else if (S.mode && c.owner === 1) {
      const pulse = reduceMotion ? 0.6 : 0.4 + 0.4 * Math.sin(now * 6);
      ctx.strokeStyle = `rgba(184,67,44,${pulse})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(sx, sy, r + 12, 0, Math.PI * 2);
      ctx.stroke();
    }
    // troop count
    const fs = Math.max(13, Math.min(20, r * 0.75));
    ctx.font = `700 ${fs}px ${UI_FONT}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const ty = sy + r + fs * 0.95;
    ctx.lineWidth = 4;
    ctx.strokeStyle = PAPER;
    ctx.lineJoin = 'round';
    const label = String(Math.floor(c.troops));
    ctx.strokeText(label, sx, ty);
    ctx.fillStyle = c.owner === 0 ? INK : col;
    ctx.fillText(label, sx, ty);
  }

  // armies
  for (const a of S.armies) {
    const [sx, sy] = at(a.x, a.y);
    const tgt = castleAt(S, a.to);
    const [tx, ty] = at(tgt.x, tgt.y);
    const d = Math.hypot(tx - sx, ty - sy) || 1;
    const r = Math.max(6, Math.min(18, 4 + Math.sqrt(a.n) * 1.5)) * Math.max(0.8, Math.min(1.3, unit / 500));
    const col = palette.owner[a.owner];
    ctx.strokeStyle = col;
    ctx.globalAlpha = 0.35;
    ctx.lineWidth = r * 0.8;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx - ((tx - sx) / d) * r * 2.2, sy - ((ty - sy) / d) * r * 2.2);
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.lineCap = 'butt';
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = PAPER;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.font = `700 ${Math.max(10, r * 0.95)}px ${UI_FONT}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = PAPER;
    ctx.fillText(String(a.n), sx, sy + 0.5);
  }

  // floaters
  for (const f of S.floaters) {
    const [sx, sy] = at(f.x, f.y);
    const y = sy - 24 - f.age * 22;
    ctx.globalAlpha = Math.max(0, 1 - f.age / FLOATER_LIFE);
    ctx.font = `800 15px ${DISPLAY_FONT}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineWidth = 4;
    ctx.strokeStyle = PAPER;
    ctx.strokeText(f.text, sx, y);
    ctx.fillStyle = toneColor(palette, f.tone);
    ctx.fillText(f.text, sx, y);
    ctx.globalAlpha = 1;
  }

  // paused veil
  if (!S.running && !S.over) {
    ctx.fillStyle = 'rgba(231,238,242,0.25)';
    ctx.fillRect(0, 0, cw, ch);
  }
}
