import './style.css';
import { neighbors, regionDef } from './data/regions';
import { TECHS } from './data/techs';
import {
  ACTION_IDS, ACTION_NAMES, ADULT_AGE, BARE_HUNTS_FOR_MORI, SAPIENS_WIT, STATUS_NAMES, actionBlock, ageYears,
  availableTechs, canWork, coldness, findPenguin, hasTech, isAdult, moveBlock, moveCost, newGame,
  researchProgress, resolveSeason, score, seasonLabel, setAction, setAll, setChief, setMove,
} from './game/rules';
import type { ActionId, GameState, Penguin, RegionId } from './game/types';
import { drawScene, penguinIcon } from './render/scene';
import { loadGame, saveGame } from './save';

// ---------------------------------------------------------------- tiny DOM helper

type Child = Node | string | null | undefined | false;
function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Record<string, unknown> = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v as EventListener);
    else if (k === 'class') el.className = String(v);
    else if (k === 'style') el.setAttribute('style', String(v));
    else if (k in el && k !== 'list') (el as unknown as Record<string, unknown>)[k] = v;
    else el.setAttribute(k, String(v));
  }
  for (const c of children) if (c !== null && c !== undefined && c !== false) el.append(c);
  return el;
}

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const seasonEl = $('season');
const regionEl = $('region');
const statsEl = $('stats');
const tabsEl = $('tabs');
const viewEl = $('view');
const dockEl = $('dock');
const dockInfo = $('dockInfo');
const advanceBtn = $<HTMLButtonElement>('advance');
const sheetEl = $('sheet');
const sheetBody = $('sheetBody');
const toastEl = $('toast');
const canvas = $<HTMLCanvasElement>('scene');
const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;

const store = (() => {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
})();

// ---------------------------------------------------------------- state

type Tab = 'herd' | 'land' | 'tech' | 'log';
let game: GameState | null = null;
const demo = newGame(Date.now() & 0xffff);
let tab: Tab = 'herd';
/** Reports of recent seasons, newest first (kept for this visit only). */
let history: { label: string; lines: string[] }[] = [];
/** Penguin shown in the open sheet, highlighted in the scene. */
let selected: number | null = null;
let sheetOnClose: (() => void) | null = null;

const g = (): GameState => game as GameState;

function persist(): void {
  if (game) saveGame(store, game);
}

// ---------------------------------------------------------------- shared bits

const JOB_HINT: Record<ActionId, string> = {
  krill: '安定して食料がとれる',
  fish: 'たくさんとれるが危険。モリがあると安全',
  craft: 'モリをつくる',
  rest: 'つがい・ひな・発明のひらめき',
  pray: 'ふしぎなことがおこる',
};
const JOB_SHORT: Record<ActionId, string> = { krill: 'オキアミ', fish: '漁', craft: 'モリ', rest: '休み', pray: '祈り' };

const level = (n: number, max: number): string =>
  n >= max * 0.7 ? 'たくさん' : n >= max * 0.4 ? 'ふつう' : n >= max * 0.15 ? 'すこし' : 'ほとんどない';

function lineClass(line: string): string | undefined {
  if (/死|食べられ|さらわれ|全滅|おそわれて|負けた|ぬすまれ|うばわれ/.test(line)) return 'bad';
  if (/ひらめいた/.test(line)) return 'tech';
  if (/生まれた|つがいになった|加わった|勝った|大発生|かしこい目/.test(line)) return 'good';
  return undefined;
}

function lines(ls: string[]): HTMLElement {
  return h('ul', { class: 'lines' }, ...ls.map((l) => h('li', { class: lineClass(l) }, l)));
}

function toast(msg: string): void {
  toastEl.textContent = msg;
  toastEl.hidden = false;
  clearTimeout((toast as unknown as { t?: number }).t);
  (toast as unknown as { t?: number }).t = window.setTimeout(() => (toastEl.hidden = true), 1600);
}

function meter(label: string, value: number, max: number, cls: string, text: string): HTMLElement {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return h('div', { class: 'meter' }, h('span', {}, label), h('div', { class: 'bar' }, h('i', { class: cls, style: `width:${pct}%` })), h('span', {}, text));
}

