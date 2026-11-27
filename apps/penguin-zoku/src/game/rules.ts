import { NAMES, zenkaku } from '../data/names';
import { REGIONS, neighbors, regionDef } from '../data/regions';
import { TECHS, techDef } from '../data/techs';
import { chance, pick, rand, randInt, shuffle } from './rng';
import type { ActionId, GameState, Penguin, RegionId, RegionState, Sex, StatusId, TechId } from './types';

/** Penguins work from this age (in seasons) on; younger ones are chicks. */
export const ADULT_AGE = 4;
/** A chick born with this much ちえ, once every tech is known, wins the game. */
export const SAPIENS_WIT = 80;
export const STAT_MAX = 150;
export const MAX_TRIBE = 24;
export const MAX_TOOLS = 40;
/** Seasons without enough food before a penguin starves. */
export const STARVE_AT = 3;
/** Bare-handed fishing trips needed before the bone spear can be invented. */
export const BARE_HUNTS_FOR_MORI = 3;

export const SEASON_NAMES = ['春', '夏', '秋', '冬'] as const;
const KRILL_BY_SEASON = [1, 1.3, 0.9, 0.6] as const;
const COLD_BY_SEASON = [5, 0, 10, 30] as const;

export const ACTION_NAMES: Record<ActionId, string> = {
  krill: 'オキアミとり',
  fish: '漁',
  craft: 'モリづくり',
  rest: 'ひなたぼっこ',
  pray: 'いのり',
};
export const ACTION_IDS: readonly ActionId[] = ['krill', 'fish', 'craft', 'rest', 'pray'];

export const STATUS_NAMES: Record<StatusId, string> = { ok: '元気', injured: 'けが', sick: '病気' };

export const seasonIndex = (turn: number): number => turn % 4;
export const yearOf = (turn: number): number => Math.floor(turn / 4) + 1;
export const seasonLabel = (turn: number): string =>
  `${yearOf(turn)}年目 ${SEASON_NAMES[seasonIndex(turn)] as string}`;
export const ageYears = (p: Penguin): number => Math.floor(p.age / 4);
export const isAdult = (p: Penguin): boolean => p.age >= ADULT_AGE;
export const canWork = (p: Penguin): boolean => isAdult(p) && p.status === 'ok';
export const hasTech = (s: GameState, t: TechId): boolean => s.techs.includes(t);
export const clampStat = (n: number): number => Math.max(1, Math.min(STAT_MAX, Math.round(n)));
export const findPenguin = (s: GameState, id: number): Penguin | undefined =>
  s.penguins.find((p) => p.id === id);
export const chief = (s: GameState): Penguin | undefined => findPenguin(s, s.chiefId);

/** A name not yet used in the tribe, adding ２世, ３世… when the base name is taken. */
export function uniqueName(s: GameState, base: string): string {
  const used = new Set(s.penguins.map((p) => p.name));
  if (!used.has(base)) return base;
  for (let n = 2; ; n++) {
    const name = `${base}${zenkaku(n)}世`;
    if (!used.has(name)) return name;
  }
}

function makePenguin(s: GameState, sex: Sex, stats: Omit<Penguin, 'id' | 'name' | 'sex' | 'status' | 'statusTurns' | 'hunger' | 'action' | 'mateId' | 'nest'>): Penguin {
  return {
    id: s.nextId++,
    name: uniqueName(s, pick(s, NAMES)),
    sex,
    status: 'ok',
    statusTurns: 0,
    hunger: 0,
    action: 'krill',
    mateId: null,
    nest: 0,
    ...stats,
  };
}

/** A wild adult penguin with stats around `base` (used for the first tribe and for newcomers). */
function wildPenguin(s: GameState, sex: Sex, base: { power: number; swim: number; wit: number; warmth: number }): Penguin {
  return makePenguin(s, sex, {
    age: randInt(s, ADULT_AGE, 24),
    lifespan: randInt(s, 44, 60),
    power: clampStat(base.power + randInt(s, -6, 6)),
    swim: clampStat(base.swim + randInt(s, -6, 6)),
    wit: clampStat(base.wit + randInt(s, -3, 3)),
    warmth: clampStat(base.warmth + randInt(s, -6, 6)),
    generation: 1,
  });
}

