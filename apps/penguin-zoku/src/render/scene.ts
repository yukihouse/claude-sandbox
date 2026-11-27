import { canWork, isAdult, seasonIndex } from '../game/rules';
import type { GameState, Penguin } from '../game/types';

export const W = 240;
export const H = 120;
const ICE_TOP = 74;
const SEA_X = 150;

const COLORS: Record<string, string> = {
  K: '#1b2430',
  W: '#f4f8fb',
  O: '#f29b30',
  G: '#9aa5ae',
  g: '#c7cfd5',
  Y: '#f5d142',
  R: '#d8443a',
  B: '#4f8fd6',
  b: '#7a5a3a',
};

const ADULT = ['..KKK..', '.KKKKK.', '.KWKWK.', '.KKOKK.', 'KKWWWKK', 'KKWWWKK', 'KKWWWKK', '.KWWWK.', '..WWW..', '.OO.OO.'];
const CHICK = ['.GGG.', 'GKGKG', 'GGOGG', 'GgggG', 'GgggG', '.O.O.'];
const CROWN = ['Y.Y.Y', 'YYYYY'];
const CROSS = ['.R.', 'RRR', '.R.'];
const DROP = ['.B.', 'BBB', '.B.'];
const HEART = ['R.R', 'RRR', '.R.'];
const SPARK = ['.Y.', 'YYY', '.Y.'];
const BONE = ['W..W', '.WW.', 'W..W'];

const SKY: readonly [string, string][] = [
  ['#9fd0ec', '#e6f4fb'], // 春
  ['#6fb7e6', '#d6eefa'], // 夏
  ['#d9a0a8', '#f4dccd'], // 秋
  ['#101a33', '#2c3a62'], // 冬
];

function sprite(ctx: CanvasRenderingContext2D, rows: readonly string[], x: number, y: number, scale = 1, maxRows = rows.length): void {
  for (let r = 0; r < Math.min(rows.length, maxRows); r++) {
    const row = rows[r] as string;
    for (let c = 0; c < row.length; c++) {
      const col = COLORS[row[c] as string];
      if (!col) continue;
      ctx.fillStyle = col;
      ctx.fillRect(Math.round(x + c * scale), Math.round(y + r * scale), scale, scale);
    }
  }
}

/** Stable pseudo-random number in [0, 1) for a penguin, so it keeps its spot between frames. */
const hash = (n: number): number => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

function drawBackdrop(ctx: CanvasRenderingContext2D, s: GameState, t: number): void {
  const season = seasonIndex(s.turn);
  const [top, bottom] = SKY[season] as [string, string];
  const g = ctx.createLinearGradient(0, 0, 0, ICE_TOP);
  g.addColorStop(0, top);
  g.addColorStop(1, bottom);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, ICE_TOP);
  if (season === 3) {
    // stars and an aurora
    ctx.fillStyle = '#e9f1ff';
    for (let i = 0; i < 24; i++) if ((i + Math.floor(t / 600)) % 7) ctx.fillRect(Math.floor(hash(i) * W), Math.floor(hash(i + 50) * 40), 1, 1);
    for (let x = 0; x < W; x += 2) {
      const y = 14 + Math.sin(x / 18 + t / 1400) * 6 + Math.sin(x / 7) * 2;
      ctx.fillStyle = x % 6 ? 'rgba(98, 230, 160, 0.35)' : 'rgba(160, 120, 240, 0.3)';
      ctx.fillRect(x, y, 2, 10);
    }
  } else {
    ctx.fillStyle = season === 1 ? '#fff3b0' : '#fff8dc';
    ctx.fillRect(200, 10, 10, 10);
    ctx.fillRect(198, 12, 14, 6);
  }
  // distant icebergs
  ctx.fillStyle = season === 3 ? '#6e7fa8' : '#cfe3ee';
  ctx.beginPath();
  ctx.moveTo(0, ICE_TOP);
  ctx.lineTo(18, 52);
  ctx.lineTo(40, 58);
  ctx.lineTo(62, 46);
  ctx.lineTo(90, 60);
  ctx.lineTo(120, 54);
  ctx.lineTo(150, ICE_TOP);
  ctx.fill();
  // sea
  ctx.fillStyle = season === 3 ? '#1c2f55' : '#2f6ea3';
  ctx.fillRect(0, ICE_TOP - 6, W, H);
  ctx.fillStyle = season === 3 ? '#2d4472' : '#4d8fc4';
  for (let i = 0; i < 18; i++) {
    const x = (hash(i + 9) * W + t / 90) % W;
    ctx.fillRect(Math.floor(x), ICE_TOP - 4 + Math.floor(hash(i) * 50), 6, 1);
  }
  // ice floe the tribe lives on
  ctx.fillStyle = season === 3 ? '#b9c6dc' : '#f2f8fb';
  ctx.fillRect(0, ICE_TOP, SEA_X, H - ICE_TOP);
  ctx.fillRect(SEA_X, ICE_TOP + 4, 4, H - ICE_TOP);
  ctx.fillStyle = season === 3 ? '#8ea0bd' : '#c3d9e6';
  ctx.fillRect(0, ICE_TOP, SEA_X, 2);
  ctx.fillRect(SEA_X + 3, ICE_TOP + 4, 1, H - ICE_TOP);
  // orca fin
  if (s.regions[s.regionId].orca > 0) {
    const x = SEA_X + 10 + ((t / 40) % (W - SEA_X - 10));
    sprite(ctx, ['...K', '..KK', '.KKK', 'KKKK'], x, ICE_TOP + 20, 2);
  }
}

