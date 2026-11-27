import './style.css';
import { neighbors, regionDef } from './data/regions';
import { TECHS } from './data/techs';
import {
  ACTION_IDS, ACTION_NAMES, ADULT_AGE, SAPIENS_WIT, STATUS_NAMES, actionBlock, ageYears, availableTechs, canWork,
  chief, coldness, hasTech, isAdult, moveBlock, moveCost, newGame, researchProgress, resolveSeason, score,
  seasonLabel, setAction, setAll, setChief, setMove,
} from './game/rules';
import type { ActionId, GameState, Penguin, RegionId } from './game/types';
import { drawScene } from './render/scene';
import { loadGame, saveGame } from './save';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const statusEl = $('status');
const titleEl = $('ptitle');
const bodyEl = $('pbody');
const footEl = $('pfoot');
const canvas = $<HTMLCanvasElement>('scene');
const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;

const store = (() => {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
})();

interface Item {
  label: string;
  sub?: string;
  off?: boolean;
  act: () => void;
}
type View =
  | { kind: 'list'; title: string; items: Item[]; cursor: number; foot?: string; back?: () => void }
  | { kind: 'text'; title: string; pages: string[][]; page: number; done: () => void; back?: () => void; big?: string };

let game: GameState | null = null;
/** State shown on the title screen's scene. */
const demo = newGame(Date.now() & 0xffff);
let view: View;
const LINES_PER_PAGE = 7;

function show(v: View): void {
  view = v;
  render();
}

function list(title: string, items: Item[], opts: { cursor?: number; foot?: string; back?: () => void } = {}): void {
  show({ kind: 'list', title, items, cursor: Math.min(opts.cursor ?? 0, Math.max(0, items.length - 1)), foot: opts.foot, back: opts.back });
}

function text(title: string, lines: string[], done: () => void, opts: { big?: string; back?: () => void } = {}): void {
  const pages: string[][] = [];
  for (let i = 0; i < lines.length; i += LINES_PER_PAGE) pages.push(lines.slice(i, i + LINES_PER_PAGE));
  if (!pages.length) pages.push([]);
  show({ kind: 'text', title, pages, page: 0, done, back: opts.back, big: opts.big });
}

function render(): void {
  renderStatus();
  titleEl.textContent = view.title;
  bodyEl.replaceChildren();
  if (view.kind === 'list') {
    const v = view;
    v.items.forEach((it, i) => {
      const row = document.createElement('div');
      row.className = `item${i === v.cursor ? ' sel' : ''}${it.off ? ' off' : ''}`;
      row.setAttribute('role', 'button');
      const no = document.createElement('span');
      no.className = 'no';
      no.textContent = i < 9 ? String(i + 1) : '';
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = it.label;
      row.append(no, label);
      if (it.sub) {
        const sub = document.createElement('span');
        sub.className = 'sub';
        sub.textContent = it.sub;
        row.append(sub);
      }
      row.addEventListener('click', () => {
        v.cursor = i;
        choose();
      });
      bodyEl.append(row);
    });
    footEl.textContent = v.foot ?? '';
    bodyEl.querySelector('.sel')?.scrollIntoView({ block: 'nearest' });
  } else {
    const v = view;
    const box = document.createElement('div');
    box.className = 'text';
    if (v.big && v.page === 0) {
      const big = document.createElement('div');
      big.className = 'big';
      big.textContent = v.big;
      box.append(big);
    }
    for (const line of v.pages[v.page] as string[]) {
      const p = document.createElement('p');
      p.textContent = line;
      if (/死|食べられ|さらわれ|全滅|おそわれて/.test(line)) p.className = 'warn';
      box.append(p);
    }
    bodyEl.append(box);
    bodyEl.scrollTop = 0;
    footEl.textContent = `${v.page + 1}/${v.pages.length}  決定で${v.page + 1 < v.pages.length ? 'つぎへ' : 'とじる'}`;
  }
}

