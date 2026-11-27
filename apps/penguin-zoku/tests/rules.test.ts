import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { GameState } from '../src/game/types';
import { game, penguin } from './fixtures';

// Every random draw comes from `rng.queue`, then `rng.fallback`, so each test controls chance.
const rng = vi.hoisted(() => ({ queue: [] as number[], fallback: 0.99 }));
vi.mock('../src/game/rng', () => {
  const rand = () => (rng.queue.length ? (rng.queue.shift() as number) : rng.fallback);
  return {
    rand,
    randInt: (_s: unknown, min: number, max: number) => min + Math.floor(rand() * (max - min + 1)),
    chance: (_s: unknown, p: number) => rand() < p,
    pick: <T>(_s: unknown, a: readonly T[]) => a[Math.floor(rand() * a.length)] as T,
    shuffle: <T>(_s: unknown, a: readonly T[]) => [...a],
  };
});

const R = await import('../src/game/rules');

beforeEach(() => {
  rng.queue = [];
  rng.fallback = 0.99;
});

/** Run one season with no random event (and the given draws first). */
function season(s: GameState, draws: number[] = []): string[] {
  rng.queue = draws;
  return R.resolveSeason(s);
}

describe('labels and helpers', () => {
  it('formats seasons and ages', () => {
    expect(R.seasonLabel(0)).toBe('1年目 春');
    expect(R.seasonLabel(7)).toBe('2年目 冬');
    expect(R.ageYears(penguin(1, { age: 9 }))).toBe(2);
    expect(R.clampStat(0)).toBe(1);
    expect(R.clampStat(999)).toBe(R.STAT_MAX);
  });

  it('makes unique names', () => {
    const s = game([penguin(1, { name: 'ユキ' }), penguin(2, { name: 'ユキ２世' })]);
    expect(R.uniqueName(s, 'ソラ')).toBe('ソラ');
    expect(R.uniqueName(s, 'ユキ')).toBe('ユキ３世');
  });
});

describe('newGame', () => {
  it('starts six adults, three of each sex, in the peninsula', () => {
    rng.fallback = 0.5;
    const s = R.newGame(1);
    expect(s.penguins).toHaveLength(6);
    expect(s.penguins.filter((p) => p.sex === 'F')).toHaveLength(3);
    expect(s.penguins.every(R.isAdult)).toBe(true);
    expect(s.regionId).toBe('peninsula');
    expect(R.chief(s)).toBeDefined();
    expect(new Set(s.penguins.map((p) => p.name)).size).toBe(6);
  });
});

describe('commands', () => {
  it('explains why an action is blocked', () => {
    const s = game([penguin(1), penguin(2), penguin(3, { age: 1 }), penguin(4, { status: 'sick' })]);
    const [c, p, chick, sick] = s.penguins as [never, never, never, never];
    expect(R.actionBlock(s, chick, 'krill')).toBe('まだひなです');
    expect(R.actionBlock(s, sick, 'krill')).toBe('病気でうごけません');
    expect(R.actionBlock(s, p, 'pray')).toBe('族長だけができます');
    expect(R.actionBlock(s, c, 'pray')).toBeNull();
    expect(R.actionBlock(s, p, 'craft')).toBe('まだ作りかたを知りません');
    s.techs.push('mori');
    expect(R.actionBlock(s, p, 'craft')).toBeNull();
    expect(R.setAction(s, 2, 'fish')).toBe(true);
    expect(R.setAction(s, 99, 'fish')).toBe(false);
    expect(R.setAction(s, 3, 'fish')).toBe(false);
  });

  it('sets everyone at once, but never to prayer', () => {
    const s = game([penguin(1), penguin(2), penguin(3, { age: 1 })]);
    expect(R.setAll(s, 'rest')).toBe(2);
    expect(s.penguins.map((p) => p.action)).toEqual(['rest', 'rest', 'krill']);
    expect(R.setAll(s, 'pray')).toBe(0);
  });

  it('changes chief and drops the old chief out of prayer', () => {
    const s = game([penguin(1, { action: 'pray' }), penguin(2), penguin(3, { age: 1 })]);
    expect(R.setChief(s, 3)).toBe(false);
    expect(R.setChief(s, 99)).toBe(false);
    expect(R.setChief(s, 2)).toBe(true);
    expect(s.chiefId).toBe(2);
    expect(s.penguins[0]!.action).toBe('rest');
    s.chiefId = 99;
    expect(R.setChief(s, 1)).toBe(true);
  });

  it('plans and cancels a move', () => {
    const s = game([penguin(1), penguin(2)], { food: 1 });
    expect(R.moveCost(s)).toBe(2);
    expect(R.moveBlock(s, 'ross')).toBe('となりの土地ではありません');
    expect(R.moveBlock(s, 'weddell')).toBe('食料が足りません（2いる）');
    expect(R.setMove(s, 'weddell')).toBe(false);
    s.food = 2;
    expect(R.setMove(s, 'weddell')).toBe(true);
    expect(s.moveTo).toBe('weddell');
    expect(R.setMove(s, null)).toBe(true);
    expect(s.moveTo).toBeNull();
  });
});

