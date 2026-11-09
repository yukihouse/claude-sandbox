import type { Level } from './types';

/** World size (landscape); portrait screens rotate it. */
export const W = 1.5;
export const H = 1;
/** World units per second. */
export const SPEED = 0.11;
/** Armies closer than this fight. */
export const CLASH = 0.026;
/** Longest simulation step, in seconds. */
export const MAX_DT = 0.05;
/** Seconds between the end condition and the result screen. */
export const END_DELAY = 0.9;
/** Seconds a floating label stays on screen. */
export const FLOATER_LIFE = 1.3;

export const REINFORCE_TROOPS = 15;
export const GALE_SECONDS = 12;
export const WALL_SECONDS = 20;

export interface LevelStats {
  /** Troops stop growing here. */
  cap: number;
  /** Troops gained per second. */
  rate: number;
  /** Radius in world units. */
  r: number;
}

export const LEVEL: Readonly<Record<Level, LevelStats>> = {
  1: { cap: 30, rate: 0.8, r: 0.034 },
  2: { cap: 50, rate: 1.2, r: 0.04 },
  3: { cap: 90, rate: 1.7, r: 0.048 },
};
