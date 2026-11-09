export const STORE_KEY = 'hyogen-no-hoka:v1';

export interface Progress {
  /** Number of chapters that can be played (1-based). */
  unlocked: number;
  /** Indexes of chapters won at least once. */
  cleared: number[];
}

type Store = Pick<Storage, 'getItem' | 'setItem'>;

const fresh = (): Progress => ({ unlocked: 1, cleared: [] });

/** Read saved progress; anything missing or malformed starts from chapter one. */
export function loadProgress(store: Store | null): Progress {
  if (!store) return fresh();
  let saved: unknown;
  try {
    saved = JSON.parse(store.getItem(STORE_KEY) ?? 'null');
  } catch {
    return fresh();
  }
  if (!saved || typeof saved !== 'object') return fresh();
  const { unlocked, cleared } = saved as Partial<Record<keyof Progress, unknown>>;
  if (typeof unlocked !== 'number' || !(unlocked >= 1)) return fresh();
  return {
    unlocked: Math.floor(unlocked),
    cleared: Array.isArray(cleared) ? cleared.filter((n): n is number => Number.isInteger(n)) : [],
  };
}

export function saveProgress(store: Store | null, p: Progress): void {
  try {
    store?.setItem(STORE_KEY, JSON.stringify(p));
  } catch {
    // storage full or blocked: progress just isn't kept
  }
}

/** Mark chapter `i` won and unlock the next one. */
export function recordWin(p: Progress, i: number, total: number): void {
  p.unlocked = Math.max(p.unlocked, Math.min(total, i + 2));
  if (!p.cleared.includes(i)) p.cleared.push(i);
}

/** Index of the chapter "つづきから" starts. */
export const nextChapter = (p: Progress, total: number): number => Math.min(p.unlocked, total) - 1;