describe('resolveSeason: moving', () => {
  it('migrates instead of working and pays food', () => {
    const s = game([penguin(1), penguin(2)], { food: 10, moveTo: 'weddell' });
    const log = season(s);
    expect(s.regionId).toBe('weddell');
    expect(s.moveTo).toBeNull();
    // 2 to move, 2 to eat, then 10% spoils: floor(6 * 0.9)
    expect(s.food).toBe(5);
    expect(log[0]).toContain('ウェッデル海へひっこした');
    expect(s.turn).toBe(1);
  });

  it('works normally when the planned move became unaffordable', () => {
    const s = game([penguin(1), penguin(2)], { food: 0, moveTo: 'weddell' });
    const log = season(s);
    expect(s.regionId).toBe('peninsula');
    expect(log.some((l) => l.includes('オキアミ'))).toBe(true);
  });

  it('does nothing once the game is over', () => {
    const s = game([penguin(1)], { over: 'lose' });
    expect(season(s)).toEqual([]);
    expect(s.turn).toBe(0);
  });
});

describe('resolveSeason: work', () => {
  it('gathers krill with the chief bonus, limited by what the region has', () => {
    const s = game([penguin(1), penguin(2)]);
    // (2.5 + 20/20) * 1.3 * 2 = 9.1 → 9
    expect(season(s)).toContain('オキアミを9とった。');
    s.regions.peninsula.krill = 3;
    const log = season(s);
    expect(log).toContain('オキアミを3とった。');
    expect(log).toContain('このあたりのオキアミが少なくなってきた……。');
  });

  it('gives no chief bonus when the chief is busy elsewhere or kotoba raises it', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2)]);
    expect(R.chiefBonus(s, s.penguins[1]!)).toBe(1);
    s.penguins[0]!.action = 'krill';
    expect(R.chiefBonus(s, s.penguins[1]!)).toBe(1.3);
    s.techs.push('kotoba');
    expect(R.chiefBonus(s, s.penguins[1]!)).toBe(1.5);
    s.penguins[0]!.status = 'injured';
    expect(R.chiefBonus(s, s.penguins[1]!)).toBe(1);
    s.chiefId = 99;
    expect(R.chiefBonus(s, s.penguins[1]!)).toBe(1);
  });

  it('fishes bare-handed, risks injury and learns from it', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2, { action: 'fish', swim: 30 })]);
    // shoal yes (0), catch randInt(0,2) → 2 (0.99), injury yes (0)
    const log = season(s, [0, 0.99, 0]);
    expect(s.bareHunts).toBe(1);
    expect(log).toContain('魚を3とった。');
    expect(log.some((l) => l.includes('素手で魚を追い'))).toBe(true);
    expect(s.penguins[1]!.status).toBe('injured');
  });

  it('fishes with spears, sharpened spears and no shoal', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2, { action: 'fish', swim: 30 })], { tools: 2 });
    // shoal yes, catch randInt(2,5) → 5, injury yes → armed message
    let log = season(s, [0, 0.99, 0]);
    expect(s.tools).toBe(1);
    expect(log).toContain('魚を7とった。');
    expect(log).toContain('P2は漁でけがをした。');
    s.penguins[1]!.status = 'ok';
    s.techs.push('togi', 'mori');
    log = season(s, [0, 0.99]);
    expect(log).toContain('魚を11とった。'); // (5 + 2) * 1.5 = 10.5 → 11
    log = season(s, [0.9]);
    expect(log).toContain('魚の群れが見つからなかった……。');
    expect(s.bareHunts).toBe(1); // the third trip had no spear left
  });

  it('caps fish at what the region has', () => {
    const s = game([penguin(1, { action: 'fish' })], { tools: 5 });
    s.regions.peninsula.fish = 2;
    expect(season(s, [0])).toContain('魚を2とった。');
  });

  it('crafts spears only once the spear is known, up to the cap', () => {
    const s = game([penguin(1, { action: 'craft', wit: 60 }), penguin(2, { action: 'craft' })]);
    expect(season(s).some((l) => l.includes('モリ'))).toBe(false);
    s.techs.push('mori');
    // (1 + 2) * 1.3 + 1 * 1.3 = 5.2 → 5
    expect(season(s)).toContain('モリを5本つくった。');
    s.tools = R.MAX_TOOLS - 1;
    expect(season(s)).toContain('モリを1本つくった。');
  });

  it('rests: research, pairing and chicks', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2, { action: 'rest' })]);
    // draws: each rester trains ちえ, then the pairing roll
    let log = season(s, [0.99, 0.99, 0]);
    expect(log).toContain('P1とP2がつがいになった！');
    expect(s.penguins[0]!.mateId).toBe(2);
    expect(s.research.points).toBeGreaterThan(0);
    log = season(s, [0.99, 0.99, 0]); // chick
    expect(log.some((l) => l.includes('ひなが生まれた'))).toBe(true);
    expect(s.penguins).toHaveLength(3);
    expect(s.births).toBe(1);
    expect(s.maxGeneration).toBe(2);
    expect(s.penguins[1]!.nest).toBe(2); // 3, minus one at season end
    log = season(s, [0.99]);
    expect(log.some((l) => l.includes('ひなが生まれた'))).toBe(false);
  });

  it('does not pair when the draw fails, and skips mothers whose mate is working', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2, { action: 'rest' })]);
    expect(season(s, [0.99, 0.99, 0.9])).not.toContain('P1とP2がつがいになった！');
    s.penguins[0]!.mateId = 2;
    s.penguins[1]!.mateId = 1;
    s.penguins[0]!.action = 'krill';
    expect(season(s, [0]).some((l) => l.includes('ひな'))).toBe(false);
  });

  it('runs out of nest space', () => {
    const ps = Array.from({ length: R.MAX_TRIBE }, (_, i) => penguin(i + 1, { action: 'krill' }));
    ps[0]!.action = 'rest';
    ps[1]!.action = 'rest';
    ps[0]!.mateId = 2;
    ps[1]!.mateId = 1;
    const s = game(ps, { food: 100 });
    expect(season(s)).toContain('巣をつくる場所がもういっぱいだ。');
  });

  it('a wise enough chick with every tech wins the game', () => {
    const s = game([penguin(1, { action: 'rest', wit: 90, mateId: 2 }), penguin(2, { action: 'rest', wit: 90, mateId: 1 })], {
      techs: ['mori', 'kotoba', 'umo', 'togi', 'uta'],
      food: 50,
    });
    const log = season(s, [0, 0, 0, 0, 0, 0]);
    expect(s.over).toBe('win');
    expect(s.sapiens).toBe(s.penguins[2]!.name);
    expect(log.some((l) => l.includes('かしこい目'))).toBe(true);
    expect(s.turn).toBe(0); // the season stops where the chick is born
  });

  it('chicks inherit and mutate their parents', () => {
    rng.fallback = 0;
    const s = game([penguin(1), penguin(2)]);
    const mom = penguin(2, { lifespan: 10, wit: 40, generation: 3 });
    const dad = penguin(1, { lifespan: 10, wit: 20, generation: 1 });
    let c = R.makeChick(s, mom, dad);
    expect(c.age).toBe(0);
    expect(c.sex).toBe('M');
    expect(c.lifespan).toBe(32);
    expect(c.wit).toBe(28); // 30 - 2
    expect(c.generation).toBe(4);
    rng.fallback = 0.99;
    s.techs.push('kotoba');
    c = R.makeChick(s, penguin(2, { lifespan: 200 }), penguin(1, { lifespan: 200 }));
    expect(c.sex).toBe('F');
    expect(c.lifespan).toBe(80);
    expect(c.wit).toBe(20 + 7 + 4);
  });
});

