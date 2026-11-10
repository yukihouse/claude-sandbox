import { describe, expect, it } from 'vitest';
import { H, W } from '../src/config';
import { CHARS } from '../src/data/chars';
import { STAGES } from '../src/data/stages';
import { inRiver } from '../src/game/geometry';

describe('stage data', () => {
  it('has five chapters', () => {
    expect(STAGES.map((s) => s.no)).toEqual(['第一章', '第二章', '第三章', '第四章', '終章']);
  });

  it.each(STAGES.map((s, i) => [s.name, s, i] as const))('%s is playable', (_name, s) => {
    const owners = new Set(s.castles.map((c) => c[2]));
    expect(owners.has(1)).toBe(true);
    expect([...owners].some((o) => o >= 2)).toBe(true);
    for (const [x, y, , , troops] of s.castles) {
      expect(x).toBeGreaterThan(0);
      expect(x).toBeLessThan(W);
      expect(y).toBeGreaterThan(0);
      expect(y).toBeLessThan(H);
      expect(troops).toBeGreaterThan(0);
      // no base sits inside a crevasse field
      expect(inRiver(s.rivers, x, y)).toBe(false);
    }
    for (const line of [...s.pre, ...s.post]) expect(CHARS[line[0]]).toBeDefined();
    expect(s.era).toMatch(/^\d{4}–(\d{4}|現在)$/);
    expect(s.win).not.toBe('');
    expect(s.pre.length).toBeGreaterThan(0);
    expect(s.post.length).toBeGreaterThan(0);
  });
});
