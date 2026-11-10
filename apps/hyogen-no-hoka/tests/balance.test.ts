import { describe, expect, it } from 'vitest';
import { STAGES } from '../src/data/stages';
import { applyItem } from '../src/game/actions';
import { aiThink } from '../src/game/ai';
import { createState, defMult, incoming } from '../src/game/rules';
import { update } from '../src/game/update';
import type { AiOwner } from '../src/types';

/** Small seeded PRNG (mulberry32) so the balance check is deterministic. */
function seeded(seed: number): () => number {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Play stage `i` with a simple bot as the player: once a second it shields a
 * threatened base with an item, then makes the same move the enemy AI would.
 */
function botPlays(i: number, seed: number): boolean {
  const S = createState(i);
  S.running = true;
  const rand = seeded(seed);
  let wait = 0;
  while (S.t < 900) {
    if (update(S, 0.05, rand)) return S.result === 'win';
    wait -= 0.05;
    if (wait > 0) continue;
    wait = 1;
    for (const c of S.castles) {
      if (c.owner !== 1) continue;
      const threat =
        incoming(S, c, (a) => a.owner !== 1) -
        incoming(S, c, (a) => a.owner === 1) -
        c.troops * defMult(S, c);
      if (threat <= -2) continue;
      if (S.items.wall > 0 && c.wallUntil <= S.t) applyItem(S, 'wall', c);
      else if (S.items.reinforce > 0) applyItem(S, 'reinforce', c);
    }
    aiThink(S, 1 as unknown as AiOwner);
  }
  return false;
}

describe('stage balance', () => {
  // A human should do at least as well as this bot, so every chapter must be
  // clearly winnable for it (the finale once was not: 13 wins in 150 games).
  it.each(STAGES.map((s, i) => [s.name, i] as const))('%s can be won', (_name, i) => {
    let wins = 0;
    for (let seed = 1; seed <= 30; seed++) if (botPlays(i, seed)) wins++;
    expect(wins).toBeGreaterThanOrEqual(6);
  });
});