/** Food eaten per season by the whole tribe. */
const upkeep = (s: GameState): number => s.penguins.length;

// ---------------------------------------------------------------- header + dock

function renderHeader(): void {
  if (!game) {
    seasonEl.textContent = 'ぺんぎん族';
    regionEl.textContent = '南極進化記';
    statsEl.replaceChildren();
    return;
  }
  const s = game;
  seasonEl.textContent = seasonLabel(s.turn);
  regionEl.textContent = regionDef(s.regionId).name + (s.coldwave > 0 ? '・寒波' : '');
  const low = s.food < upkeep(s);
  statsEl.replaceChildren(
    h('li', { class: low ? 'warn' : undefined }, `食料 ${s.food}`),
    h('li', {}, `モリ ${s.tools}`),
    h('li', {}, `${s.penguins.length}羽`),
    h('li', {}, `寒さ ${coldness(s)}`),
    h('li', {}, `第${s.maxGeneration}世代`),
  );
}

function renderDock(): void {
  if (!game) {
    dockEl.hidden = true;
    tabsEl.hidden = true;
    return;
  }
  const s = game;
  dockEl.hidden = false;
  tabsEl.hidden = false;
  if (s.moveTo) {
    dockInfo.replaceChildren(h('b', {}, `${regionDef(s.moveTo).name}へひっこし`), h('br'), `食料 -${moveCost(s)}・この季節はしごとなし`);
    advanceBtn.textContent = 'ひっこす';
    return;
  }
  const counts = new Map<ActionId, number>();
  for (const p of s.penguins) if (canWork(p)) counts.set(p.action, (counts.get(p.action) ?? 0) + 1);
  const jobs = ACTION_IDS.filter((a) => counts.get(a)).map((a) => `${JOB_SHORT[a]}${counts.get(a)}`).join('・') || 'はたらけるペンギンがいない';
  const low = s.food < upkeep(s);
  dockInfo.replaceChildren(
    h('b', {}, jobs),
    h('br'),
    low ? h('span', { class: 'bad' }, `食料が足りない（毎季節 ${upkeep(s)} 食べる）`) : `毎季節 ${upkeep(s)} 食べる`,
  );
  advanceBtn.textContent = '季節をすすめる';
}

function renderTabs(): void {
  for (const b of tabsEl.querySelectorAll<HTMLButtonElement>('button')) {
    b.setAttribute('aria-selected', String(b.dataset.tab === tab));
    b.tabIndex = b.dataset.tab === tab ? 0 : -1;
  }
}

function render(): void {
  renderHeader();
  renderDock();
  if (!game) {
    viewEl.replaceChildren(titleView());
    return;
  }
  renderTabs();
  const views: Record<Tab, () => HTMLElement[]> = { herd: herdView, land: landView, tech: techView, log: logView };
  const scroll = viewEl.scrollTop;
  viewEl.replaceChildren(...views[tab]());
  viewEl.scrollTop = scroll;
}

// ---------------------------------------------------------------- title

function titleView(): HTMLElement {
  const saved = loadGame(store);
  return h(
    'section',
    { class: 'panel title-card' },
    h('p', { class: 'logo' }, 'ぺんぎん族'),
    h('p', { class: 'sub' }, '南極の氷の上で、ペンギンの群れを育て、進化させよう'),
    h(
      'div',
      { class: 'buttons' },
      saved && h('button', { type: 'button', class: 'primary', onclick: () => resume(saved) }, `つづきから（${seasonLabel(saved.turn)}）`),
      h('button', { type: 'button', class: saved ? 'secondary' : 'primary', onclick: () => (saved ? confirmNew() : startNew()) }, 'はじめから'),
      h('button', { type: 'button', class: 'ghost', onclick: howto }, 'あそびかた'),
    ),
  );
}

function confirmNew(): void {
  openSheet([
    h('h2', { id: 'sheetTitle' }, '新しくはじめますか？'),
    h('p', {}, 'いまの群れのセーブは消えます。'),
    h(
      'div',
      { class: 'sheet-actions' },
      h('button', { type: 'button', class: 'secondary', onclick: closeSheet }, 'やめる'),
      h('button', { type: 'button', class: 'primary', onclick: () => { closeSheet(); startNew(); } }, 'はじめから'),
    ),
  ]);
}

