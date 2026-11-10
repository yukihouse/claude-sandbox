import type { FloaterTone, Owner } from '../types';

export interface Palette {
  owner: Record<Owner, string>;
  ink: string;
  paper: string;
  terrain: string;
}

export const UI_FONT = '"Zen Kaku Gothic New", "Hiragino Sans", system-ui, sans-serif';
export const DISPLAY_FONT = '"Shippori Mincho B1", "Hiragino Mincho ProN", serif';

/**
 * Canvas colours. They match the custom properties in style.css (a test keeps
 * them in sync) but are not read from CSS at runtime: a stylesheet that is not
 * applied yet gives empty strings, and the canvas then draws everything black.
 */
export const PALETTE: Readonly<Palette> = {
  // 2 ブリザード: a dark storm violet. 3 流氷: sea-ice teal (also drawn as a hexagon,
  // so the two never depend on colour alone).
  owner: { 0: '#86929b', 1: '#2a63a8', 2: '#4a2d63', 3: '#258a7a' },
  ink: '#18242e',
  paper: '#f5f8fa',
  terrain: '#dde8ee',
};

/** The style.css custom property each canvas colour mirrors. */
export const CSS_VARS: Readonly<Record<string, string>> = {
  '--neutral': PALETTE.owner[0],
  '--player': PALETTE.owner[1],
  '--blizzard': PALETTE.owner[2],
  '--floe': PALETTE.owner[3],
  '--ink': PALETTE.ink,
  '--tray': PALETTE.paper,
  '--terrain': PALETTE.terrain,
};

export const toneColor = (p: Palette, tone: FloaterTone): string => (tone === 'player' ? p.owner[1] : p.ink);