export function newGame(seed: number): GameState {
  const regions = {} as Record<RegionId, RegionState>;
  for (const r of REGIONS) regions[r.id] = { krill: r.krillMax, fish: r.fishMax, orca: 0 };
  const s: GameState = {
    version: 1,
    seed: seed | 0,
    turn: 0,
    regionId: 'peninsula',
    regions,
    food: 16,
    tools: 0,
    techs: [],
    research: { target: null, points: 0 },
    bareHunts: 0,
    penguins: [],
    chiefId: 0,
    nextId: 1,
    moveTo: null,
    coldwave: 0,
    over: null,
    maxGeneration: 1,
    births: 0,
    deaths: 0,
    sapiens: null,
  };
  const base = { power: 22, swim: 22, wit: 12, warmth: 22 };
  for (const sex of ['M', 'F', 'M', 'F', 'M', 'F'] as const) s.penguins.push(wildPenguin(s, sex, base));
  s.chiefId = bestLeader(s.penguins).id;
  return s;
}

const total = (p: Penguin): number => p.power + p.swim + p.wit;

/** The adult with the highest total stats, or the oldest if there are no adults. */
function bestLeader(ps: Penguin[]): Penguin {
  const adults = ps.filter(isAdult);
  if (!adults.length) return ps.reduce((a, b) => (b.age > a.age ? b : a));
  return adults.reduce((a, b) => (total(b) > total(a) ? b : a));
}

// ---------------------------------------------------------------- commands

/** Why `p` cannot take `a`, or null if it can. */
export function actionBlock(s: GameState, p: Penguin, a: ActionId): string | null {
  if (!isAdult(p)) return 'まだひなです';
  if (p.status !== 'ok') return `${STATUS_NAMES[p.status]}でうごけません`;
  if (a === 'pray' && p.id !== s.chiefId) return '族長だけができます';
  if (a === 'craft' && !hasTech(s, 'mori')) return 'まだ作りかたを知りません';
  return null;
}

export function setAction(s: GameState, id: number, a: ActionId): boolean {
  const p = findPenguin(s, id);
  if (!p || actionBlock(s, p, a)) return false;
  p.action = a;
  return true;
}

/** Give every penguin that can take `a` that job (prayer is chief-only, so it is refused). Returns how many changed. */
export function setAll(s: GameState, a: ActionId): number {
  if (a === 'pray') return 0;
  let n = 0;
  for (const p of s.penguins) if (setAction(s, p.id, a)) n++;
  return n;
}

export function setChief(s: GameState, id: number): boolean {
  const p = findPenguin(s, id);
  if (!p || !isAdult(p)) return false;
  const old = chief(s);
  if (old && old.action === 'pray') old.action = 'rest';
  s.chiefId = id;
  return true;
}

/** Food the whole tribe needs to migrate (one per penguin, on top of eating). */
export const moveCost = (s: GameState): number => s.penguins.length;

/** Why the tribe cannot move to `to`, or null. */
export function moveBlock(s: GameState, to: RegionId): string | null {
  if (!neighbors(s.regionId).includes(to)) return 'となりの土地ではありません';
  if (s.food < moveCost(s)) return `食料が足りません（${moveCost(s)}いる）`;
  return null;
}

/** Plan a migration for the coming season, or cancel it with null. */
export function setMove(s: GameState, to: RegionId | null): boolean {
  if (to === null) {
    s.moveTo = null;
    return true;
  }
  if (moveBlock(s, to)) return false;
  s.moveTo = to;
  return true;
}

// ---------------------------------------------------------------- season

/** Advance one season: work (or migrate), events, eating, cold, health, aging. Returns the season's report. */
export function resolveSeason(s: GameState): string[] {
  if (s.over) return [];
  const log: string[] = [];
  if (s.moveTo && !moveBlock(s, s.moveTo)) {
    s.food -= moveCost(s);
    s.regionId = s.moveTo;
    log.push(`群れは${regionDef(s.regionId).name}へひっこした。（食料 -${moveCost(s)}）`);
  } else {
    work(s, log);
  }
  s.moveTo = null;
  if (!s.over) {
    randomEvent(s, log);
    eat(s, log);
    cold(s, log);
    health(s, log);
    research(s, log);
    regrow(s);
    if (s.coldwave > 0 && --s.coldwave === 0) log.push('寒波がおさまった。');
    s.turn++;
    if (!s.penguins.length) {
      s.over = 'lose';
      log.push('群れは全滅してしまった……。');
    } else ensureChief(s, log);
  }
  return log;
}

