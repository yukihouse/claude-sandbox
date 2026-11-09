import { CLASH, END_DELAY, FLOATER_LIFE, LEVEL, SPEED } from '../config';
import type { AiOwner, Army, GameState } from '../types';
import { aiThink } from './ai';
import { inRiver } from './geometry';
import { arrive, castleAt } from './rules';

const AI_OWNERS: readonly AiOwner[] = [2, 3];

/**
 * Advance the simulation by `dt` seconds.
 * Returns true on the step where the stage ends (show the result screen).
 */
export function update(S: GameState, dt: number, rand: () => number = Math.random): boolean {
  S.t += dt;
  for (const c of S.castles) {
    if (c.owner === 0) continue;
    const L = LEVEL[c.level];
    if (c.troops < L.cap) c.troops = Math.min(L.cap, c.troops + L.rate * dt);
    else if (c.troops > L.cap) c.troops = Math.max(L.cap, c.troops - 0.5 * dt);
  }
  for (const c of S.castles) if (c.flash > 0) c.flash = Math.max(0, c.flash - dt * 1.2);

  // movement
  const keep: Army[] = [];
  for (const a of S.armies) {
    const tgt = castleAt(S, a.to);
    const dx = tgt.x - a.x;
    const dy = tgt.y - a.y;
    const d = Math.hypot(dx, dy);
    let sp = SPEED;
    if (a.owner === 1 && S.t < S.galeUntil) sp *= 2;
    if (inRiver(S.stage.rivers, a.x, a.y)) sp *= 0.5;
    const step = sp * dt;
    if (step >= d) {
      arrive(S, a, tgt);
      continue;
    }
    a.x += (dx / d) * step;
    a.y += (dy / d) * step;
    keep.push(a);
  }
  S.armies = keep;

  // field clashes
  for (let i = 0; i < S.armies.length; i++) {
    const a = S.armies[i] as Army;
    if (a.n <= 0) continue;
    for (let j = i + 1; j < S.armies.length; j++) {
      const b = S.armies[j] as Army;
      if (b.n <= 0 || a.owner === b.owner) continue;
      if (Math.hypot(a.x - b.x, a.y - b.y) < CLASH) {
        const m = Math.min(a.n, b.n);
        a.n -= m;
        b.n -= m;
        S.floaters.push({
          x: (a.x + b.x) / 2,
          y: (a.y + b.y) / 2,
          text: '−' + m,
          tone: 'ink',
          age: 0,
        });
        if (a.n <= 0) break;
      }
    }
  }
  S.armies = S.armies.filter((a) => a.n > 0);

  for (const f of S.floaters) f.age += dt;
  S.floaters = S.floaters.filter((f) => f.age < FLOATER_LIFE);

  // AI
  const ai = S.stage.ai;
  for (const owner of AI_OWNERS) {
    if (!S.castles.some((c) => c.owner === owner)) continue;
    S.aiTimer[owner] -= dt;
    if (S.aiTimer[owner] <= 0) {
      aiThink(S, owner);
      S.aiTimer[owner] = ai.interval * (0.75 + rand() * 0.5);
    }
  }

  // end check
  if (S.endAt === null) {
    const hostile = S.castles.some((c) => c.owner >= 2) || S.armies.some((a) => a.owner >= 2);
    const mine = S.castles.some((c) => c.owner === 1) || S.armies.some((a) => a.owner === 1);
    if (!hostile) {
      S.result = 'win';
      S.endAt = S.t + END_DELAY;
    } else if (!mine) {
      S.result = 'lose';
      S.endAt = S.t + END_DELAY;
    }
  } else if (S.t >= S.endAt && !S.over) {
    S.over = true;
    S.running = false;
    S.selected = null;
    S.mode = null;
    return true;
  }
  return false;
}