function renderStatus(): void {
  if (!game) {
    statusEl.textContent = 'ぺんぎん族 〜南極進化記〜';
    return;
  }
  const s = game;
  statusEl.replaceChildren(
    ...[
      seasonLabel(s.turn),
      regionDef(s.regionId).name,
      `食料${s.food}`,
      `モリ${s.tools}`,
      `${s.penguins.length}羽`,
    ].map((t) => {
      const span = document.createElement('span');
      span.textContent = t;
      return span;
    }),
  );
}

function choose(): void {
  if (view.kind === 'list') {
    const it = view.items[view.cursor];
    if (it && !it.off) it.act();
    else if (it) flash();
  } else {
    const v = view;
    if (v.page + 1 < v.pages.length) {
      v.page++;
      render();
    } else v.done();
  }
}

function back(): void {
  view.back?.();
}

function moveCursor(d: number): void {
  if (view.kind === 'list') {
    const n = view.items.length;
    if (!n) return;
    view.cursor = (view.cursor + d + n) % n;
    render();
  } else if (d > 0) choose();
  else if (view.page > 0) {
    view.page--;
    render();
  }
}

function flash(): void {
  bodyEl.animate([{ opacity: 1 }, { opacity: 0.4 }, { opacity: 1 }], { duration: 160 });
}

// ---------------------------------------------------------------- screens

function titleScreen(): void {
  game = null;
  const saved = loadGame(store);
  list(
    'ぺんぎん族 〜南極進化記〜',
    [
      { label: 'はじめから', act: () => startNew(saved !== null) },
      { label: 'つづきから', sub: saved ? seasonLabel(saved.turn) : 'データなし', off: !saved, act: () => resume(saved as GameState) },
      { label: 'あそびかた', act: () => howto() },
    ],
    { foot: '南極の氷の上で、ペンギンの群れを生きのびさせよう' },
  );
}

function startNew(overwrite: boolean): void {
  const go = () => {
    game = newGame((Math.random() * 2 ** 31) | 0);
    saveGame(store, game);
    text(
      'はじまり',
      [
        'ここは南極半島。',
        '6羽のペンギンが、氷の上で身をよせあっている。',
        'えさをとり、ひなを育て、知恵をつけて、',
        'きびしい南極を生きのびよう。',
        '',
        `いつか、ちえ${SAPIENS_WIT}をこえる「かしこいペンギン」が生まれる日まで……。`,
      ],
      mainMenu,
    );
  };
  if (!overwrite) return go();
  list('はじめから', [
    { label: 'はい（前の群れは消えます）', act: go },
    { label: 'いいえ', act: titleScreen },
  ], { back: titleScreen });
}

function resume(s: GameState): void {
  game = s;
  mainMenu();
}

function howto(): void {
  text(
    'あそびかた',
    [
      '■季節ごとに、1羽ずつしごとを決めて「季節をすすめる」。',
      '■オキアミとり：安定して食料がとれる。',
      '■漁：魚がとれるが、素手だとけがをしやすい。',
      '　素手で何度か漁をすると、モリを思いつくかも。',
      '■モリづくり：モリを作る。モリで漁をするとたくさんとれる。',
      '■ひなたぼっこ：のんびりすると、つがいができて、ひなが生まれる。発明のひらめきもたまる。',
      '■いのり：族長だけ。ふしぎなことがおこる。',
      '■族長と同じしごとをするペンギンは、はかどる。',
      '■食料は1羽1季節に1つ。足りないと、うえ死にする。',
      '■食料は季節ごとに少しずつくさる。',
      '■えさは土地ごとに限りがある。少なくなったら、となりの土地へひっこそう（1羽につき食料1）。',
      '■冬は寒く、えさも少ない。寒さに弱いと病気になる。',
      '■シャチ、ヒョウアザラシ、ブリザード、ほかの群れ……南極は危険がいっぱい。',
      '■ペンギンは年をとると死ぬ。ひなは親の力を受けつぐ。',
      `■発明を5つすべて身につけ、ちえ${SAPIENS_WIT}以上のひなが生まれたらクリア。`,
      '■群れが全滅したらゲームオーバー。',
    ],
    titleScreen,
    { back: titleScreen },
  );
}