describe('prayer', () => {
  const chiefPraying = () => game([penguin(1, { action: 'pray' }), penguin(2, { status: 'injured', statusTurns: 3 })]);

  it('heals the hurt', () => {
    const s = chiefPraying();
    const log = season(s, [0.1, 0]);
    expect(log).toContain('族長のいのりが通じ、P2のぐあいがよくなった。');
  });

  it('heals a hurt penguin among healthy ones', () => {
    const s = game([penguin(1, { action: 'pray' }), penguin(2), penguin(3, { status: 'injured', statusTurns: 2 })]);
    const log = season(s, [0.1, 0]);
    expect(log).toContain('族長のいのりが通じ、P3のぐあいがよくなった。');
  });

  it('raises a stat, does nothing, or wears the chief out', () => {
    let s = chiefPraying();
    let log = season(s, [0.5, 0, 0, 0]);
    expect(log).toContain('族長のいのりが通じ、P1のちからが3あがった！');
    s = chiefPraying();
    log = season(s, [0.8]);
    expect(log).toContain('族長はいのったが、なにもおこらなかった。');
    s = chiefPraying();
    log = season(s, [0.95]);
    expect(log.some((l) => l.includes('弱ってしまった'))).toBe(true);
    expect(s.penguins[0]!.lifespan).toBe(56);
  });

  it('with nobody hurt, a low roll raises a stat', () => {
    const s = game([penguin(1, { action: 'pray' })]);
    expect(season(s, [0.1, 0, 0.99, 0.99]).some((l) => l.includes('さむさが8あがった'))).toBe(true);
  });
});

