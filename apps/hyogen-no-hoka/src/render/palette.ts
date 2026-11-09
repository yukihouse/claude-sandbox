import type { FloaterTone, Owner } from '../types';

export interface Palette {
  owner: Record<Owner, string>;
  ink: string;
  paper: string;
  terrain: string;
}

export const UI_FONT = '"Zen Kaku Gothic New", "Hiragino Sans", system-ui, sans-serif';
export const DISPLAY_FONT = '"Shippori Mincho B1", "Hiragino Mincho ProN", serif';

const cssVar = (name: string): string =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/**
 * Colours come from the CSS custom properties in style.css. Returns null while
 * any of them is still empty (the stylesheet is not applied yet): drawing with
 * an empty colour silently keeps the canvas default, black.
 */
export function readPalette(get: (name: string) => string = cssVar): Palette | null {
  const p: Palette = {
    owner: { 0: get('--neutral'), 1: get('--player'), 2: get('--enemy'), 3: get('--bandit') },
    ink: get('--ink'),
    paper: get('--tray'),
    terrain: get('--terrain'),
  };
  const all = [...Object.values(p.owner), p.ink, p.paper, p.terrain];
  return all.every((c) => c !== '') ? p : null;
}

export const toneColor = (p: Palette, tone: FloaterTone): string => (tone === 'player' ? p.owner[1] : p.ink);
