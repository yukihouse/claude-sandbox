import { GALE_SECONDS, REINFORCE_TROOPS, WALL_SECONDS } from '../config';
import type { Castle, GameState, ItemKind, TargetItem } from '../types';
import { castleAt, floater, send } from './rules';

export function select(S: GameState, c: Castle): void {
  S.selected = c.id;
  S.mode = null;
}

export function deselect(S: GameState): void {
  S.selected = null;
}

export function selectedCastle(S: GameState): Castle | null {
  return S.selected === null ? null : castleAt(S, S.selected);
}

/** Troops sent from `c` at `pct` percent. */
export const sendCount = (c: Castle, pct: number): number => Math.floor((c.troops * pct) / 100);

export function sendRatio(S: GameState, from: Castle, to: Castle, pct: number): boolean {
  const n = sendCount(from, pct);
  if (n < 1) {
    floater(S, from, '隊員が足りない', 'ink');
    return false;
  }
  return send(S, from, to, n);
}

/** Whole seconds of 雪上車 left (0 or less when inactive). */
export const galeLeft = (S: GameState): number => Math.ceil(S.galeUntil - S.t);

/** Press an item button. */
export function useItem(S: GameState, kind: ItemKind): void {
  if (!S.running || S.items[kind] <= 0) return;
  if (kind === 'gale') {
    S.items.gale--;
    S.galeUntil = Math.max(S.galeUntil, S.t) + GALE_SECONDS;
    return;
  }
  if (S.mode === kind) {
    S.mode = null;
    return;
  }
  const sel = selectedCastle(S);
  if (sel) {
    applyItem(S, kind, sel);
    return;
  }
  S.mode = kind;
}

export function applyItem(S: GameState, kind: TargetItem, c: Castle): void {
  if (c.owner !== 1 || S.items[kind] <= 0) return;
  S.items[kind]--;
  if (kind === 'reinforce') {
    c.troops += REINFORCE_TROOPS;
    floater(S, c, `+${REINFORCE_TROOPS}`, 'player');
  } else {
    c.wallUntil = Math.max(c.wallUntil, S.t) + WALL_SECONDS;
    floater(S, c, '防寒壁', 'player');
  }
  S.mode = null;
}

/** A press on the map while an item waits for its target. */
export function tapInItemMode(S: GameState, kind: TargetItem, c: Castle | null): void {
  if (c && c.owner === 1) applyItem(S, kind, c);
  else S.mode = null;
}

/**
 * Pointer released on castle `c` (or empty ground).
 * `dragFrom` is the castle a drag started from, if the pointer moved far enough.
 */
export function release(S: GameState, dragFrom: Castle | null, c: Castle | null, pct: number): void {
  if (dragFrom) {
    if (c && c !== dragFrom && dragFrom.owner === 1) sendRatio(S, dragFrom, c, pct);
    deselect(S);
    return;
  }
  const sel = selectedCastle(S);
  if (sel) {
    if (c && c !== sel && sel.owner === 1) {
      sendRatio(S, sel, c, pct);
      deselect(S);
    } else if (c && c.owner === 1 && c !== sel) select(S, c);
    else deselect(S);
  } else if (c && c.owner === 1) select(S, c);
}