describe('events', () => {
  const ev = (id: string) => R.EVENTS.find((e) => e.id === id)!;

  it('picks by weight and returns null when nothing can happen', () => {
    const s = game([penguin(1)]);
    expect(R.pickEvent(s, 0)?.id).toBe('blizzard');
    expect(R.pickEvent(s, 0.999999)?.id).toBe('bloom');
    const nothing = game([penguin(1)]);
    const spy = R.EVENTS.map((e) => vi.spyOn(e, 'weight').mockReturnValue(0));
    expect(R.pickEvent(nothing, 0.5)).toBeNull();
    spy.forEach((x) => x.mockRestore());
    // r = 1 (or rounding just below it) still lands on the last possible event.
    expect(R.pickEvent(s, 1)?.id).toBe('bloom');
  });

  it('weights depend on season, region and tribe', () => {
    const s = game([penguin(1, { action: 'rest' })]);
    expect(ev('blizzard').weight(s)).toBe(1);
    expect(ev('aurora').weight(s)).toBe(0);
    expect(ev('seal').weight(s)).toBe(0);
    expect(ev('plague').weight(s)).toBe(0);
    s.turn = 3;
    expect(ev('blizzard').weight(s)).toBe(4);
    expect(ev('aurora').weight(s)).toBe(0.8);
    s.turn = 2;
    expect(ev('aurora').weight(s)).toBe(0.8);
    s.regions.peninsula.orca = 2;
    expect(ev('orca').weight(s)).toBe(0);
    s.coldwave = 2;
    expect(ev('coldwave').weight(s)).toBe(0);
  });

  it('fires one when the season roll hits', () => {
    const s = game([penguin(1), penguin(2)]);
    // draws: both krill workers train, event roll 0 → yes, pick 0 → blizzard; nobody below 45 warmth
    const log = season(s, [0.99, 0.99, 0, 0]);
    expect(log).toContain('ブリザードがふきあれた！');
  });

  it('the first year is calmer', () => {
    const s = game([penguin(1)]);
    expect(season(s, [0.99, 0.2])).not.toContain('ブリザードがふきあれた！');
    s.turn = 4;
    expect(season(s, [0.99, 0.2, 0])).toContain('ブリザードがふきあれた！');
  });

  it('blizzard injures the cold-sensitive', () => {
    rng.fallback = 0;
    const s = game([penguin(1, { warmth: 10 }), penguin(2, { warmth: 10, status: 'sick' }), penguin(3, { warmth: 50 })]);
    const log: string[] = [];
    ev('blizzard').run(s, log);
    expect(log).toEqual(['ブリザードがふきあれた！', 'P1は飛ばされてけがをした。']);
    s.penguins[0]!.status = 'ok';
    s.penguins[0]!.warmth = 25;
    s.techs.push('umo');
    const log2: string[] = [];
    ev('blizzard').run(s, log2);
    expect(log2).toHaveLength(1);
  });

  it('orcas empty the sea and attack field workers while they stay', () => {
    rng.fallback = 0;
    const s = game([penguin(1), penguin(2), penguin(3, { action: 'rest' })]);
    const log: string[] = [];
    ev('orca').run(s, log);
    expect(s.regions.peninsula.orca).toBe(3);
    expect(s.regions.peninsula.fish).toBe(0);
    // next season: three trainings, then P1 killed (0.01), P2 injured (0.1); then no event
    rng.fallback = 0.99;
    const l2 = season(s, [0.99, 0.99, 0.99, 0.01, 0.1, 0.99]);
    expect(l2).toContain('P1はシャチにおそわれてしまった。');
    expect(l2).toContain('P2はシャチに追われてけがをした。');
    expect(s.regions.peninsula.fish).toBe(0); // no regrowth while orcas are around
    const s3 = game([penguin(1)]);
    s3.regions.peninsula.orca = 1;
    expect(season(s3, [0.5]).some((l) => l.includes('シャチ'))).toBe(false);
  });

  it('leopard seal: driven off, injures, or kills', () => {
    const run = (draws: number[], extra = {}) => {
      const s = game([penguin(1, extra)]);
      const log: string[] = [];
      rng.queue = draws;
      ev('seal').run(s, log);
      return { s, log };
    };
    expect(run([0, 0], { power: 50 }).log).toContain('P1はなんとか追いはらった。');
    const hurt = run([0, 0.99, 0.1]);
    expect(hurt.log).toContain('P1は大けがをした。');
    const dead = run([0, 0.99, 0.9]);
    expect(dead.s.penguins).toHaveLength(0);
    expect(dead.log).toContain('P1はヒョウアザラシに食べられてしまった。');
  });

  it('calving injures and washes away krill', () => {
    rng.fallback = 0;
    const s = game([penguin(1), penguin(2, { status: 'sick' })]);
    const log: string[] = [];
    ev('calving').run(s, log);
    expect(log).toContain('P1は波にのまれてけがをした。');
    expect(s.regions.peninsula.krill).toBe(22);
  });

  it('plague makes several sick', () => {
    rng.fallback = 0.99;
    const s = game(Array.from({ length: 6 }, (_, i) => penguin(i + 1)));
    expect(ev('plague').weight(s)).toBe(0.8);
    const log: string[] = [];
    ev('plague').run(s, log);
    expect(s.penguins.filter((p) => p.status === 'sick')).toHaveLength(3);
  });

  it('a cold wave lasts several seasons and then ends', () => {
    rng.fallback = 0;
    const s = game([penguin(1, { warmth: 150 })]);
    const log: string[] = [];
    ev('coldwave').run(s, log);
    expect(s.coldwave).toBe(4);
    expect(R.coldness(s)).toBe(0 + 5 + 20);
    s.coldwave = 1;
    rng.fallback = 0.99;
    expect(season(s)).toContain('寒波がおさまった。');
  });

  it('skuas take an unguarded chick, are chased off, or steal food', () => {
    const s = game([penguin(1), penguin(2, { age: 1 })], { food: 10 });
    rng.fallback = 0;
    let log: string[] = [];
    ev('skua').run(s, log);
    expect(log).toContain('P2はトウゾクカモメにさらわれてしまった。');
    s.penguins.push(penguin(3, { age: 1 }), penguin(4, { action: 'rest' }), penguin(5, { action: 'rest' }));
    log = [];
    ev('skua').run(s, log);
    expect(log).toEqual(['トウゾクカモメがひなをねらったが、おとなたちが追いはらった。']);
    const s2 = game([penguin(1)], { food: 2 });
    log = [];
    ev('skua').run(s2, log);
    expect(s2.food).toBe(0);
    expect(log).toEqual(['トウゾクカモメに食料を2ぬすまれた！']);
  });

  it('rival colonies: talks bring a newcomer or a gift', () => {
    rng.fallback = 0;
    const s = game([penguin(1), penguin(2)], { techs: ['kotoba'] });
    let log: string[] = [];
    ev('rival').run(s, log);
    expect(s.penguins).toHaveLength(3);
    expect(s.penguins[2]!.generation).toBe(1);
    expect(log[1]).toContain('が群れに加わった！');
    // full tribe → gift instead
    const full = game(Array.from({ length: R.MAX_TRIBE }, (_, i) => penguin(i + 1)), { techs: ['kotoba'], food: 0 });
    log = [];
    ev('rival').run(full, log);
    expect(full.food).toBe(3);
    expect(log[1]).toBe('ことばで話し合い、なかよくなった。食料を3わけてもらった。');
  });

  it('rival colonies: fights are won or lost by strength', () => {
    rng.fallback = 0;
    const strong = game([penguin(1, { power: 150 })], { food: 0 });
    let log: string[] = [];
    ev('rival').run(strong, log);
    expect(log[1]).toBe('なわばり争いに勝った！ 食料を3手に入れた。');
    rng.fallback = 0.99;
    const weak = game([penguin(1, { power: 1 }), penguin(2, { power: 1 })], { food: 10, techs: ['kotoba'] });
    log = [];
    ev('rival').run(weak, log);
    expect(weak.food).toBe(7);
    expect(log).toContain('P1はつつかれてけがをした。');
    expect(R.tribePower(weak)).toBe(0);
  });

  it('krill bloom and aurora', () => {
    const s = game([penguin(1)]);
    const log: string[] = [];
    ev('bloom').run(s, log);
    expect(s.regions.peninsula.krill).toBe(68);
    ev('aurora').run(s, log);
    expect(s.penguins[0]!.wit).toBe(21);
    // a bloom above the maximum is not cut back by regrowth
    season(s);
    expect(s.regions.peninsula.krill).toBeGreaterThan(45);
  });
});