function startNew(): void {
  game = newGame((Math.random() * 2 ** 31) | 0);
  history = [];
  tab = 'herd';
  persist();
  render();
  openSheet([
    h('h2', { id: 'sheetTitle' }, 'はじまり'),
    h('p', {}, 'ここは南極半島。6羽のペンギンが、氷の上で身をよせあっている。'),
    h('p', {}, `えさをとり、ひなを育て、知恵をつけて、いつか ちえ${SAPIENS_WIT} をこえる「かしこいペンギン」が生まれる日まで、群れを生きのびさせよう。`),
    h('p', { class: 'note' }, 'ペンギンをタップしてしごとを決め、下の「季節をすすめる」を押そう。'),
    h('button', { type: 'button', class: 'primary wide', onclick: closeSheet }, 'はじめる'),
  ]);
}

function resume(s: GameState): void {
  game = s;
  history = [];
  tab = 'herd';
  render();
}

function howto(): void {
  openSheet([
    h('h2', { id: 'sheetTitle' }, 'あそびかた'),
    h(
      'ol',
      { class: 'howto' },
      h('li', {}, '1ターンは1季節。ペンギンをタップしてしごとを決め、「季節をすすめる」。'),
      h('li', {}, 'オキアミとり：安定して食料がとれる。漁：魚がとれるが、素手だとけがをしやすい。素手で何度か漁をするとモリを思いつく。'),
      h('li', {}, 'ひなたぼっこ：オスとメスがつがいになり、つがいがそろって休むとひなが生まれる。発明のひらめきもたまる。'),
      h('li', {}, '族長（★）と同じしごとのペンギンははかどる。いのりは族長だけ。'),
      h('li', {}, '食料は1羽1季節に1つ。3季節続けて足りないとうえ死に。食料は季節ごとに1割くさる。'),
      h('li', {}, 'えさは土地ごとに限りがある。減ったら「土地」タブからとなりへひっこそう（1羽につき食料1）。'),
      h('li', {}, '冬は寒くてえさも少ない。シャチ、ヒョウアザラシ、ブリザード、ほかの群れにも注意。'),
      h('li', {}, 'ひなは両親の力を受けつぐ。年をとると死ぬので、世代をつないでいこう。'),
      h('li', {}, `発明を5つすべて身につけ、ちえ${SAPIENS_WIT}以上のひなが生まれたらクリア。全滅したらゲームオーバー。`),
    ),
    h('button', { type: 'button', class: 'primary wide', onclick: closeSheet }, 'とじる'),
  ]);
}

// ---------------------------------------------------------------- herd tab

function herdView(): HTMLElement[] {
  const s = g();
  const out: HTMLElement[] = [];
  if (s.moveTo) {
    out.push(
      h(
        'div',
        { class: 'notice' },
        h('span', {}, `次の季節は${regionDef(s.moveTo).name}へひっこす（しごとなし）`),
        h('button', { type: 'button', class: 'ghost', onclick: () => { setMove(s, null); persist(); render(); } }, 'やめる'),
      ),
    );
  } else {
    out.push(
      h('div', { class: 'row-head' }, h('h2', {}, 'まとめて指示')),
      h(
        'div',
        { class: 'chips' },
        ...ACTION_IDS.filter((a) => a !== 'pray').map((a) =>
          h(
            'button',
            {
              type: 'button',
              class: 'chip',
              disabled: a === 'craft' && !hasTech(s, 'mori'),
              onclick: () => {
                const n = setAll(s, a);
                persist();
                render();
                toast(`${n}羽を「${ACTION_NAMES[a]}」にした`);
              },
            },
            `全員 ${ACTION_NAMES[a]}`,
          ),
        ),
      ),
    );
  }
  const order = [...s.penguins].sort((a, b) => Number(isAdult(b)) - Number(isAdult(a)) || Number(b.id === s.chiefId) - Number(a.id === s.chiefId));
  out.push(h('div', { class: 'row-head' }, h('h2', {}, `群れ ${s.penguins.length}羽`)), h('div', { class: 'list' }, ...order.map((p) => penguinRow(s, p))));
  return out;
}

