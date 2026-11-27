import { describe, expect, it } from 'vitest';
import { NAMES, zenkaku } from '../src/data/names';
import { REGIONS, neighbors, regionDef } from '../src/data/regions';
import { TECHS, techDef } from '../src/data/techs';

describe('regions', () => {
  it('form a ring around the coast', () => {
    expect(neighbors('peninsula')).toEqual(['amundsen', 'weddell']);
    expect(neighbors('amundsen')).toEqual(['ross', 'peninsula']);
    for (const r of REGIONS) {
      for (const n of neighbors(r.id)) expect(neighbors(n)).toContain(r.id);
    }
  });

  it('have unique ids and sane numbers', () => {
    expect(new Set(REGIONS.map((r) => r.id)).size).toBe(REGIONS.length);
    for (const r of REGIONS) {
      expect(regionDef(r.id)).toBe(r);
      expect(r.krillMax).toBeGreaterThan(0);
      expect(r.fishMax).toBeGreaterThan(0);
      expect(r.note.length).toBeGreaterThan(0);
    }
  });
});

describe('techs', () => {
  it('only require techs listed earlier', () => {
    TECHS.forEach((t, i) => {
      expect(techDef(t.id)).toBe(t);
      if (t.requires) expect(TECHS.slice(0, i).map((x) => x.id)).toContain(t.requires);
    });
  });
});

describe('names', () => {
  it('are unique', () => {
    expect(new Set(NAMES).size).toBe(NAMES.length);
  });

  it('zenkaku converts digits', () => {
    expect(zenkaku(12)).toBe('１２');
    expect(zenkaku(30)).toBe('３０');
  });
});