const coldwaveMult = (s: GameState): number => (s.coldwave > 0 ? 0.7 : 1);

/** Yield multiplier for a worker doing the same job as an able chief. */
export function chiefBonus(s: GameState, p: Penguin): number {
  const c = chief(s);
  if (!c || !canWork(c) || c.action !== p.action) return 1;
  return hasTech(s, 'kotoba') ? 1.5 : 1.3;
}

function train(s: GameState, p: Penguin, stat: 'power' | 'swim' | 'wit', p1: number): void {
  if (chance(s, p1)) p[stat] = clampStat(p[stat] + 1);
}

function injure(p: Penguin, status: Exclude<StatusId, 'ok'>, turns: number): void {
  p.status = status;
  p.statusTurns = Math.max(p.statusTurns, turns);
}

function work(s: GameState, log: string[]): void {
  const reg = s.regions[s.regionId];
  const workers = (a: ActionId) => s.penguins.filter((p) => canWork(p) && p.action === a);
  const season = seasonIndex(s.turn);

  const krillers = workers('krill');
  if (krillers.length) {
    let want = 0;
    for (const p of krillers) {
      want += (2.5 + p.swim / 20) * chiefBonus(s, p) * (KRILL_BY_SEASON[season] as number) * coldwaveMult(s);
      train(s, p, 'swim', 0.4);
    }
    const got = Math.min(Math.round(want), reg.krill);
    reg.krill -= got;
    s.food += got;
    log.push(`オキアミを${got}とった。`);
    if (got < Math.round(want)) log.push('このあたりのオキアミが少なくなってきた……。');
  }

  const hunters = workers('fish');
  if (hunters.length) {
    const shoal = chance(s, 0.75);
    let want = 0;
    for (const p of hunters) {
      const armed = s.tools > 0;
      if (armed) s.tools--;
      else s.bareHunts++;
      if (shoal) {
        const base = armed ? randInt(s, 2, 5) + p.swim / 15 : randInt(s, 0, 2) + p.swim / 30;
        want += base * (armed && hasTech(s, 'togi') ? 1.5 : 1) * chiefBonus(s, p) * coldwaveMult(s);
      }
      if (chance(s, armed ? 0.05 : 0.2)) {
        injure(p, 'injured', 2);
        log.push(armed ? `${p.name}は漁でけがをした。` : `${p.name}は素手で魚を追い、岩にぶつかってけがをした。`);
      }
      train(s, p, 'swim', 0.4);
      train(s, p, 'power', 0.2);
    }
    if (shoal) {
      const got = Math.min(Math.round(want), reg.fish);
      reg.fish -= got;
      s.food += got;
      log.push(`魚を${got}とった。`);
    } else log.push('魚の群れが見つからなかった……。');
  }

  const crafters = workers('craft');
  if (crafters.length && hasTech(s, 'mori')) {
    let made = 0;
    for (const p of crafters) {
      made += (1 + Math.floor(p.wit / 30)) * chiefBonus(s, p);
      train(s, p, 'wit', 0.3);
    }
    const before = s.tools;
    s.tools = Math.min(MAX_TOOLS, s.tools + Math.round(made));
    log.push(`モリを${s.tools - before}本つくった。`);
  }

  const resters = workers('rest');
  if (resters.length) {
    for (const p of resters) {
      s.research.points += 1 + p.wit / 15;
      train(s, p, 'wit', 0.25);
    }
    pairUp(s, resters, log);
    breed(s, resters, log);
  }

  const c = chief(s);
  if (c && canWork(c) && c.action === 'pray') pray(s, c, log);
}

function pairUp(s: GameState, resters: Penguin[], log: string[]): void {
  const single = (sex: Sex) => shuffle(s, resters.filter((p) => p.sex === sex && p.mateId === null));
  const males = single('M');
  const females = single('F');
  const p1 = hasTech(s, 'uta') ? 0.8 : 0.5;
  for (let i = 0; i < Math.min(males.length, females.length); i++) {
    const m = males[i] as Penguin;
    const f = females[i] as Penguin;
    if (!chance(s, p1)) continue;
    m.mateId = f.id;
    f.mateId = m.id;
    log.push(`${m.name}と${f.name}がつがいになった！`);
  }
}

