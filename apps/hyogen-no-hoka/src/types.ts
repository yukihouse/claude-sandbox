/** 0 無人 / 1 自軍の探検隊・観測隊 (player) / 2 ブリザード / 3 流氷 */
export type Owner = 0 | 1 | 2 | 3;
/** AI-controlled factions: the Antarctic weather and ice, never other people. */
export type AiOwner = 2 | 3;
/** 1 観測小屋 / 2 基地 / 3 本部 */
export type Level = 1 | 2 | 3;
export type ItemKind = 'reinforce' | 'gale' | 'wall';
/** Items that are used on one of the player's bases. */
export type TargetItem = Exclude<ItemKind, 'gale'>;
export type CharId = 'narr' | 'nagi' | 'minato' | 'gen' | 'log';
export type Point = readonly [x: number, y: number];
/**
 * What the chapter's map looks like: the Ross Ice Shelf by the sea, mountains
 * and a glacier, the open Weddell Sea with ice floes, sea ice off an island,
 * or the flat inland plateau.
 */
export type TerrainKind = 'shelf' | 'glacier' | 'sea' | 'coast' | 'plateau';
/** Tents and depots (the early expeditions) or the buildings of a research station. */
export type BaseStyle = 'camp' | 'station';
/** A place name printed on the map. */
export type Place = readonly [x: number, y: number, name: string];

export interface Character {
  name: string;
  role: string;
}

export type StoryLine = readonly [who: CharId, text: string];

/** A crevasse field: crossing one halves movement speed. */
export interface River {
  w: number;
  pts: readonly Point[];
}

export interface AiConfig {
  /** Seconds between decisions (randomised ±25%). */
  interval: number;
  /** How many more troops than needed the AI sends. */
  greed: number;
  /** How strongly the AI prefers attacking the player. */
  focus: number;
}

export type CastleDef = readonly [x: number, y: number, owner: Owner, level: Level, troops: number];

export interface StageDef {
  no: string;
  name: string;
  /** The years of the real expedition the chapter retells, e.g. '1910–1912'. */
  era: string;
  /** Result text after a win. */
  win: string;
  terrain: TerrainKind;
  bases: BaseStyle;
  places: readonly Place[];
  castles: readonly CastleDef[];
  rivers: readonly River[];
  ai: AiConfig;
  items: Readonly<Record<ItemKind, number>>;
  pre: readonly StoryLine[];
  post: readonly StoryLine[];
}

export interface Castle {
  id: number;
  x: number;
  y: number;
  owner: Owner;
  level: Level;
  troops: number;
  /** Game time until which the 防寒壁 doubles defence. */
  wallUntil: number;
  /** Capture flash, 1 → 0. */
  flash: number;
}

export interface Army {
  owner: Owner;
  n: number;
  /** Target castle id. */
  to: number;
  x: number;
  y: number;
}

export type FloaterTone = 'player' | 'ink';

export interface Floater {
  x: number;
  y: number;
  text: string;
  tone: FloaterTone;
  age: number;
}

export interface GameState {
  /** Stage index into STAGES. */
  i: number;
  stage: StageDef;
  t: number;
  running: boolean;
  paused: boolean;
  over: boolean;
  endAt: number | null;
  result: 'win' | 'lose' | null;
  castles: Castle[];
  armies: Army[];
  floaters: Floater[];
  aiTimer: Record<AiOwner, number>;
  items: Record<ItemKind, number>;
  galeUntil: number;
  selected: number | null;
  /** An item waiting for the player to tap a target base. */
  mode: TargetItem | null;
  captured: number;
}