const g = (): GameState => game as GameState;

const level = (n: number, max: number): string =>
  n >= max * 0.7 ? 'たくさん' : n >= max * 0.4 ? 'ふつう' : n >= max * 0.15 ? 'すこし' : 'ほとんどない';

function jobSummary(s: GameState): string {
  const counts = new Map<ActionId, number>();
  for (const p of s.penguins) if (canWork(p)) counts.set(p.action, (counts.get(p.action) ?? 0) + 1);
  const short: Record<ActionId, string> = { krill: 'オキ', fish: '漁', craft: 'モリ', rest: '休', pray: '祈' };
  return ACTION_IDS.filter((a) => counts.get(a)).map((a) => `${short[a]}${counts.get(a)}`).join(' ');
}

function mainMenu(cursor = 0): void {
  const s = g();
  const c = chief(s);
  const bar = '■'.repeat(Math.round(researchProgress(s) * 5)).padEnd(5, '□');
  const items: Item[] = [
    { label: 'しごとを決める', sub: s.moveTo ? 'ひっこし中' : jobSummary(s), act: () => assignList() },
    { label: 'みんなに同じしごと', act: () => allMenu() },
    { label: '族長を決める', sub: c ? `★${c.name}` : '', act: () => chiefMenu() },
    { label: 'ひっこす', sub: s.moveTo ? `→${regionDef(s.moveTo).name}` : '', act: () => moveMenu() },
    { label: '群れのようす', sub: `${s.penguins.length}羽`, act: () => herdList() },
    { label: '発明', sub: `${s.techs.length}/${TECHS.length} ${bar}`, act: () => techList() },
    { label: '土地のようす', act: () => regionInfo() },
    { label: '季節をすすめる', sub: '▶', act: () => advance() },
    { label: 'タイトルへ', sub: '自動セーブ', act: () => titleScreen() },
  ];
  list(`${seasonLabel(s.turn)}　なにをする？`, items, { cursor, foot: `寒さ${coldness(s)}  第${s.maxGeneration}世代` });
}

function penguinLabel(s: GameState, p: Penguin): string {
  return `${p.id === s.chiefId ? '★' : ''}${p.name}${p.sex === 'M' ? '♂' : '♀'}${ageYears(p)}才`;
}

function penguinState(p: Penguin): string {
  if (!isAdult(p)) return 'ひな';
  if (p.status !== 'ok') return STATUS_NAMES[p.status];
  return ACTION_NAMES[p.action];
}

function assignList(cursor = 0): void {
  const s = g();
  if (s.moveTo) {
    text('しごとを決める', ['この季節はひっこしをするので、しごとはできません。', '「ひっこす」でとりやめることもできます。'], () => mainMenu(0));
    return;
  }
  const ps = s.penguins;
  list(
    'だれに指示する？',
    ps.map((p, i) => ({
      label: penguinLabel(s, p),
      sub: penguinState(p),
      off: !canWork(p),
      act: () => actionMenu(p, () => assignList(Math.min(i + 1, ps.length - 1))),
    })),
    { cursor, back: () => mainMenu(0), foot: '決定すると、そのペンギンのしごとをえらべます' },
  );
}

function actionHint(a: ActionId): string {
  switch (a) {
    case 'krill': return '安定して食料';
    case 'fish': return '多くとれるが危険';
    case 'craft': return 'モリをつくる';
    case 'rest': return 'つがい・発明';
    case 'pray': return '族長のみ';
  }
}