function breed(s: GameState, resters: Penguin[], log: string[]): void {
  const resting = new Set(resters.map((p) => p.id));
  const base = 0.5 + (hasTech(s, 'uta') ? 0.25 : 0) - (seasonIndex(s.turn) === 3 ? 0.2 : 0);
  for (const mom of resters) {
    if (mom.sex !== 'F' || mom.mateId === null || mom.nest > 0 || !resting.has(mom.mateId)) continue;
    if (s.penguins.length >= MAX_TRIBE) {
      log.push('巣をつくる場所がもういっぱいだ。');
      return;
    }
    if (!chance(s, base)) continue;
    const dad = findPenguin(s, mom.mateId) as Penguin;
    mom.nest = 3;
    const chick = makeChick(s, mom, dad);
    s.penguins.push(chick);
    s.births++;
    s.maxGeneration = Math.max(s.maxGeneration, chick.generation);
    log.push(`${mom.name}と${dad.name}にひなが生まれた！ 名前は${chick.name}。（第${chick.generation}世代）`);
    if (s.techs.length === TECHS.length && chick.wit >= SAPIENS_WIT) {
      s.over = 'win';
      s.sapiens = chick.name;
      log.push(`${chick.name}は、これまでのどのペンギンよりもかしこい目をしている……！`);
      return;
    }
  }
}

/** A chick inheriting the average of its parents' stats, with a random mutation. */
export function makeChick(s: GameState, mom: Penguin, dad: Penguin): Penguin {
  const mix = (a: number, b: number, bonus = 0) => clampStat((a + b) / 2 + randInt(s, -3, 6) + bonus);
  // ちえ drifts upward a little faster than the body: the tribe is evolving toward wisdom.
  const mixWit = (a: number, b: number, bonus: number) => clampStat((a + b) / 2 + randInt(s, -2, 7) + bonus);
  return makePenguin(s, chance(s, 0.5) ? 'M' : 'F', {
    age: 0,
    lifespan: Math.max(32, Math.min(80, Math.round((mom.lifespan + dad.lifespan) / 2) + randInt(s, -4, 4))),
    power: mix(mom.power, dad.power),
    swim: mix(mom.swim, dad.swim),
    wit: mixWit(mom.wit, dad.wit, hasTech(s, 'kotoba') ? 4 : 0),
    warmth: mix(mom.warmth, dad.warmth),
    generation: Math.max(mom.generation, dad.generation) + 1,
  });
}

function pray(s: GameState, c: Penguin, log: string[]): void {
  const r = rand(s);
  const hurt = s.penguins.filter((p) => p.status !== 'ok');
  if (r < 0.3 && hurt.length) {
    const p = pick(s, hurt);
    p.status = 'ok';
    p.statusTurns = 0;
    log.push(`族長のいのりが通じ、${p.name}のぐあいがよくなった。`);
  } else if (r < 0.7) {
    const p = pick(s, s.penguins);
    const stat = pick(s, ['power', 'swim', 'wit', 'warmth'] as const);
    const up = randInt(s, 3, 8);
    p[stat] = clampStat(p[stat] + up);
    log.push(`族長のいのりが通じ、${p.name}の${STAT_NAMES[stat]}が${up}あがった！`);
  } else if (r < 0.9) {
    log.push('族長はいのったが、なにもおこらなかった。');
  } else {
    c.lifespan = Math.max(c.age + 1, c.lifespan - 4);
    log.push('族長はいのりすぎて、すっかり弱ってしまった……。（寿命がちぢんだ）');
  }
}

export const STAT_NAMES = { power: 'ちから', swim: 'およぎ', wit: 'ちえ', warmth: 'さむさ' } as const;

// ---------------------------------------------------------------- events

interface EventDef {
  id: string;
  weight: (s: GameState) => number;
  run: (s: GameState, log: string[]) => void;
}

const fieldWorkers = (s: GameState) => s.penguins.filter((p) => canWork(p) && (p.action === 'krill' || p.action === 'fish'));
const someOf = (s: GameState, ps: Penguin[], n: number) => shuffle(s, ps).slice(0, n);

