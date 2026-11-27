import type { RegionId } from '../game/types';

export interface RegionDef {
  id: RegionId;
  name: string;
  krillMax: number;
  fishMax: number;
  /** Base cold; winter and cold waves add to it. */
  cold: number;
  /** Multiplier on how often orcas show up. */
  orca: number;
  /** Multiplier on how often other colonies show up. */
  rival: number;
  note: string;
}

/** Regions in order around the coast of Antarctica; the tribe moves to a neighbour. */
export const REGIONS: readonly RegionDef[] = [
  { id: 'peninsula', name: '南極半島', krillMax: 45, fishMax: 20, cold: 0, orca: 1, rival: 1.5,
    note: '南極でいちばん暖かい土地。オキアミが多く、ほかの群れも多い。' },
  { id: 'weddell', name: 'ウェッデル海', krillMax: 30, fishMax: 30, cold: 15, orca: 1, rival: 1,
    note: '厚い海氷にかこまれた海。氷がせまってくると逃げ場がない。' },
  { id: 'lutzow', name: 'リュツォ・ホルム湾', krillMax: 25, fishMax: 30, cold: 15, orca: 0.5, rival: 0.5,
    note: '日本の昭和基地がある湾。おだやかだが、えさはほどほど。' },
  { id: 'prydz', name: 'プリッツ湾', krillMax: 35, fishMax: 25, cold: 20, orca: 1, rival: 1,
    note: '大きな氷河が海に流れこむ湾。オキアミがよく集まる。' },
  { id: 'adelie', name: 'アデリーランド', krillMax: 30, fishMax: 20, cold: 10, orca: 0.5, rival: 1,
    note: 'アデリーペンギンの名前のもとになった土地。風が強い。' },
  { id: 'ross', name: 'ロス海', krillMax: 35, fishMax: 45, cold: 25, orca: 2, rival: 0.5,
    note: '魚がとても多い豊かな海。そのぶんシャチも多い。' },
  { id: 'amundsen', name: 'アムンゼン海', krillMax: 20, fishMax: 25, cold: 10, orca: 1, rival: 0.5,
    note: '人もペンギンもあまり来ない、静かな海。' },
];

export function regionDef(id: RegionId): RegionDef {
  return REGIONS.find((r) => r.id === id) as RegionDef;
}

/** The two regions next to `id` along the coast. */
export function neighbors(id: RegionId): RegionId[] {
  const i = REGIONS.findIndex((r) => r.id === id);
  const n = REGIONS.length;
  return [(REGIONS[(i + n - 1) % n] as RegionDef).id, (REGIONS[(i + 1) % n] as RegionDef).id];
}