function actionMenu(p: Penguin, next: () => void): void {
  const s = g();
  list(
    `${p.name}のしごと`,
    ACTION_IDS.map((a) => {
      const block = actionBlock(s, p, a);
      return {
        label: `${a === p.action ? '・' : '　'}${ACTION_NAMES[a]}`,
        sub: block ?? actionHint(a),
        off: block !== null,
        act: () => {
          setAction(s, p.id, a);
          saveGame(store, s);
          next();
        },
      };
    }),
    { cursor: Math.max(0, ACTION_IDS.indexOf(p.action)), back: next, foot: statLine(p) },
  );
}

const statLine = (p: Penguin): string => `力${p.power} 泳${p.swim} 知${p.wit} 寒${p.warmth}`;

function allMenu(): void {
  const s = g();
  list(
    'みんなのしごと',
    ACTION_IDS.filter((a) => a !== 'pray').map((a) => ({
      label: ACTION_NAMES[a],
      sub: a === 'craft' && !hasTech(s, 'mori') ? 'まだ知らない' : actionHint(a),
      off: a === 'craft' && !hasTech(s, 'mori'),
      act: () => {
        const n = setAll(s, a);
        saveGame(store, s);
        text('みんなのしごと', [`${n}羽を「${ACTION_NAMES[a]}」にした。`], () => mainMenu(1));
      },
    })),
    { back: () => mainMenu(1) },
  );
}

function chiefMenu(): void {
  const s = g();
  list(
    '族長をえらぶ',
    s.penguins.map((p) => ({
      label: penguinLabel(s, p),
      sub: statLine(p),
      off: !isAdult(p),
      act: () => {
        setChief(s, p.id);
        saveGame(store, s);
        mainMenu(2);
      },
    })),
    { back: () => mainMenu(2), foot: '族長と同じしごとのペンギンは、はかどる' },
  );
}

function moveMenu(): void {
  const s = g();
  const here = regionDef(s.regionId);
  const items: Item[] = neighbors(s.regionId).map((id: RegionId) => {
    const block = moveBlock(s, id);
    const r = s.regions[id];
    const d = regionDef(id);
    return {
      label: d.name,
      sub: block ?? `オキアミ${level(r.krill, d.krillMax)} 魚${level(r.fish, d.fishMax)}`,
      off: block !== null,
      act: () => {
        setMove(s, id);
        saveGame(store, s);
        text('ひっこし', [`次の季節、群れは${d.name}へひっこす。`, d.note, `（食料を${moveCost(s)}使います。この季節はしごとができません）`], () => mainMenu(3));
      },
    };
  });
  if (s.moveTo) items.push({ label: 'ひっこしをやめる', act: () => { setMove(s, null); saveGame(store, s); mainMenu(3); } });
  list(`ひっこし先（いまは${here.name}）`, items, { back: () => mainMenu(3), foot: `ひっこしには食料が${moveCost(s)}いります` });
}

function herdList(cursor = 0): void {
  const s = g();
  list(
    `群れのようす（${s.penguins.length}羽）`,
    s.penguins.map((p, i) => ({ label: penguinLabel(s, p), sub: penguinState(p), act: () => penguinDetail(p, i) })),
    { cursor, back: () => mainMenu(4) },
  );
}

function penguinDetail(p: Penguin, i: number): void {
  const s = g();
  const mate = p.mateId !== null ? s.penguins.find((q) => q.id === p.mateId) : undefined;
  text(
    penguinLabel(s, p),
    [
      `${p.sex === 'M' ? 'オス' : 'メス'}　第${p.generation}世代${p.id === s.chiefId ? '　族長' : ''}`,
      `年れい ${ageYears(p)}才（寿命まであと${Math.ceil((p.lifespan - p.age) / 4)}年ほど）`,
      `ちから ${p.power}　およぎ ${p.swim}`,
      `ちえ　 ${p.wit}　さむさ ${p.warmth}`,
      `ようす ${isAdult(p) ? STATUS_NAMES[p.status] : `ひな（${ADULT_AGE - p.age}季節でおとな）`}${p.hunger ? '・はらぺこ' : ''}`,
      `つがい ${mate ? mate.name : 'なし'}`,
    ],
    () => herdList(i),
    { back: () => herdList(i) },
  );
}