function kill(s: GameState, p: Penguin, why: string, log: string[]): void {
  s.penguins = s.penguins.filter((q) => q !== p);
  for (const q of s.penguins) if (q.mateId === p.id) q.mateId = null;
  s.deaths++;
  log.push(`${p.name}は${why}。`);
}

/** Tribe-wide strength for fights: healthy adults' ちから plus spears. */
export const tribePower = (s: GameState): number =>
  s.penguins.filter(canWork).reduce((a, p) => a + p.power, 0) + s.tools * 3;

export const EVENTS: readonly EventDef[] = [
  {
    id: 'blizzard',
    weight: (s) => (seasonIndex(s.turn) === 3 ? 4 : 1),
    run: (s, log) => {
      log.push('ブリザードがふきあれた！');
      for (const p of s.penguins) {
        const resist = p.warmth + (hasTech(s, 'umo') ? 25 : 0);
        if (p.status === 'ok' && resist < 45 && chance(s, 0.3)) {
          injure(p, 'injured', 2);
          log.push(`${p.name}は飛ばされてけがをした。`);
        }
      }
    },
  },
  {
    id: 'orca',
    weight: (s) => (s.regions[s.regionId].orca > 0 ? 0 : 1.2 * regionDef(s.regionId).orca),
    run: (s, log) => {
      const reg = s.regions[s.regionId];
      reg.orca = randInt(s, 3, 5);
      reg.fish = 0;
      log.push('シャチの群れがあらわれた！ 魚がすっかり食べられてしまった。しばらく海に出るのは危ない。');
    },
  },
  {
    id: 'seal',
    weight: (s) => (fieldWorkers(s).length ? 1.5 : 0),
    run: (s, log) => {
      const p = pick(s, fieldWorkers(s));
      log.push(`ヒョウアザラシが${p.name}におそいかかった！`);
      if (p.power + Math.min(s.tools, 10) * 3 > randInt(s, 10, 60)) log.push(`${p.name}はなんとか追いはらった。`);
      else if (chance(s, 0.75)) {
        injure(p, 'injured', 3);
        log.push(`${p.name}は大けがをした。`);
      } else kill(s, p, 'ヒョウアザラシに食べられてしまった', log);
    },
  },
  {
    id: 'calving',
    weight: () => 0.8,
    run: (s, log) => {
      log.push('近くの氷山がくずれ、大波がおしよせた！');
      for (const p of someOf(s, s.penguins.filter((q) => q.status === 'ok'), randInt(s, 1, 3))) {
        injure(p, 'injured', 2);
        log.push(`${p.name}は波にのまれてけがをした。`);
      }
      const reg = s.regions[s.regionId];
      reg.krill = Math.floor(reg.krill / 2);
    },
  },
  {
    id: 'plague',
    weight: (s) => (s.penguins.length >= 6 ? 0.8 : 0),
    run: (s, log) => {
      log.push('群れに流行り病がひろがった！');
      for (const p of someOf(s, s.penguins.filter((q) => q.status === 'ok'), randInt(s, 1, 3))) {
        injure(p, 'sick', 2);
        log.push(`${p.name}が病気になった。`);
      }
    },
  },
  {
    id: 'coldwave',
    weight: (s) => (s.coldwave > 0 ? 0 : 0.5),
    run: (s, log) => {
      s.coldwave = randInt(s, 4, 8);
      log.push('大寒波がやってきた！ しばらくのあいだ、寒さがきびしく、えさもとりにくい。');
    },
  },
  {
    id: 'skua',
    weight: () => 1,
    run: (s, log) => {
      const chicks = s.penguins.filter((p) => !isAdult(p));
      const guards = s.penguins.filter((p) => canWork(p) && p.action === 'rest').length;
      if (chicks.length && guards < 2) {
        kill(s, pick(s, chicks), 'トウゾクカモメにさらわれてしまった', log);
        log.push('（ひなを守るには、巣で休んでいるおとなが2羽以上ほしい）');
      } else if (chicks.length) {
        log.push('トウゾクカモメがひなをねらったが、おとなたちが追いはらった。');
      } else {
        const lost = Math.min(s.food, randInt(s, 3, 6));
        s.food -= lost;
        log.push(`トウゾクカモメに食料を${lost}ぬすまれた！`);
      }
    },
  },
  {
    id: 'rival',
    weight: (s) => 1.2 * regionDef(s.regionId).rival,
    run: (s, log) => {
      log.push('ほかのペンギンの群れがやってきた！');
      if (hasTech(s, 'kotoba') && chance(s, 0.6)) {
        if (s.penguins.length < MAX_TRIBE && chance(s, 0.5)) {
          const avg = (k: 'power' | 'swim' | 'wit' | 'warmth') =>
            s.penguins.reduce((a, p) => a + p[k], 0) / s.penguins.length;
          const p = wildPenguin(s, chance(s, 0.5) ? 'M' : 'F', {
            power: avg('power'), swim: avg('swim'), wit: avg('wit') - 5, warmth: avg('warmth'),
          });
          s.penguins.push(p);
          log.push(`ことばで話し合い、なかよくなった。${p.name}が群れに加わった！`);
        } else {
          const gift = randInt(s, 3, 8);
          s.food += gift;
          log.push(`ことばで話し合い、なかよくなった。食料を${gift}わけてもらった。`);
        }
        return;
      }
      const ours = tribePower(s);
      const theirs = randInt(s, 20, 50) + s.penguins.length * randInt(s, 10, 22);
      if (ours >= theirs) {
        const loot = randInt(s, 3, 8);
        s.food += loot;
        log.push(`なわばり争いに勝った！ 食料を${loot}手に入れた。`);
      } else {
        const lost = Math.floor(s.food * 0.3);
        s.food -= lost;
        log.push(`なわばり争いに負けた……。食料を${lost}うばわれた。`);
        for (const p of someOf(s, s.penguins.filter(canWork), randInt(s, 1, 3))) {
          injure(p, 'injured', 2);
          log.push(`${p.name}はつつかれてけがをした。`);
        }
      }
    },
  },
  {
    id: 'bloom',
    weight: () => 0.8,
    run: (s, log) => {
      const reg = s.regions[s.regionId];
      reg.krill = Math.round(regionDef(s.regionId).krillMax * 1.5);
      log.push('海がピンク色にそまった。オキアミの大発生だ！');
    },
  },
  {
    id: 'aurora',
    weight: (s) => (seasonIndex(s.turn) === 3 || seasonIndex(s.turn) === 2 ? 0.8 : 0),
    run: (s, log) => {
      for (const p of s.penguins) p.wit = clampStat(p.wit + 1);
      log.push('夜空にオーロラがゆれた。みんなで空を見上げ、少しかしこくなった気がする。（全員のちえ +1）');
    },
  },
];

