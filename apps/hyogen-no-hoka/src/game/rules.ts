import { LEVEL } from '../config';
import { STAGES } from '../data/stages';
import type { Army, Castle, FloaterTone, GameState, StageDef } from '../types';
import { dist, type XY } from './geometry';

export function createState(i: number, stages: readonly StageDef[] = STAGES): GameState {
  const stage = stages[i];
  if (!stage) throw new RangeError(`no stage ${i}`);
  return {
    i,
    stage,
    t: 0,
    running: false,
    paused: false,
    over: false,
    endAt: null,
    result: null,
    castles: stage.castles.map(([x, y, owner, level, troops], id) => ({
      id,
      x,
      y,
      owner,
      level,
      troops,
      wallUntil: 0,
      flash: 0,
    })),
    armies: [],
    floaters: [],
    aiTimer: { 2: stage.ai.interval * 2.2, 3: stage.ai.interval * 2.6 },
    items: { ...stage.items },
    galeUntil: 0,
    selected: null,
    mode: null,
    captured: 0,
  };
}

export function castleAt(S: GameState, id: number): Castle {
  const c = S.castles[id];
  if (!c) throw new RangeError(`no castle ${id}`);
  return c;
}

/** Defence multiplier: 2 while a 防寒壁 is up. */
export const defMult = (S: GameState, c: Castle): number => (c.wallUntil > S.t ? 2 : 1);

/** Troops of armies heading to `c` that match `pred`. */
export function incoming(S: GameState, c: Castle, pred: (a: Army) => boolean): number {
  let n = 0;
  for (const a of S.armies) if (a.to === c.id && pred(a)) n += a.n;
  return n;
}

export function floater(S: GameState, at: XY, text: string, tone: FloaterTone): void {
  S.floaters.push({ x: at.x, y: at.y, text, tone, age: 0 });
}

/** Send `n` troops (rounded down) from one castle to another. */
export function send(S: GameState, from: Castle, to: Castle, n: number): boolean {
  n = Math.floor(n);
  if (n < 1 || from === to || from.troops < n) return false;
  from.troops -= n;
  const d = dist(from, to) || 1;
  const r = LEVEL[from.level].r;
  S.armies.push({
    owner: from.owner,
    n,
    to: to.id,
    x: from.x + ((to.x - from.x) / d) * r,
    y: from.y + ((to.y - from.y) / d) * r,
  });
  return true;
}

/** An army reaches castle `c`: reinforce it, or attack it. */
export function arrive(S: GameState, a: Army, c: Castle): void {
  if (c.owner === a.owner) {
    c.troops += a.n;
    return;
  }
  const mult = defMult(S, c);
  const def = c.troops * mult;
  if (a.n > def) {
    c.owner = a.owner;
    c.troops = a.n - def;
    c.wallUntil = 0;
    c.flash = 1;
    if (a.owner === 1) {
      S.captured++;
      floater(S, c, '制圧', 'player');
    } else if (S.selected === c.id) {
      S.selected = null;
    }
  } else {
    c.troops -= a.n / mult;
  }
}
