import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { CSS_VARS, PALETTE, toneColor } from '../src/render/palette';

describe('PALETTE', () => {
  it('matches the colours in style.css', () => {
    const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8');
    const root = css.match(/:root\s*\{([^}]*)\}/)?.[1] ?? '';
    for (const [name, colour] of Object.entries(CSS_VARS)) {
      expect(root, name).toMatch(new RegExp(`${name}:\\s*${colour};`));
    }
  });

  it('gives floaters the player colour or ink', () => {
    expect(toneColor(PALETTE, 'player')).toBe('#2a63a8');
    expect(toneColor(PALETTE, 'ink')).toBe('#18242e');
  });
});
