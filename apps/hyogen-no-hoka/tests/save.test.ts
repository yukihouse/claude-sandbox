import { describe, expect, it } from 'vitest';
import { loadProgress, nextChapter, recordWin, saveProgress, STORE_KEY } from '../src/save';

const store = (value: string | null) => {
  const data = new Map<string, string>();
  if (value !== null) data.set(STORE_KEY, value);
  return {
    data,
    getItem: (k: string) => data.get(k) ?? null,
    setItem: (k: string, v: string) => void data.set(k, v),
  };
};

describe('loadProgress', () => {
  it('starts fresh without storage or saved data', () => {
    expect(loadProgress(null)).toEqual({ unlocked: 1, cleared: [] });
    expect(loadProgress(store(null))).toEqual({ unlocked: 1, cleared: [] });
  });

  it('reads saved progress', () => {
    expect(loadProgress(store('{"unlocked":3,"cleared":[0,1]}'))).toEqual({ unlocked: 3, cleared: [0, 1] });
    expect(loadProgress(store('{"unlocked":2}'))).toEqual({ unlocked: 2, cleared: [] });
  });

  it('ignores malformed data', () => {
    for (const bad of ['{', '5', '"x"', '{"unlocked":0}', '{"unlocked":"3"}', '{}']) {
      expect(loadProgress(store(bad)), bad).toEqual({ unlocked: 1, cleared: [] });
    }
    expect(loadProgress(store('{"unlocked":2.7,"cleared":[0,"1",1.5,2]}'))).toEqual({
      unlocked: 2,
      cleared: [0, 2],
    });
  });
});

describe('saveProgress', () => {
  it('writes JSON under the store key', () => {
    const s = store(null);
    saveProgress(s, { unlocked: 2, cleared: [0] });
    expect(loadProgress(s)).toEqual({ unlocked: 2, cleared: [0] });
  });

  it('survives missing or failing storage', () => {
    expect(() => saveProgress(null, { unlocked: 1, cleared: [] })).not.toThrow();
    const full = {
      getItem: () => null,
      setItem: () => {
        throw new Error('QuotaExceededError');
      },
    };
    expect(() => saveProgress(full, { unlocked: 1, cleared: [] })).not.toThrow();
  });
});

describe('recordWin / nextChapter', () => {
  it('unlocks the next chapter once and caps at the last', () => {
    const p = { unlocked: 1, cleared: [] as number[] };
    recordWin(p, 0, 5);
    recordWin(p, 0, 5);
    expect(p).toEqual({ unlocked: 2, cleared: [0] });
    expect(nextChapter(p, 5)).toBe(1);
    recordWin(p, 4, 5);
    expect(p.unlocked).toBe(5);
    expect(nextChapter({ unlocked: 9, cleared: [] }, 5)).toBe(4);
  });

  it('does not re-lock when replaying an earlier chapter', () => {
    const p = { unlocked: 4, cleared: [0, 1, 2] };
    recordWin(p, 0, 5);
    expect(p).toEqual({ unlocked: 4, cleared: [0, 1, 2] });
  });
});