/** Pick an event by weight from `r` in [0, 1); null when every weight is zero. */
export function pickEvent(s: GameState, r: number): EventDef | null {
  const ws = EVENTS.map((e) => e.weight(s));
  const sum = ws.reduce((a, b) => a + b, 0);
  if (sum <= 0) return null;
  let x = r * sum;
  let chosen: EventDef | null = null;
  for (let i = 0; i < EVENTS.length; i++) {
    const w = ws[i] as number;
    if (w <= 0) continue;
    chosen = EVENTS[i] as EventDef;
    if (x < w) break;
    x -= w;
  }
  // Rounding can leave x just past the end; the last possible event takes it.
  return chosen;
}

function randomEvent(s: GameState, log: string[]): void {
  const reg = s.regions[s.regionId];
  if (reg.orca > 0) {
    for (const p of fieldWorkers(s)) {
      const r = rand(s);
      if (r < 0.03) kill(s, p, 'シャチにおそわれてしまった', log);
      else if (r < 0.15) {
        injure(p, 'injured', 3);
        log.push(`${p.name}はシャチに追われてけがをした。`);
      }
    }
  }
  // The first year is calmer, so a new player can learn the ropes.
  if (!chance(s, s.turn < 4 ? 0.15 : 0.35)) return;
  pickEvent(s, rand(s))?.run(s, log);
}

// ---------------------------------------------------------------- upkeep

