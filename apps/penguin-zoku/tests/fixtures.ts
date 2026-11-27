import { newGame } from '../src/game/rules';
import type { GameState, Penguin } from '../src/game/types';

/** A healthy adult penguin with plain stats; override what a test needs. */
export function penguin(id: number, extra: Partial<Penguin> = {}): Penguin {
  return {
    id,
    name: `P${id}`,
    sex: id % 2 ? 'M' : 'F',
    age: 8,
    lifespan: 60,
    power: 20,
    swim: 20,
    wit: 20,
    warmth: 40,
    status: 'ok',
    statusTurns: 0,
    hunger: 0,
    action: 'krill',
    mateId: null,
    nest: 0,
    generation: 1,
    ...extra,
  };
}

/** A new game whose tribe is replaced by `ps` (chief = first). */
export function game(ps: Penguin[], extra: Partial<GameState> = {}): GameState {
  const s = newGame(42);
  s.penguins = ps;
  s.chiefId = ps[0]?.id ?? 0;
  s.nextId = 100;
  return Object.assign(s, extra);
}