function jobChip(s: GameState, p: Penguin): HTMLElement {
  if (!isAdult(p)) return h('span', { class: 'job off' }, 'ひな');
  if (p.status !== 'ok') return h('span', { class: 'job off' }, STATUS_NAMES[p.status]);
  if (s.moveTo) return h('span', { class: 'job off' }, 'ひっこし');
  return h('span', { class: `job ${p.action}` }, ACTION_NAMES[p.action]);
}

function penguinRow(s: GameState, p: Penguin): HTMLElement {
  const mate = p.mateId !== null ? findPenguin(s, p.mateId) : undefined;
  return h(
    'button',
    { type: 'button', class: 'peng', onclick: () => penguinSheet(p.id) },
    h('img', { src: penguinIcon(p), alt: '' }),
    h(
      'div',
      { class: 'who' },
      h(
        'div',
        { class: 'name' },
        p.id === s.chiefId && h('span', { class: 'crown', title: '族長' }, '★'),
        p.name,
        h('small', {}, `${p.sex === 'M' ? '♂' : '♀'} ${ageYears(p)}才`),
        mate && h('span', { class: 'tag love' }, `♥${mate.name}`),
      ),
      h(
        'div',
        { class: 'meta' },
        h('span', {}, `力${p.power}`),
        h('span', {}, `泳${p.swim}`),
        h('span', {}, `知${p.wit}`),
        h('span', {}, `寒${p.warmth}`),
        p.hunger > 0 && h('span', { class: 'tag bad' }, 'はらぺこ'),
      ),
    ),
    jobChip(s, p),
  );
}

/** The next penguin after `id` (in list order) that can be given a job. */
function nextWorker(s: GameState, id: number): Penguin | undefined {
  const ws = s.penguins.filter(canWork);
  const i = ws.findIndex((p) => p.id === id);
  return ws[i + 1];
}

function penguinSheet(id: number): void {
  const s = g();
  const p = findPenguin(s, id);
  if (!p) return closeSheet();
  selected = id;
  const mate = p.mateId !== null ? findPenguin(s, p.mateId) : undefined;
  const status = !isAdult(p)
    ? `ひな（あと${ADULT_AGE - p.age}季節でおとな）`
    : `${STATUS_NAMES[p.status]}${p.statusTurns ? `（あと${p.statusTurns}季節）` : ''}`;
  const next = nextWorker(s, id);
  const canAssign = !s.moveTo && canWork(p);
  openSheet(
    [
      h(
        'div',
        { class: 'sheet-head' },
        h('img', { src: penguinIcon(p), alt: '' }),
        h(
          'div',
          {},
          h('h2', { id: 'sheetTitle' }, p.id === s.chiefId ? `★${p.name}` : p.name),
          h('div', { class: 'note' }, `${p.sex === 'M' ? 'オス' : 'メス'}・${ageYears(p)}才・第${p.generation}世代・${status}`),
          h('div', { class: 'note' }, `つがい：${mate ? mate.name : 'なし'}・寿命まであと${Math.max(0, Math.ceil((p.lifespan - p.age) / 4))}年ほど${p.hunger ? '・はらぺこ' : ''}`),
        ),
        h('button', { type: 'button', class: 'ghost', 'aria-label': 'とじる', onclick: closeSheet }, '✕'),
      ),
      h(
        'div',
        { class: 'statgrid' },
        ...([['ちから', p.power], ['およぎ', p.swim], ['ちえ', p.wit], ['さむさ', p.warmth]] as const).map(([k, v]) =>
          h('div', {}, h('small', {}, k), h('b', {}, String(v))),
        ),
      ),
      canAssign
        ? h(
            'div',
            { class: 'jobs' },
            ...ACTION_IDS.map((a) => {
              const block = actionBlock(s, p, a);
              return h(
                'button',
                {
                  type: 'button',
                  class: `jobbtn ${a}${p.action === a ? ' on' : ''}`,
                  disabled: block !== null,
                  'aria-pressed': String(p.action === a),
                  onclick: () => {
                    setAction(s, p.id, a);
                    persist();
                    render();
                    if (next) penguinSheet(next.id);
                    else {
                      closeSheet();
                      toast('全員のしごとを決めた');
                    }
                  },
                },
                h('b', {}, ACTION_NAMES[a]),
                h('small', {}, block ?? JOB_HINT[a]),
              );
            }),
          )
        : h('p', { class: 'note' }, s.moveTo && canWork(p) ? 'この季節はひっこしをするので、しごとはありません。' : actionBlock(s, p, 'krill') ?? ''),
      h(
        'div',
        { class: 'sheet-actions' },
        isAdult(p) && p.id !== s.chiefId &&
          h('button', { type: 'button', class: 'secondary', onclick: () => { setChief(s, p.id); persist(); render(); penguinSheet(p.id); toast(`${p.name}が族長になった`); } }, '族長にする'),
        next && canAssign && h('button', { type: 'button', class: 'secondary', onclick: () => penguinSheet(next.id) }, `つぎ：${next.name} ›`),
      ),
    ],
    () => (selected = null),
  );
}