function eat(s: GameState, log: string[]): void {
  const order = [...s.penguins.filter((p) => !isAdult(p)), ...s.penguins.filter(isAdult)];
  let hungry = 0;
  for (const p of order) {
    const need = 1;
    if (s.food >= need) {
      s.food -= need;
      p.hunger = 0;
    } else {
      p.hunger++;
      hungry++;
    }
  }
  if (hungry) log.push(`食料が足りず、${hungry}羽がおなかをすかせている。`);
  for (const p of order) if (p.hunger >= STARVE_AT) kill(s, p, 'うえ死にしてしまった', log);
  s.food = Math.floor(s.food * 0.9);
}

/** How cold it is this season where the tribe lives. */
export const coldness = (s: GameState): number =>
  regionDef(s.regionId).cold + (COLD_BY_SEASON[seasonIndex(s.turn)] as number) + (s.coldwave > 0 ? 20 : 0);

function cold(s: GameState, log: string[]): void {
  const c = coldness(s);
  for (const p of s.penguins) {
    const resist = p.warmth + (hasTech(s, 'umo') ? 25 : 0) - (isAdult(p) ? 0 : 10);
    if (p.status === 'ok' && c > resist && chance(s, (c - resist) / 120)) {
      injure(p, 'sick', 2);
      log.push(`${p.name}はかぜをひいた。`);
    }
  }
}

function health(s: GameState, log: string[]): void {
  for (const p of [...s.penguins]) {
    if (p.status !== 'ok') {
      const risk = (p.status === 'sick' ? 0.06 : 0.03) * (isAdult(p) ? 1 : 2);
      if (chance(s, risk)) {
        kill(s, p, p.status === 'sick' ? '病気で死んでしまった' : 'けががもとで死んでしまった', log);
        continue;
      }
      if (--p.statusTurns <= 0) {
        p.status = 'ok';
        p.statusTurns = 0;
      }
    }
    if (p.nest > 0) p.nest--;
    const wasChick = !isAdult(p);
    p.age++;
    if (p.age >= p.lifespan) kill(s, p, '寿命をむかえ、しずかに息をひきとった', log);
    else if (wasChick && isAdult(p)) {
      p.action = 'krill';
      log.push(`${p.name}はおとなになった。`);
    }
  }
}

/** Techs that can become the research target now. */
export function availableTechs(s: GameState): TechId[] {
  return TECHS.filter(
    (t) =>
      !hasTech(s, t.id) &&
      (t.requires === null || hasTech(s, t.requires)) &&
      (t.id !== 'mori' || s.bareHunts >= BARE_HUNTS_FOR_MORI),
  ).map((t) => t.id);
}

function research(s: GameState, log: string[]): void {
  for (;;) {
    if (s.research.target === null) {
      const options = availableTechs(s);
      if (!options.length) return;
      s.research.target = pick(s, options);
    }
    const t = techDef(s.research.target);
    if (s.research.points < t.cost) return;
    s.research.points -= t.cost;
    s.techs.push(t.id);
    s.research.target = null;
    log.push(`ひらめいた！ 群れは「${t.name}」を身につけた！`);
  }
}

/** Share of the current research done, 0..1 (0 when nothing can be researched yet). */
export function researchProgress(s: GameState): number {
  const t = s.research.target ?? availableTechs(s)[0];
  if (!t) return 0;
  return Math.min(1, s.research.points / techDef(t).cost);
}

function regrow(s: GameState): void {
  const winter = seasonIndex(s.turn) === 3;
  for (const r of REGIONS) {
    const reg = s.regions[r.id];
    reg.krill = Math.max(reg.krill, Math.min(r.krillMax, Math.round(reg.krill + r.krillMax * (winter ? 0.1 : 0.3))));
    if (reg.orca > 0) reg.orca--;
    else reg.fish = Math.min(r.fishMax, Math.round(reg.fish + r.fishMax * 0.2));
  }
}

function ensureChief(s: GameState, log: string[]): void {
  if (chief(s)) return;
  const c = bestLeader(s.penguins);
  s.chiefId = c.id;
  log.push(`${c.name}が新しい族長になった。`);
}

/** Score shown at the end: seasons survived, generations and wisdom. */
export function score(s: GameState): number {
  const wit = s.penguins.reduce((a, p) => Math.max(a, p.wit), 0);
  return s.turn * 10 + s.maxGeneration * 100 + s.techs.length * 200 + wit * 5 + (s.over === 'win' ? 5000 : 0);
}
