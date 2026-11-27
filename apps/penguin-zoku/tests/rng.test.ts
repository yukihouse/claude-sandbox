import { describe, expect, it } from 'vitest';
import { chance, pick, rand, randInt, shuffle } from '../src/game/rng';

describe('rng', () => {
  it('is deterministic for a seed and stays in [0, 1)', () => {
    const a = { seed: 7 };
    const b = { seed: 7 };
    const xs = Array.from({ length: 200 }, () => rand(a));
    expect(xs).toEqual(Array.from({ length: 200 }, () => rand(b)));
    expect(xs.every((x) => x >= 0 && x < 1)).toBe(true);
    expect(new Set(xs).size).toBeGreaterThan(190);
  });

  it('randInt covers both ends inclusively', () => {
    const s = { seed: 1 };
    const seen = new Set(Array.from({ length: 300 }, () => randInt(s, 2, 4)));
    expect([...seen].sort()).toEqual([2, 3, 4]);
  });

  it('chance respects 0 and 1', () => {
    const s = { seed: 3 };
    expect(chance(s, 0)).toBe(false);
    expect(chance(s, 1)).toBe(true);
  });

  it('pick and shuffle keep the elements', () => {
    const s = { seed: 5 };
    const items = [1, 2, 3, 4, 5];
    expect(items).toContain(pick(s, items));
    const out = shuffle(s, items);
    expect([...out].sort()).toEqual(items);
    expect(items).toEqual([1, 2, 3, 4, 5]);
  });
});
