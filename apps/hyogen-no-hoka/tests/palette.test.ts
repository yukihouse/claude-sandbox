import { afterEach, describe, expect, it, vi } from 'vitest';
import { readPalette, toneColor } from '../src/render/palette';

const css: Record<string, string> = {
  '--neutral': '#86929b',
  '--player': '#2a63a8',
  '--enemy': '#b8432c',
  '--bandit': '#ad7e1a',
  '--ink': '#18242e',
  '--tray': '#f5f8fa',
  '--terrain': '#dde8ee',
};

afterEach(() => vi.unstubAllGlobals());

describe('readPalette', () => {
  it('maps the CSS custom properties to canvas colours', () => {
    const p = readPalette((name) => css[name] ?? '');
    expect(p).toEqual({
      owner: { 0: '#86929b', 1: '#2a63a8', 2: '#b8432c', 3: '#ad7e1a' },
      ink: '#18242e',
      paper: '#f5f8fa',
      terrain: '#dde8ee',
    });
  });

  it('returns null while any colour is still missing (stylesheet not applied yet)', () => {
    expect(readPalette(() => '')).toBeNull();
    expect(readPalette((name) => (name === '--terrain' ? '' : (css[name] ?? '')))).toBeNull();
  });

  it('reads the document root by default, trimming whitespace', () => {
    const root = {};
    vi.stubGlobal('document', { documentElement: root });
    vi.stubGlobal('getComputedStyle', (el: unknown) => {
      expect(el).toBe(root);
      return { getPropertyValue: (name: string) => ` ${css[name] ?? ''} ` };
    });
    expect(readPalette()?.terrain).toBe('#dde8ee');
  });
});

describe('toneColor', () => {
  it('uses the player colour or ink', () => {
    const p = readPalette((name) => css[name] ?? '');
    expect(p && toneColor(p, 'player')).toBe('#2a63a8');
    expect(p && toneColor(p, 'ink')).toBe('#18242e');
  });
});
