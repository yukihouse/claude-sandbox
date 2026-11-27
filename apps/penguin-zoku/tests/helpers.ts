import { neighbors } from '../src/data/regions';
import {
  canWork, chief, hasTech, moveBlock, moveCost, resolveSeason, setAction, setMove,
} from '../src/game/rules';
import type { GameState, Penguin } from '../src/game/types';

/** A simple player that gives sensible orders each season (used for balance tests). */
export function autoOrders(s: GameState): void {
  const reg = s.regions[s.regionId];

  const workers = s.penguins.filter(canWork);
  const c = chief(s);
  const need = s.penguins.length;
  // Leave when food here is running out and we can afford it.
  if (reg.krill + reg.fish < need * 1.5 || reg.orca > 0) {
    const best = neighbors(s.regionId)
      .filter((r) => !moveBlock(s, r))
      .sort((a, b) => s.regions[b].krill + s.regions[b].fish - (s.regions[a].krill + s.regions[a].fish))[0];
    if (best && s.regions[best].krill + s.regions[best].fish > need * 3 && s.food >= moveCost(s) + need) {
      setMove(s, best);
      return;
    }
  }
  const enough = s.food >= need * 2;
  workers.forEach((p: Penguin, i) => {
    let a: Penguin['action'];
    const rest = enough ? i % 2 === 0 : i % 4 === 0;
    if (rest) a = 'rest';
    else if (hasTech(s, 'mori') && s.tools < 4 && i % 3 === 1) a = 'craft';
    else if ((s.tools > 0 || s.bareHunts < 3) && reg.fish > 5 && i % 3 === 0) a = 'fish';
    else a = 'krill';
    setAction(s, p.id, a);
  });
  if (c && canWork(c) && enough && s.penguins.some((p) => p.status !== 'ok')) setAction(s, c.id, 'pray');

}

/** Play up to `max` seasons with autoOrders. */
export function autoplay(s: GameState, max: number): GameState {
  for (let i = 0; i < max && !s.over; i++) {
    autoOrders(s);
    resolveSeason(s);
  }
  return s;
}