describe('upkeep', () => {
  it('feeds chicks first and starves the hungry', () => {
    const s = game([penguin(1, { action: 'rest', hunger: 2 }), penguin(2, { age: 1 })], { food: 1 });
    const log = season(s);
    expect(log).toContain('食料が足りず、1羽がおなかをすかせている。');
    expect(log).toContain('P1はうえ死にしてしまった。');
    expect(s.penguins.map((p) => p.id)).toEqual([2]);
    expect(s.over).toBeNull();
  });

  it('ends the game when the last penguin dies', () => {
    const s = game([penguin(1, { action: 'rest', hunger: 2 })], { food: 0 });
    const log = season(s);
    expect(s.over).toBe('lose');
    expect(log.at(-1)).toBe('群れは全滅してしまった……。');
  });

  it('cold makes the thin-feathered sick, less so with grooming', () => {
    const s = game([penguin(1, { warmth: 1, action: 'rest' })]);
    s.turn = 3; // winter
    // draws: training, event roll, then the cold roll
    const log = season(s, [0.99, 0.99, 0]);
    expect(log).toContain('P1はかぜをひいた。');
    const warm = game([penguin(1, { warmth: 30, action: 'rest' })], { techs: ['umo'] });
    warm.turn = 3;
    expect(season(warm, [0.99, 0.99, 0])).not.toContain('P1はかぜをひいた。');
  });

  it('heals over time, or dies of illness and wounds', () => {
    const s = game([penguin(1, { action: 'rest' }), penguin(2, { status: 'injured', statusTurns: 1 })]);
    season(s);
    expect(s.penguins[1]!.status).toBe('ok');
    const sick = game([penguin(1, { action: 'rest' }), penguin(2, { status: 'sick', statusTurns: 3 }), penguin(3, { age: 1, status: 'injured', statusTurns: 3 })]);
    // draws: rest research/pair/breed..., we let fallback handle and force death via 0 for health rolls
    rng.fallback = 0.99;
    rng.queue = [];
    const healthOnly = (st: GameState) => {
      // Skip everything else by making the only adult unable to act.
      st.penguins[0]!.status = 'injured';
      st.penguins[0]!.statusTurns = 5;
    };
    healthOnly(sick);
    // order of draws: event roll (no), no cold rolls (warm enough), health: P1, P2, P3
    const log = season(sick, [0.99, 0.99, 0, 0]);
    expect(log).toContain('P2は病気で死んでしまった。');
    expect(log).toContain('P3はけががもとで死んでしまった。');
  });

  it('grows chicks up and lets the old die', () => {
    const s = game([penguin(1, { age: 59, action: 'rest' }), penguin(2, { age: 3, action: 'rest' }), penguin(3, { action: 'rest', power: 30 })]);
    const log = season(s);
    expect(log).toContain('P2はおとなになった。');
    expect(s.penguins.find((p) => p.id === 2)!.action).toBe('krill');
    expect(log).toContain('P1は寿命をむかえ、しずかに息をひきとった。');
    expect(log.at(-1)).toBe('P3が新しい族長になった。');
  });

  it('picks the oldest chick as chief when no adult is left', () => {
    const s = game([penguin(1, { age: 59 }), penguin(2, { age: 0 }), penguin(3, { age: 2 }), penguin(4, { age: 1 })], { food: 10 });
    const log = season(s);
    expect(log.at(-1)).toBe('P3が新しい族長になった。');
  });

  it('clears the mate of a penguin that dies', () => {
    const s = game([penguin(1, { age: 59, mateId: 2 }), penguin(2, { mateId: 1, action: 'rest' })]);
    season(s);
    expect(s.penguins[0]!.mateId).toBeNull();
  });
});

