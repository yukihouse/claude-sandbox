import { createState } from '../src/game/rules';
import type { CastleDef, GameState, River, StageDef } from '../src/types';

/** A one-off stage built from just the castles (and optionally crevasses) a test needs. */
export function stage(castles: CastleDef[], extra: Partial<StageDef> = {}): StageDef {
  return {
    no: 'テスト',
    name: 'テスト',
    era: '2000–2001',
    win: 'テスト',
    castles,
    rivers: [] as River[],
    ai: { interval: 4, greed: 1.2, focus: 1 },
    items: { reinforce: 1, gale: 1, wall: 1 },
    pre: [],
    post: [],
    ...extra,
  };
}

export function state(castles: CastleDef[], extra: Partial<StageDef> = {}): GameState {
  const S = createState(0, [stage(castles, extra)]);
  S.running = true;
  return S;
}