function techList(): void {
  const s = g();
  const open = availableTechs(s);
  const lines: string[] = [];
  for (const t of TECHS) {
    if (hasTech(s, t.id)) lines.push(`◆${t.name}`, `　${t.desc}`);
    else lines.push(`◇？？？${open.includes(t.id) ? '（ひらめきそう）' : ''}`);
  }
  lines.push('', 'ひなたぼっこをすると、ひらめきがたまります。');
  text(`発明 ${s.techs.length}/${TECHS.length}`, lines, () => mainMenu(5), { back: () => mainMenu(5) });
}

function regionInfo(): void {
  const s = g();
  const d = regionDef(s.regionId);
  const r = s.regions[s.regionId];
  text(
    d.name,
    [
      d.note,
      `オキアミ：${level(r.krill, d.krillMax)}`,
      `魚：${level(r.fish, d.fishMax)}`,
      `寒さ：${coldness(s)}${s.coldwave > 0 ? '（寒波）' : ''}`,
      r.orca > 0 ? 'シャチがうろついている！ 海に出ると危ない。' : '',
    ].filter(Boolean),
    () => mainMenu(6),
    { back: () => mainMenu(6) },
  );
}

function advance(): void {
  const s = g();
  const label = seasonLabel(s.turn);
  const lines = resolveSeason(s);
  saveGame(store, s);
  if (!lines.length) lines.push('しずかな季節だった。');
  text(`${label}のできごと`, lines, () => (s.over ? ending() : mainMenu(7)));
}

function ending(): void {
  const s = g();
  const best = s.penguins.reduce((a, p) => Math.max(a, p.wit), 0);
  const lines =
    s.over === 'win'
      ? [
          `${s.sapiens}は、空を見上げて考えた。`,
          '「ぼくたちは、どこから来て、どこへ行くのだろう」',
          '南極の氷の上に、かしこいペンギンが生まれた。',
          '群れの長い旅は、新しい時代をむかえる。',
        ]
      : ['南極の風だけが、氷の上をふきぬけていく……。'];
  lines.push(
    '',
    `生きのびた年月：${Math.floor(s.turn / 4)}年${s.turn % 4}季節`,
    `世代：第${s.maxGeneration}世代　発明：${s.techs.length}/${TECHS.length}`,
    `生まれたひな：${s.births}羽${best ? `　最高のちえ：${best}` : ''}`,
    `スコア：${score(s)}`,
  );
  text(s.over === 'win' ? 'エンディング' : 'ゲームオーバー', lines, titleScreen, { big: s.over === 'win' ? 'ペンギヌス誕生！' : '群れは全滅した' });
}

// ---------------------------------------------------------------- input

$('kUp').addEventListener('click', () => moveCursor(-1));
$('kDown').addEventListener('click', () => moveCursor(1));
$('kOk').addEventListener('click', choose);
$('kBack').addEventListener('click', back);
$('kMenu').addEventListener('click', () => (game ? mainMenu(0) : titleScreen()));

document.addEventListener('keydown', (e) => {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  const k = e.key;
  if (k === 'ArrowUp') moveCursor(-1);
  else if (k === 'ArrowDown') moveCursor(1);
  else if (k === 'Enter' || k === ' ') choose();
  else if (k === 'Escape' || k === 'Backspace') back();
  else if (/^[1-9]$/.test(k) && view.kind === 'list') {
    const i = Number(k) - 1;
    if (i >= view.items.length) return;
    view.cursor = i;
    choose();
  } else return;
  e.preventDefault();
});

// ---------------------------------------------------------------- loop

let lastDraw = 0;
function frame(t: number): void {
  // Redraw ~10 times a second for a choppy, retro feel.
  if (t - lastDraw > 100) {
    lastDraw = t;
    drawScene(ctx, game ?? demo, t);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

titleScreen();
