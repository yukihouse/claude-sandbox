import { LEVEL, SPEED } from '../config';
import type { AiOwner, Army, Castle, GameState } from '../types';
import { dist } from './geometry';
import { defMult, incoming, send } from './rules';

/** One decision for an AI faction: defend, attack, or move troops to the front. */
export function aiThink(S: GameState, owner: AiOwner): void {
  const ai = S.stage.ai;
  const cs = S.castles;
  const mine = cs.filter((c) => c.owner === owner);
  if (!mine.length) return;
  const hostileTo = (a: Army) => a.owner !== owner;
  const friendly = (a: Army) => a.owner === owner;

  // 1. shore up a castle that is about to fall
  for (const c of mine) {
    const shortfall = incoming(S, c, hostileTo) - incoming(S, c, friendly) - c.troops * defMult(S, c);
    if (shortfall > -2) {
      const helper = mine
        .filter((m) => m !== c && m.troops > 12)
        .sort((a, b) => dist(a, c) - dist(b, c))[0];
      if (helper && dist(helper, c) / SPEED < 7) {
        // Always at least 5 and affordable: helpers have > 12 troops and shortfall > -2.
        send(S, helper, c, Math.min(Math.floor(helper.troops - 4), Math.ceil(shortfall + 6)));
        return;
      }
    }
  }

  // 2. attack the best-value reachable target
  let best: { s: Castle; t: Castle; n: number; score: number } | null = null;
  for (const s of mine) {
    const reserve = Math.max(3, s.troops * 0.3, incoming(S, s, hostileTo) - incoming(S, s, friendly));
    const avail = Math.floor(s.troops - reserve);
    if (avail < 6) continue;
    for (const t of cs) {
      if (t.owner === owner) continue;
      const d = dist(s, t);
      const travel = d / SPEED;
      let est = t.troops * defMult(S, t) + (t.owner !== 0 ? LEVEL[t.level].rate * travel : 0);
      est += incoming(S, t, (a) => a.owner === t.owner) - incoming(S, t, friendly);
      if (est < 0) continue;
      const n = Math.min(avail, Math.ceil(est * ai.greed) + 3);
      if (n <= est + 1) continue;
      const value = t.level * 1.4 + (t.owner === 1 ? ai.focus : t.owner === 0 ? 0.7 : 0.9);
      const score = value / (0.25 + d) / (1 + est * 0.03);
      if (!best || score > best.score) best = { s, t, n, score };
    }
  }
  if (best) {
    send(S, best.s, best.t, best.n);
    return;
  }

  // 3. move idle troops from the rear to the front
  const foes = cs.filter((c) => c.owner !== owner && c.owner !== 0);
  if (!foes.length || mine.length < 2) return;
  const front = (c: Castle) => Math.min(...foes.map((f) => dist(c, f)));
  const sorted = mine.slice().sort((a, b) => front(a) - front(b));
  const frontline = sorted[0] as Castle;
  for (const c of sorted.slice(1).reverse()) {
    if (c.troops >= LEVEL[c.level].cap * 0.85) {
      send(S, c, frontline, c.troops * 0.6);
      return;
    }
  }
}
