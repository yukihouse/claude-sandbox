import type { Owner, StageDef } from '../types';

/** What each owner stands for, as shown in the map legend. */
export const FACTIONS: Readonly<Record<Owner, string>> = {
  0: '無人',
  1: '自軍',
  2: 'ブリザード',
  3: '流氷',
};

/** The owners present at the start of a stage, in legend order. */
export const ownersIn = (stage: StageDef): Owner[] =>
  ([1, 2, 3, 0] as const).filter((o) => stage.castles.some((c) => c[2] === o));
