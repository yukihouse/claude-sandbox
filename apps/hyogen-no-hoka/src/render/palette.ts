import type { FloaterTone, Owner } from '../types';

export interface Palette {
  owner: Record<Owner, string>;
  ink: string;
  paper: string;
  terrain: string;
}

export const UI_FONT = '"Zen Kaku Gothic New", "Hiragino Sans", system-ui, sans-serif';
export const DISPLAY_FONT = '"Shippori Mincho B1", "Hiragino Mincho ProN", serif';

/** Colours come from the CSS custom properties in style.css. */
export function readPalette(root: Element = document.documentElement): Palette {
  const style = getComputedStyle(root);
  const v = (name: string) => style.getPropertyValue(name).trim();
  return {
    owner: { 0: v('--neutral'), 1: v('--player'), 2: v('--enemy'), 3: v('--bandit') },
    ink: v('--ink'),
    paper: v('--tray'),
    terrain: v('--terrain'),
  };
}

export const toneColor = (p: Palette, tone: FloaterTone): string => (tone === 'player' ? p.owner[1] : p.ink);
