export type RegionId = 'peninsula' | 'weddell' | 'lutzow' | 'prydz' | 'adelie' | 'ross' | 'amundsen';
export type ActionId = 'krill' | 'fish' | 'craft' | 'rest' | 'pray';
export type StatusId = 'ok' | 'injured' | 'sick';
export type TechId = 'mori' | 'kotoba' | 'umo' | 'togi' | 'uta';
export type Sex = 'M' | 'F';

export interface Penguin {
  id: number;
  name: string;
  sex: Sex;
  /** Age in seasons (4 seasons = 1 year). */
  age: number;
  /** Dies of old age when `age` reaches this. */
  lifespan: number;
  /** ちから: fighting and fending off danger. */
  power: number;
  /** およぎ: how much krill and fish it brings back. */
  swim: number;
  /** ちえ: tool making and inventions. Reaching SAPIENS_WIT at birth wins. */
  wit: number;
  /** さむさ: resistance to cold. */
  warmth: number;
  status: StatusId;
  /** Seasons left until injured/sick recovers. */
  statusTurns: number;
  /** Seasons in a row without enough food. */
  hunger: number;
  action: ActionId;
  mateId: number | null;
  /** Seasons until this female can raise another chick. */
  nest: number;
  generation: number;
}

export interface RegionState {
  krill: number;
  fish: number;
  /** Seasons an orca pod stays in this region. */
  orca: number;
}

export interface GameState {
  version: 1;
  seed: number;
  /** Seasons elapsed; season of the year is turn % 4. */
  turn: number;
  regionId: RegionId;
  regions: Record<RegionId, RegionState>;
  food: number;
  /** Bone spears; each fishing trip with one uses it up. */
  tools: number;
  techs: TechId[];
  research: { target: TechId | null; points: number };
  /** Fishing trips made without a spear (needed before the spear can be invented). */
  bareHunts: number;
  penguins: Penguin[];
  chiefId: number;
  nextId: number;
  /** Region the tribe migrates to when the season advances. */
  moveTo: RegionId | null;
  /** Seasons left in a cold wave. */
  coldwave: number;
  over: null | 'win' | 'lose';
  maxGeneration: number;
  births: number;
  deaths: number;
  /** Name of the chick that won the game. */
  sapiens: string | null;
}