// ---------------------------------------------------------------- land tab

function regionPanel(s: GameState, id: RegionId, here: boolean): HTMLElement {
  const d = regionDef(id);
  const r = s.regions[id];
  const block = here ? null : moveBlock(s, id);
  const planned = s.moveTo === id;
  return h(
    'section',
    { class: 'panel' },
    h('div', { class: 'row-head' }, h('h3', {}, d.name), here && h('span', { class: 'tag' }, 'いまいる土地')),
    h('p', { class: 'note' }, d.note),
    meter('オキアミ', r.krill, d.krillMax, 'krill', level(r.krill, d.krillMax)),
    meter('魚', r.fish, d.fishMax, 'fish', level(r.fish, d.fishMax)),
    meter('寒さ', d.cold, 40, 'cold', d.cold >= 20 ? 'きびしい' : d.cold >= 10 ? 'ふつう' : 'おだやか'),
    r.orca > 0 && h('p', { class: 'warnline' }, 'シャチがうろついている！ 海に出ると危ない'),
    !here &&
      (planned
        ? h('button', { type: 'button', class: 'secondary', onclick: () => { setMove(s, null); persist(); render(); } }, 'ひっこしをやめる')
        : h(
            'button',
            {
              type: 'button',
              class: 'primary',
              disabled: block !== null,
              onclick: () => {
                setMove(s, id);
                persist();
                render();
                toast(`次の季節、${d.name}へひっこす`);
              },
            },
            block ?? `ここへひっこす（食料 ${moveCost(s)}）`,
          )),
  );
}

function landView(): HTMLElement[] {
  const s = g();
  return [
    regionPanel(s, s.regionId, true),
    h('div', { class: 'row-head' }, h('h2', {}, 'となりの土地')),
    ...neighbors(s.regionId).map((id) => regionPanel(s, id, false)),
    h('p', { class: 'note' }, 'ひっこすと、その季節はしごとができません。えさは時間がたつと少しずつもどります。'),
  ];
}

// ---------------------------------------------------------------- tech tab

function techView(): HTMLElement[] {
  const s = g();
  const open = availableTechs(s);
  const pct = Math.round(researchProgress(s) * 100);
  return [
    h(
      'section',
      { class: 'panel' },
      h('h3', {}, `発明 ${s.techs.length} / ${TECHS.length}`),
      meter('ひらめき', pct, 100, '', open.length ? `${pct}%` : '—'),
      h('p', { class: 'note' }, open.length ? 'ひなたぼっこをすると、ひらめきがたまります。' : 'いまは何も思いつきそうにない。'),
    ),
    ...TECHS.map((t) => {
      const known = hasTech(s, t.id);
      const hint =
        t.id === 'mori' && !known && s.bareHunts < BARE_HUNTS_FOR_MORI
          ? `素手の漁をもう少し（あと${BARE_HUNTS_FOR_MORI - s.bareHunts}回）`
          : open.includes(t.id)
            ? 'ひらめきそう……'
            : 'まだ見当もつかない';
      return h(
        'section',
        { class: `panel tech${known ? ' known' : ''}` },
        h('span', { class: 'mark', 'aria-hidden': 'true' }, known ? '◆' : '◇'),
        h('div', {}, h('b', {}, known ? t.name : '？？？'), h('p', {}, known ? t.desc : hint)),
      );
    }),
  ];
}

