import { describe, expect, it } from 'vitest';
import { newGame } from '../src/game/rules';
import { STORE_KEY, isGameState, loadGame, saveGame } from '../src/save';

function memory(): Storage & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return {
    data,
    getItem: (k: string) => data.get(k) ?? null,
    setItem: (k: string, v: string) => void data.set(k, v),
    removeItem: (k: string) => void data.delete(k),
  } as unknown as Storage & { data: Map<string, string> };
}

describe('save', () => {
  it('round-trips a game', () => {
    const st = memory();
    const s = newGame(9);
    s.moveTo = 'weddell';
    s.research.target = 'kotoba';
    s.penguins[0]!.mateId = s.penguins[1]!.id;
    saveGame(st, s);
    expect(loadGame(st)).toEqual(s);
  });

  it('clears the save when the game is over', () => {
    const st = memory();
    const s = newGame(9);
    saveGame(st, s);
    s.over = 'lose';
    saveGame(st, s);
    expect(st.data.has(STORE_KEY)).toBe(false);
    expect(loadGame(st)).toBeNull();
  });

  it('survives missing or failing storage', () => {
    expect(loadGame(null)).toBeNull();
    saveGame(null, newGame(1));
    const broken = {
      getItem: () => { throw new Error('blocked'); },
      setItem: () => { throw new Error('full'); },
      removeItem: () => { throw new Error('blocked'); },
    };
    expect(loadGame(broken)).toBeNull();
    expect(() => saveGame(broken, newGame(1))).not.toThrow();
  });

  it('rejects unreadable JSON', () => {
    const st = memory();
    st.setItem(STORE_KEY, '{not json');
    expect(loadGame(st)).toBeNull();
  });

  it('rejects malformed games', () => {
    const ok = () => JSON.parse(JSON.stringify(newGame(3)));
    expect(isGameState(ok())).toBe(true);
    const bad: ((s: any) => unknown)[] = [
      () => null,
      () => 'x',
      (s) => ({ ...s, version: 2 }),
      (s) => ({ ...s, food: 'many' }),
      (s) => ({ ...s, turn: Infinity }),
      (s) => ({ ...s, regionId: 'mars' }),
      (s) => ({ ...s, moveTo: 'mars' }),
      (s) => ({ ...s, over: 'win' }),
      (s) => ({ ...s, regions: null }),
      (s) => ({ ...s, regions: { ...s.regions, ross: undefined } }),
      (s) => ({ ...s, regions: { ...s.regions, ross: { krill: 1, fish: 1 } } }),
      (s) => ({ ...s, techs: 'mori' }),
      (s) => ({ ...s, techs: ['fire'] }),
      (s) => ({ ...s, research: null }),
      (s) => ({ ...s, research: { target: null } }),
      (s) => ({ ...s, research: { target: 'fire', points: 0 } }),
      (s) => ({ ...s, penguins: [] }),
      (s) => ({ ...s, penguins: 'six' }),
      (s) => ({ ...s, penguins: [null] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], age: '3' }] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], name: 3 }] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], sex: 'X' }] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], status: 'dead' }] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], action: 'fly' }] }),
      (s) => ({ ...s, penguins: [{ ...s.penguins[0], mateId: 'x' }] }),
    ];
    for (const f of bad) expect(isGameState(f(ok()))).toBe(false);
  });
});
