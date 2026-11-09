import { describe, expect, it } from 'vitest';
import { createState } from '../src/game/rules';
import { createView, hitCastle, layout, radius, toS } from '../src/render/view';
import type { Castle } from '../src/types';

const sized = (cw: number, ch: number) => {
  const v = createView();
  v.cw = cw;
  v.ch = ch;
  layout(v);
  return v;
};

describe('layout / toS', () => {
  it('fits the landscape map with padding, centred', () => {
    const v = sized(1000, 600);
    expect(v.portrait).toBe(false);
    // pad = max(26, 600 × 0.07 = 42); min((1000-84)/1.5, (600-84)/1) = 516
    expect(v.scale).toBe(516);
    expect(v.ox).toBe((1000 - 1.5 * 516) / 2);
    expect(v.oy).toBe(42);
    expect(toS(v, 0, 0)).toEqual([v.ox, v.oy]);
    expect(toS(v, 1.5, 1)).toEqual([v.ox + 1.5 * 516, v.oy + 516]);
  });

  it('rotates the map on tall screens', () => {
    const v = sized(400, 800);
    expect(v.portrait).toBe(true);
    // the world's left edge (x = 0) ends up at the bottom
    const [, bottom] = toS(v, 0, 0);
    const [, top] = toS(v, 1.5, 0);
    expect(bottom).toBeGreaterThan(top);
    expect(toS(v, 1.5, 1)).toEqual([v.ox + v.scale, v.oy]);
  });

  it('never shrinks below one pixel per world unit', () => {
    expect(sized(10, 10).scale).toBe(1);
  });
});

describe('radius / hitCastle', () => {
  const v = sized(1000, 600);
  const castles: Castle[] = createState(0).castles;

  it('keeps bases at least 16px across', () => {
    const c = castles[0] as Castle;
    expect(radius(v, c)).toBeCloseTo(0.04 * 516);
    expect(radius(sized(100, 100), c)).toBe(16);
  });

  it('finds the base under a tap, preferring the nearest', () => {
    const c = castles[1] as Castle;
    const [x, y] = toS(v, c.x, c.y);
    expect(hitCastle(v, castles, x + 10, y)).toBe(c);
    expect(hitCastle(v, castles, x + 200, y + 200)).toBeNull();
    const twins: Castle[] = [{ ...c, id: 0 }, { ...c, id: 1, x: c.x + 0.02 }];
    expect(hitCastle(v, twins, ...toS(v, c.x + 0.015, c.y))?.id).toBe(1);
    expect(hitCastle(v, twins, ...toS(v, c.x + 0.005, c.y))?.id).toBe(0);
  });
});
