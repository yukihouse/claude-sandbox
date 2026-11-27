import type { GameState } from './types';

/** Next number in [0, 1) from the game's seeded PRNG (mulberry32); advances `s.seed`. */
export function rand(s: Pick<GameState, 'seed'>): number {
  s.seed = (s.seed + 0x6d2b79f5) | 0;
  let t = Math.imul(s.seed ^ (s.seed >>> 15), 1 | s.seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

/** Integer in [min, max], both inclusive. */
export const randInt = (s: Pick<GameState, 'seed'>, min: number, max: number): number =>
  min + Math.floor(rand(s) * (max - min + 1));

export const chance = (s: Pick<GameState, 'seed'>, p: number): boolean => rand(s) < p;

/** Random element; the array must not be empty. */
export const pick = <T>(s: Pick<GameState, 'seed'>, items: readonly T[]): T =>
  items[Math.floor(rand(s) * items.length)] as T;

/** Fisher–Yates shuffle into a new array. */
export function shuffle<T>(s: Pick<GameState, 'seed'>, items: readonly T[]): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand(s) * (i + 1));
    [out[i], out[j]] = [out[j] as T, out[i] as T];
  }
  return out;
}
