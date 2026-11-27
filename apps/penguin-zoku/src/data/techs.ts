import type { TechId } from '../game/types';

export interface TechDef {
  id: TechId;
  name: string;
  /** Leisure points needed once it becomes the research target. */
  cost: number;
  /** Tech that must be known first. */
  requires: TechId | null;
  desc: string;
}

export const TECHS: readonly TechDef[] = [
  { id: 'mori', name: '骨のモリ', cost: 8, requires: null,
    desc: 'しごと「モリづくり」ができるようになる。モリを持って漁に出ると魚がたくさんとれる。素手で何度か漁をしないと思いつかない。' },
  { id: 'kotoba', name: 'ことば', cost: 20, requires: null,
    desc: 'ほかの群れと話し合えるようになる。族長のまとめる力が強くなり、ひながかしこく生まれる。' },
  { id: 'umo', name: '羽づくろい', cost: 15, requires: null,
    desc: '羽の手入れをおぼえ、寒さにぐっと強くなる。' },
  { id: 'togi', name: 'モリみがき', cost: 25, requires: 'mori',
    desc: 'モリをとがらせる。モリで漁をしたときにとれる魚が1.5倍になる。' },
  { id: 'uta', name: 'よびうた', cost: 20, requires: 'kotoba',
    desc: 'つがいの相手を声で呼びあう。つがいができやすく、ひなも生まれやすくなる。' },
];

export function techDef(id: TechId): TechDef {
  return TECHS.find((t) => t.id === id) as TechDef;
}
