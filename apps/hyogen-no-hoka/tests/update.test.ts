import { describe, expect, it } from 'vitest';
import { CLASH, END_DELAY, FLOATER_LIFE, SPEED } from '../src/config';
import { castleAt } from '../src/game/rules';
import { update } from '../src/game/update';
import type { Army } from '../src/types';
import { state } from './helpers';

const army = (owner: Army['owner'], n: number, to: number, x: number, y = 0): Army => ({ owner, n, to, x, y });
const never = () => {
  throw new Error('AI should not have thought');
};

describe('update: bases', () => {
  it('grows owned bases towards their cap and shrinks overfull ones', () => {
    const S = state([
      [0, 0, 1, 1, 10],
      [0.2, 0, 2, 1, 40],
      [0.4, 0, 0, 1, 10],
      [0.6, 0, 1, 1, 30],
      [0.8, 0, 1, 1, 29.9],
    ]);
    update(S, 1, never);
    expect(S.t).toBe(1);
    expect(castleAt(S, 0).troops).toBeCloseTo(10.8);
    expect(castleAt(S, 1).troops).toBe(39.5);
    expect(castleAt(S, 2).troops).toBe(10);
    expect(castleAt(S, 3).troops).toBe(30);
    expect(castleAt(S, 4).troops).toBe(30);
  });

  it('fades the capture flash', () => {
    const S = state([
      [0, 0, 1, 1, 10],
      [1, 0, 2, 1, 10],
    ]);
    castleAt(S, 0).flash = 1;
    castleAt(S, 1).flash = 0.1;
    update(S, 0.5, never);
    expect(castleAt(S, 0).flash).toBeCloseTo(0.4);
    expect(castleAt(S, 1).flash).toBe(0);
  });
});

describe('update: armies', () => {
  const twoBases = (rivers = false) =>
    state(
      [
        [0, 0, 1, 1, 10],
        [1, 0, 2, 1, 10],
      ],
      rivers ? { rivers: [{ w: 0.2, pts: [[0.5, -1], [0.5, 1]] }] } : {},
    );

  it('marches towards the target', () => {
    const S = twoBases();
    S.armies = [army(1, 5, 1, 0)];
    update(S, 1, never);
    expect(S.armies[0]?.x).toBeCloseTo(SPEED);
  });

  it('doubles player speed under 雪上車 only', () => {
    const S = twoBases();
    S.galeUntil = 5;
    S.armies = [army(1, 5, 1, 0), army(2, 5, 0, 1)];
    update(S, 1, never);
    expect(S.armies[0]?.x).toBeCloseTo(SPEED * 2);
    expect(S.armies[1]?.x).toBeCloseTo(1 - SPEED);
  });

  it('halves speed inside a crevasse field', () => {
    const S = twoBases(true);
    S.armies = [army(1, 5, 1, 0.45)];
    update(S, 1, never);
    expect(S.armies[0]?.x).toBeCloseTo(0.45 + SPEED / 2);
  });

  it('arrives when the step reaches the target', () => {
    const S = twoBases();
    S.armies = [army(1, 15, 1, 1 - SPEED)];
    update(S, 1, never);
    expect(S.armies).toEqual([]);
    expect(castleAt(S, 1).owner).toBe(1);
  });

  it('makes opposing armies that meet lose the smaller number each', () => {
    const S = twoBases();
    S.armies = [army(1, 5, 1, 0.5), army(2, 3, 0, 0.5 + CLASH / 2)];
    update(S, 0.001, never);
    expect(S.armies).toHaveLength(1);
    expect(S.armies[0]).toMatchObject({ owner: 1, n: 2 });
    expect(S.floaters).toEqual([expect.objectContaining({ text: '−3', tone: 'ink' })]);
  });

  it('leaves armies of one side and far-apart armies alone', () => {
    const S = twoBases();
    S.armies = [army(1, 5, 1, 0.5), army(1, 5, 1, 0.5), army(2, 5, 0, 0.6)];
    update(S, 0.001, never);
    expect(S.armies.map((a) => a.n)).toEqual([5, 5, 5]);
  });

  it('stops a destroyed army from fighting again', () => {
    const S = twoBases();
    // a dies against c; b (same side as a) then meets c already at 0
    S.armies = [army(1, 2, 1, 0.5), army(1, 10, 1, 0.5), army(2, 2, 0, 0.5)];
    update(S, 0.001, never);
    expect(S.armies).toEqual([expect.objectContaining({ owner: 1, n: 10 })]);

    // a survives b, then a dies against c; d is never reached
    S.armies = [army(1, 5, 1, 0.5), army(2, 2, 0, 0.5), army(2, 3, 0, 0.5), army(3, 9, 0, 0.5)];
    update(S, 0.001, never);
    expect(S.armies.map((x) => [x.owner, x.n])).toEqual([[3, 9]]);
    expect(S.floaters.map((f) => f.text)).toEqual(['−2', '−2', '−3']);
  });

  it('ages floaters and drops old ones', () => {
    const S = twoBases();
    S.floaters = [
      { x: 0, y: 0, text: 'a', tone: 'ink', age: 0 },
      { x: 0, y: 0, text: 'b', tone: 'ink', age: FLOATER_LIFE - 0.1 },
    ];
    update(S, 0.2, never);
    expect(S.floaters.map((f) => f.text)).toEqual(['a']);
    expect(S.floaters[0]?.age).toBeCloseTo(0.2);
  });
});

describe('update: AI timers', () => {
  it('counts down for factions with bases and resets after thinking', () => {
    const S = state([
      [0, 0, 1, 1, 10],
      [1, 0, 2, 1, 10],
    ]);
    S.aiTimer = { 2: 0.5, 3: 0.5 };
    update(S, 0.2, never);
    expect(S.aiTimer).toEqual({ 2: 0.3, 3: 0.5 });
    update(S, 0.3, () => 0.5);
    expect(S.aiTimer[2]).toBe(4);
  });
});

describe('update: end of stage', () => {
  it('wins once no hostile base or army remains, after a short delay', () => {
    const S = state([[0, 0, 1, 1, 10]]);
    S.selected = 0;
    S.mode = 'wall';
    expect(update(S, 0.1, never)).toBe(false);
    expect(S.result).toBe('win');
    expect(S.endAt).toBeCloseTo(0.1 + END_DELAY);
    expect(update(S, END_DELAY - 0.05, never)).toBe(false);
    expect(update(S, 0.1, never)).toBe(true);
    expect(S).toMatchObject({ over: true, running: false, selected: null, mode: null });
    expect(update(S, 0.1, never)).toBe(false);
  });

  it('loses once no friendly base or army remains', () => {
    const S = state([[1, 0, 2, 1, 10]]);
    update(S, 0.1, never);
    expect(S.result).toBe('lose');
  });

  it('keeps going while armies are still on the field', () => {
    const S = state([[0, 0, 0, 1, 10]]);
    S.armies = [army(1, 1, 0, 0.5), army(2, 1, 0, 0.9)];
    update(S, 0.01, never);
    expect(S.result).toBeNull();
    expect(S.endAt).toBeNull();
  });
});