function drawSnow(ctx: CanvasRenderingContext2D, t: number, heavy: boolean): void {
  ctx.fillStyle = '#ffffff';
  const n = heavy ? 70 : 30;
  for (let i = 0; i < n; i++) {
    const x = (hash(i) * W + (t / (heavy ? 12 : 40)) * (0.5 + hash(i + 3))) % W;
    const y = (hash(i + 7) * H + t / (heavy ? 18 : 30)) % H;
    ctx.fillRect(Math.floor(x), Math.floor(y), 1, 1);
  }
}

/** Where a penguin stands (or swims) in the scene. */
function placeOf(p: Penguin, t: number): { x: number; y: number; inSea: boolean; frame: number } {
  const h1 = hash(p.id);
  const h2 = hash(p.id + 1000);
  const inSea = canWork(p) && (p.action === 'krill' || p.action === 'fish');
  const frame = Math.floor(t / 400 + h1 * 4) % 2;
  if (inSea) {
    return {
      x: SEA_X + 8 + h1 * (W - SEA_X - 24) + Math.sin(t / 700 + h2 * 6) * 3,
      y: ICE_TOP + 4 + h2 * 30 + frame,
      inSea,
      frame,
    };
  }
  const chick = !isAdult(p);
  return {
    x: 4 + h1 * (SEA_X - 22) + (p.action === 'rest' && canWork(p) ? Math.sin(t / 900 + h2 * 6) * 2 : 0),
    y: ICE_TOP + 2 + h2 * (chick ? 30 : 24) + (frame && canWork(p) ? -1 : 0) + (chick ? 8 : 0),
    inSea,
    frame,
  };
}

function drawPenguin(ctx: CanvasRenderingContext2D, s: GameState, p: Penguin, t: number): void {
  const { x, y, inSea, frame } = placeOf(p, t);
  const h1 = hash(p.id);
  if (inSea) {
    sprite(ctx, ADULT, x, y, 2, 4);
    ctx.fillStyle = '#9cc9ea';
    ctx.fillRect(Math.round(x) - 2, Math.round(y) + 8, 18, 1);
    if (p.action === 'fish' && s.tools > 0) sprite(ctx, ['W', 'W', 'W', 'W'], x + 15, y - 4, 1);
  } else {
    if (!isAdult(p)) sprite(ctx, CHICK, x + 2, y, 2);
    else sprite(ctx, ADULT, x, y, 2);
    if (p.status === 'injured') sprite(ctx, CROSS, x + 10, y + 6, 1);
    if (p.status === 'sick') sprite(ctx, DROP, x + 10, y + 6, 1);
    if (canWork(p) && p.action === 'craft') sprite(ctx, BONE, x + 13, y + 14, 1);
    if (canWork(p) && p.action === 'pray' && frame) sprite(ctx, SPARK, x + 5, y - 6, 1);
    if (canWork(p) && p.action === 'rest' && p.mateId !== null && Math.floor(t / 1200 + h1 * 5) % 3 === 0)
      sprite(ctx, HEART, x + 5, y - 5, 1);
  }
  if (p.id === s.chiefId) sprite(ctx, CROWN, x + 2, y - 3, 1);
}

const ARROW = ['YYYYY', '.YYY.', '..Y..'];

/** Draw the tribe on its ice floe for time `t` (ms). */
export function drawScene(ctx: CanvasRenderingContext2D, s: GameState, t: number, selectedId: number | null = null): void {
  ctx.imageSmoothingEnabled = false;
  drawBackdrop(ctx, s, t);
  const order = [...s.penguins].sort((a, b) => hash(a.id + 1000) - hash(b.id + 1000));
  for (const p of order) drawPenguin(ctx, s, p, t);
  if (seasonIndex(s.turn) === 3 || s.coldwave > 0) drawSnow(ctx, t, s.coldwave > 0);
  const sel = selectedId === null ? undefined : s.penguins.find((p) => p.id === selectedId);
  if (sel) {
    const { x, y } = placeOf(sel, t);
    sprite(ctx, ARROW, x + 2, y - 9 + (Math.floor(t / 300) % 2), 1);
  }
}

/** A penguin as a small pixel-art SVG data URI, for lists. */
export function penguinIcon(p: Penguin): string {
  const rows = isAdult(p) ? ADULT : CHICK;
  const w = 7;
  const h = 10;
  const ox = Math.floor((w - (rows[0] as string).length) / 2);
  const oy = h - rows.length;
  let rects = '';
  rows.forEach((row, r) => {
    for (let c = 0; c < row.length; c++) {
      const col = COLORS[row[c] as string];
      if (col) rects += `<rect x="${c + ox}" y="${r + oy}" width="1" height="1" fill="${col}"/>`;
    }
  });
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges">${rects}</svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}