describe('research', () => {
  it('needs bare-handed fishing before the spear', () => {
    const s = game([penguin(1)], { techs: ['kotoba', 'umo', 'uta'] });
    expect(R.availableTechs(s)).toEqual([]);
    expect(R.researchProgress(s)).toBe(0);
    s.bareHunts = R.BARE_HUNTS_FOR_MORI;
    expect(R.availableTechs(s)).toEqual(['mori']);
    s.research.points = 4;
    expect(R.researchProgress(s)).toBe(0.5);
  });

  it('learns techs in a row when there are enough points', () => {
    const s = game([penguin(1, { action: 'rest' })], { bareHunts: 3 });
    s.research.points = 200;
    rng.fallback = 0;
    const log = season(s, [0.99]);
    expect(s.techs).toHaveLength(5);
    expect(log.filter((l) => l.startsWith('ひらめいた！'))).toHaveLength(5);
    expect(R.researchProgress(s)).toBe(0);
  });

  it('keeps points while nothing can be invented', () => {
    const s = game([penguin(1, { action: 'rest' })], { techs: ['kotoba', 'umo', 'uta'] });
    season(s);
    expect(s.research.points).toBeGreaterThan(0);
    expect(s.research.target).toBeNull();
    s.research.target = 'mori';
    s.research.points = 4;
    expect(R.researchProgress(s)).toBe(0.5);
  });
});

describe('score', () => {
  it('rewards time, generations, techs, wisdom and winning', () => {
    const s = game([penguin(1, { wit: 30 })], { turn: 10, maxGeneration: 2, techs: ['mori'] });
    expect(R.score(s)).toBe(100 + 200 + 200 + 150);
    s.over = 'win';
    s.penguins = [];
    expect(R.score(s)).toBe(100 + 200 + 200 + 5000);
  });
});