// ---------------------------------------------------------------- log tab

function logView(): HTMLElement[] {
  if (!history.length) return [h('p', { class: 'note' }, 'まだ記録はありません。季節をすすめると、ここにできごとが残ります。')];
  return history.map((e) => h('section', { class: 'panel log' }, h('h3', {}, e.label), lines(e.lines)));
}

// ---------------------------------------------------------------- season

function advance(): void {
  const s = g();
  const label = seasonLabel(s.turn);
  const ls = resolveSeason(s);
  if (!ls.length) ls.push('しずかな季節だった。');
  history.unshift({ label, lines: ls });
  history = history.slice(0, 40);
  persist();
  render();
  openSheet([
    h('h2', { id: 'sheetTitle' }, `${label}のできごと`),
    lines(ls),
    h('button', { type: 'button', class: 'primary wide', onclick: () => (s.over ? ending() : closeSheet()) }, s.over ? '結果を見る' : 'つづける'),
  ]);
}

function ending(): void {
  const s = g();
  const best = s.penguins.reduce((a, p) => Math.max(a, p.wit), 0);
  const win = s.over === 'win';
  openSheet(
    [
      h('p', { class: 'big' }, win ? 'ペンギヌス誕生！' : '群れは全滅した'),
      ...(win
        ? [
            h('p', {}, `${s.sapiens}は、空を見上げて考えた。「ぼくたちは、どこから来て、どこへ行くのだろう」`),
            h('p', {}, '南極の氷の上に、かしこいペンギンが生まれた。群れの長い旅は、新しい時代をむかえる。'),
          ]
        : [h('p', {}, '南極の風だけが、氷の上をふきぬけていく……。')]),
      h(
        'div',
        { class: 'score' },
        h('div', {}, h('small', {}, '生きのびた'), h('b', {}, `${Math.floor(s.turn / 4)}年${s.turn % 4}季節`)),
        h('div', {}, h('small', {}, '世代'), h('b', {}, `第${s.maxGeneration}世代`)),
        h('div', {}, h('small', {}, '発明'), h('b', {}, `${s.techs.length}/${TECHS.length}`)),
        h('div', {}, h('small', {}, '生まれたひな'), h('b', {}, `${s.births}羽`)),
        best > 0 && h('div', {}, h('small', {}, '最高のちえ'), h('b', {}, String(best))),
        h('div', {}, h('small', {}, 'スコア'), h('b', {}, String(score(s)))),
      ),
      h('button', { type: 'button', class: 'primary wide', onclick: () => { closeSheet(); game = null; render(); } }, 'タイトルへ'),
    ],
    () => {
      game = null;
      render();
    },
  );
}

// ---------------------------------------------------------------- sheet

function openSheet(children: Child[], onClose: (() => void) | null = null): void {
  sheetBody.replaceChildren(...children.filter((c): c is Node | string => !!c));
  sheetOnClose = onClose;
  sheetEl.hidden = false;
  sheetBody.parentElement?.scrollTo(0, 0);
  sheetBody.querySelector<HTMLElement>('button.primary, .jobbtn.on, button')?.focus({ preventScroll: true });
}

function closeSheet(): void {
  if (sheetEl.hidden) return;
  sheetEl.hidden = true;
  const cb = sheetOnClose;
  sheetOnClose = null;
  selected = null;
  cb?.();
}

// ---------------------------------------------------------------- wiring

$('backdrop').addEventListener('click', closeSheet);
advanceBtn.addEventListener('click', advance);
tabsEl.addEventListener('click', (e) => {
  const b = (e.target as HTMLElement).closest<HTMLButtonElement>('button[data-tab]');
  if (!b) return;
  tab = b.dataset.tab as Tab;
  viewEl.scrollTop = 0;
  render();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeSheet();
});

let lastDraw = 0;
function frame(t: number): void {
  // ~10 frames a second keeps the pixel art choppy and cheap on battery.
  if (t - lastDraw > 100) {
    lastDraw = t;
    drawScene(ctx, game ?? demo, t, selected);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

render();
