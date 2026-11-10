import { describe, expect, it } from 'vitest';
import { H, W } from '../src/config';
import { CHARS } from '../src/data/chars';
import { FACTIONS, ownersIn } from '../src/data/factions';
import { PORTRAITS } from '../src/data/portraits';
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
    for (const [x, y, name] of s.places) {
      expect(name).not.toBe('');
      expect(x).toBeGreaterThan(0);
      expect(x).toBeLessThan(W);
      expect(y).toBeGreaterThan(0);
      expect(y).toBeLessThan(H);
      // place names stay clear of the bases
      for (const [cx, cy] of s.castles) expect(Math.hypot(cx - x, cy - y)).toBeGreaterThan(0.12);
    }
    expect(s.pre.length).toBeGreaterThan(0);
    expect(s.post.length).toBeGreaterThan(0);
  });
});

describe('factions', () => {
  it('names every owner', () => {
    expect(Object.values(FACTIONS)).toEqual(['無人', '自軍', 'ブリザード', '流氷']);
  });

  it('lists the owners on a stage, player first and unmanned last', () => {
    expect(ownersIn(STAGES[0]!)).toEqual([1, 2, 0]);
    expect(ownersIn(STAGES[2]!)).toEqual([1, 2, 3, 0]);
  });

  it('draws early expeditions as camps and later ones as stations', () => {
    expect(STAGES.map((s) => s.bases)).toEqual(['camp', 'camp', 'camp', 'station', 'station']);
    expect(STAGES.map((s) => s.terrain)).toEqual(['shelf', 'glacier', 'sea', 'coast', 'plateau']);
  });
});

describe('portraits', () => {
  it('gives every speaker but the narrator an SVG portrait named after them', () => {
    const speakers = Object.keys(CHARS).filter((id) => id !== 'narr');
    expect(Object.keys(PORTRAITS).sort()).toEqual(speakers.sort());
    for (const [id, svg] of Object.entries(PORTRAITS)) {
      expect(svg).toMatch(/^<svg [^>]*viewBox="0 0 60 80"/);
      expect(svg).toContain(`aria-label="${CHARS[id as keyof typeof CHARS].name}"`);
      expect(svg.endsWith('</svg>')).toBe(true);
    }
  });

  it('keeps gradient ids unique, since all portraits share one page', () => {
    const ids = Object.values(PORTRAITS).flatMap((svg) => [...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]));
    expect(new Set(ids).size).toBe(ids.length);
  });
});
