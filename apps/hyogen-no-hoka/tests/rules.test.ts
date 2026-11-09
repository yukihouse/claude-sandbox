import { describe, expect, it } from 'vitest';
import { LEVEL } from '../src/config';
import { STAGES } from '../src/data/stages';
import { arrive, castleAt, createState, defMult, incoming, send } from '../src/game/rules';
import { state } from './helpers';

describe('createState', () => {
  it('builds castles and items from the stage definition', () => {
    const S = createState(0);
    expect(S.stage).toBe(STAGES[0]);
    expect(S.castles[0]).toEqual({ id: 0, x: 0.2, y: 0.5, owner: 1, level: 2, troops: 20, wallUntil: 0, flash: 0 });
    expect(S.items).toEqual(STAGES[0]?.items);
    expect(S.items).not.toBe(STAGES[0]?.items);
    expect(S.aiTimer).toEqual({ 2: 4.5 * 2.2, 3: 4.5 * 2.6 });
    expect(S.running).toBe(false);
  });

  it('rejects an unknown stage', () => {
    expect(() => createState(STAGES.length)).toThrow(RangeError);
  });
});

describe('castleAt', () => {
  it('returns the castle or throws', () => {
    const S = state([[0, 0, 1, 1, 5]]);
    expect(castleAt(S, 0).troops).toBe(5);
    expect(() => castleAt(S, 1)).toThrow(RangeError);
  });
});

describe('defMult / incoming', () => {
  it('doubles defence while a wall is up', () => {
    const S = state([[0, 0, 1, 1, 5]]);
    const c = castleAt(S, 0);
    expect(defMult(S, c)).toBe(1);
    c.wallUntil = 3;
    expect(defMult(S, c)).toBe(2);
    S.t = 3;
    expect(defMult(S, c)).toBe(1);
  });

  it('sums matching armies heading to a castle', () => {
    const S = state([
      [0, 0, 1, 1, 5],
      [1, 0, 2, 1, 5],
    ]);
    S.armies = [
      { owner: 2, n: 4, to: 0, x: 0, y: 0 },
      { owner: 2, n: 3, to: 0, x: 0, y: 0 },
      { owner: 1, n: 9, to: 0, x: 0, y: 0 },
      { owner: 2, n: 7, to: 1, x: 0, y: 0 },
    ];
    expect(incoming(S, castleAt(S, 0), (a) => a.owner === 2)).toBe(7);
  });
});

describe('send', () => {
  it('moves whole troops out to the edge of the base', () => {
    const S = state([
      [0, 0, 1, 2, 10],
      [1, 0, 0, 1, 5],
    ]);
    expect(send(S, castleAt(S, 0), castleAt(S, 1), 4.9)).toBe(true);
    expect(castleAt(S, 0).troops).toBe(6);
    expect(S.armies).toEqual([{ owner: 1, n: 4, to: 1, x: LEVEL[2].r, y: 0 }]);
  });

  it('refuses empty, self and over-sized orders', () => {
    const S = state([
      [0, 0, 1, 1, 10],
      [1, 0, 0, 1, 5],
    ]);
    const a = castleAt(S, 0);
    const b = castleAt(S, 1);
    expect(send(S, a, b, 0.5)).toBe(false);
    expect(send(S, a, a, 3)).toBe(false);
    expect(send(S, a, b, 11)).toBe(false);
    expect(S.armies).toEqual([]);
    expect(a.troops).toBe(10);
  });

  it('handles two bases at the same spot', () => {
    const S = state([
      [0.5, 0.5, 1, 1, 10],
      [0.5, 0.5, 0, 1, 5],
    ]);
    expect(send(S, castleAt(S, 0), castleAt(S, 1), 2)).toBe(true);
    expect(S.armies[0]).toMatchObject({ x: 0.5, y: 0.5 });
  });
});

describe('arrive', () => {
  const setup = () =>
    state([
      [0, 0, 1, 1, 10],
      [1, 0, 2, 1, 10],
    ]);

  it('reinforces a friendly base', () => {
    const S = setup();
    arrive(S, { owner: 1, n: 5, to: 0, x: 0, y: 0 }, castleAt(S, 0));
    expect(castleAt(S, 0).troops).toBe(15);
  });

  it('wears down a base it cannot take, less so behind a wall', () => {
    const S = setup();
    const c = castleAt(S, 1);
    arrive(S, { owner: 1, n: 4, to: 1, x: 0, y: 0 }, c);
    expect(c.troops).toBe(6);
    c.wallUntil = 10;
    arrive(S, { owner: 1, n: 4, to: 1, x: 0, y: 0 }, c);
    expect(c.troops).toBe(4);
    expect(c.owner).toBe(2);
    // exactly equal force holds the base
    arrive(S, { owner: 1, n: 8, to: 1, x: 0, y: 0 }, c);
    expect(c).toMatchObject({ owner: 2, troops: 0 });
  });

  it('lets the player capture a base', () => {
    const S = setup();
    const c = castleAt(S, 1);
    c.wallUntil = 1;
    arrive(S, { owner: 1, n: 25, to: 1, x: 0, y: 0 }, c);
    expect(c).toMatchObject({ owner: 1, troops: 5, wallUntil: 0, flash: 1 });
    expect(S.captured).toBe(1);
    expect(S.floaters).toEqual([{ x: 1, y: 0, text: '制圧', tone: 'player', age: 0 }]);
  });

  it('drops the selection when an enemy takes the selected base', () => {
    const S = setup();
    S.selected = 0;
    arrive(S, { owner: 2, n: 11, to: 0, x: 0, y: 0 }, castleAt(S, 0));
    expect(castleAt(S, 0).owner).toBe(2);
    expect(S.selected).toBeNull();
    expect(S.captured).toBe(0);
    expect(S.floaters).toEqual([]);
  });

  it('keeps the selection when an enemy takes another base', () => {
    const S = state([
      [0, 0, 1, 1, 10],
      [1, 0, 0, 1, 2],
    ]);
    S.selected = 0;
    arrive(S, { owner: 2, n: 5, to: 1, x: 0, y: 0 }, castleAt(S, 1));
    expect(castleAt(S, 1).owner).toBe(2);
    expect(S.selected).toBe(0);
  });
});
