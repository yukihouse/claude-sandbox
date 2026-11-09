import { describe, expect, it } from 'vitest';
import { dist, inRiver, segmentDistance, segments } from '../src/game/geometry';
import { mulberry } from '../src/game/rng';

describe('geometry', () => {
  it('measures straight-line distance', () => {
    expect(dist({ x: 0, y: 0 }, { x: 3, y: 4 })).toBe(5);
  });

  it('pairs consecutive points', () => {
    expect([...segments([1, 2, 3])]).toEqual([
      [1, 2],
      [2, 3],
    ]);
    expect([...segments([1])]).toEqual([]);
  });

  it('measures distance to a segment, clamped to its ends', () => {
    expect(segmentDistance(0.5, 1, [0, 0], [1, 0])).toBe(1);
    expect(segmentDistance(-3, 4, [0, 0], [1, 0])).toBe(5);
    expect(segmentDistance(4, 4, [0, 0], [1, 0])).toBe(5);
    // a zero-length segment acts as a point
    expect(segmentDistance(3, 4, [0, 0], [0, 0])).toBe(5);
  });

  it('detects points inside a crevasse field', () => {
    const rivers = [{ w: 0.1, pts: [[0, 0], [1, 0], [1, 1]] as const }];
    expect(inRiver(rivers, 0.5, 0.04)).toBe(true);
    expect(inRiver(rivers, 0.96, 0.5)).toBe(true);
    expect(inRiver(rivers, 0.5, 0.06)).toBe(false);
    expect(inRiver(rivers, 0.5, 0.06, 0.02)).toBe(true);
    expect(inRiver([], 0, 0)).toBe(false);
  });
});

describe('mulberry', () => {
  it('is deterministic per seed and stays in [0, 1)', () => {
    const a = mulberry(42);
    const b = mulberry(42);
    const xs = Array.from({ length: 200 }, () => a());
    expect(Array.from({ length: 200 }, () => b())).toEqual(xs);
    expect(xs.every((x) => x >= 0 && x < 1)).toBe(true);
    expect(mulberry(43)()).not.toBe(xs[0]);
  });
});
