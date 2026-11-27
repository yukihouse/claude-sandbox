import { REGIONS } from './data/regions';
import { TECHS } from './data/techs';
import type { GameState } from './game/types';

export const STORE_KEY = 'penguin-zoku:v1';

type Store = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const PENGUIN_NUMS = ['id', 'age', 'lifespan', 'power', 'swim', 'wit', 'warmth', 'statusTurns', 'hunger', 'nest', 'generation'] as const;
const ACTIONS = ['krill', 'fish', 'craft', 'rest', 'pray'];
const STATUSES = ['ok', 'injured', 'sick'];
const regionIds: string[] = REGIONS.map((r) => r.id);
const techIds: string[] = TECHS.map((t) => t.id);

function validPenguin(v: unknown): boolean {
  if (!v || typeof v !== 'object') return false;
  const p = v as Record<string, unknown>;
  return (
    PENGUIN_NUMS.every((k) => isNum(p[k])) &&
    typeof p.name === 'string' &&
    (p.sex === 'M' || p.sex === 'F') &&
    STATUSES.includes(p.status as string) &&
    ACTIONS.includes(p.action as string) &&
    (p.mateId === null || isNum(p.mateId))
  );
}

/** Check that `v` has the shape of a saved game, so a broken save never crashes the game. */
export function isGameState(v: unknown): v is GameState {
  if (!v || typeof v !== 'object') return false;
  const s = v as Record<string, unknown>;
  if (s.version !== 1) return false;
  if (!['seed', 'turn', 'food', 'tools', 'bareHunts', 'chiefId', 'nextId', 'coldwave', 'maxGeneration', 'births', 'deaths'].every((k) => isNum(s[k]))) return false;
  if (!regionIds.includes(s.regionId as string)) return false;
  if (s.moveTo !== null && !regionIds.includes(s.moveTo as string)) return false;
  if (s.over !== null) return false;
  const regions = s.regions as Record<string, unknown> | null;
  if (!regions || typeof regions !== 'object') return false;
  for (const id of regionIds) {
    const r = regions[id] as Record<string, unknown> | undefined;
    if (!r || !isNum(r.krill) || !isNum(r.fish) || !isNum(r.orca)) return false;
  }
  if (!Array.isArray(s.techs) || !s.techs.every((t) => techIds.includes(t as string))) return false;
  const research = s.research as Record<string, unknown> | null;
  if (!research || typeof research !== 'object' || !isNum(research.points)) return false;
  if (research.target !== null && !techIds.includes(research.target as string)) return false;
  if (!Array.isArray(s.penguins) || !s.penguins.length || !s.penguins.every(validPenguin)) return false;
  return true;
}

/** The saved game in progress, or null when there is none or it is unreadable. */
export function loadGame(store: Store | null): GameState | null {
  if (!store) return null;
  try {
    const v: unknown = JSON.parse(store.getItem(STORE_KEY) ?? 'null');
    return isGameState(v) ? v : null;
  } catch {
    return null;
  }
}

/** Save a game in progress; a finished game clears the save instead. */
export function saveGame(store: Store | null, s: GameState): void {
  try {
    if (s.over) store?.removeItem(STORE_KEY);
    else store?.setItem(STORE_KEY, JSON.stringify(s));
  } catch {
    // storage full or blocked: the game just isn't kept
  }
}
