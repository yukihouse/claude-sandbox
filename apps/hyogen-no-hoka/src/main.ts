import './style.css';
import { MAX_DT } from './config';
import { STAGES } from './data/stages';
import { release, select, tapInItemMode, useItem } from './game/actions';
import { aiThink } from './game/ai';
import { createState } from './game/rules';
import { update } from './game/update';
import { type Drag, render, type Scene } from './render/draw';
import { readPalette } from './render/palette';
import { buildTerrain } from './render/terrain';
import { registerServiceWorker, warmFonts, whenControlled } from './pwa';
import { createView, hitCastle, layout, toS } from './render/view';
import { loadProgress, nextChapter, recordWin, saveProgress } from './save';
import type { AiOwner, GameState, ItemKind } from './types';
import { $ } from './ui/dom';
import { Story } from './ui/story';
import { Tray } from './ui/tray';

// ---------- setup ----------
function getStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}
const storage = getStorage();
const progress = loadProgress(storage);

const field = $('#field');
const canvas = $<HTMLCanvasElement>('#map');
const ctx = canvas.getContext('2d');
if (!ctx) throw new Error('canvas 2d is not available');

const view = createView();
const scene: Scene = {
  ctx,
  view,
  palette: readPalette(),
  terrain: null,
  pointer: { x: 0, y: 0, inside: false },
  drag: null,
  reduceMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
};
const tray = new Tray();
const story = new Story();

let S: GameState | null = null;

// ---------- stage flow ----------
function startStage(i: number): void {
  S = createState(i);
  const stage = S.stage;
  $('#chapNo').textContent = stage.no;
  $('#chapName').textContent = stage.name;
  rebuildTerrain();
  tray.update(S);
  hideAll();
  const started = S;
  story.play(stage.pre, () => {
    started.running = true;
  });
}

function rebuildTerrain(): void {
  if (!S || !view.cw || !scene.palette) return;
  scene.terrain = buildTerrain(view, S.i, S.stage, canvas.width, canvas.height, scene.palette);
}

function resize(): void {
  const r = field.getBoundingClientRect();
  view.cw = r.width;
  view.ch = r.height;
  view.dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.round(r.width * view.dpr);
  canvas.height = Math.round(r.height * view.dpr);
  layout(view);
  rebuildTerrain();
}

// ---------- input ----------
const hit = (x: number, y: number) => (S ? hitCastle(view, S.castles, x, y) : null);

function localPoint(e: PointerEvent): [number, number] {
  const r = canvas.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}

canvas.addEventListener('pointerdown', (e) => {
  if (!S || !S.running) return;
  const [x, y] = localPoint(e);
  scene.pointer = { x, y, inside: true };
  const c = hit(x, y);
  if (S.mode) {
    tapInItemMode(S, S.mode, c);
    tray.update(S);
    return;
  }
  if (c && c.owner === 1) {
    scene.drag = { from: c, x, y, moved: false };
    canvas.setPointerCapture(e.pointerId);
  } else {
    scene.drag = { from: null, x, y, moved: false };
  }
});
canvas.addEventListener('pointermove', (e) => {
  const [x, y] = localPoint(e);
  scene.pointer = { x, y, inside: true };
  const drag = scene.drag;
  if (drag && drag.from && Math.hypot(x - drag.x, y - drag.y) > 12) drag.moved = true;
});
canvas.addEventListener('pointerleave', () => {
  scene.pointer.inside = false;
});
canvas.addEventListener('pointerup', (e) => {
  const d: Drag | null = scene.drag;
  scene.drag = null;
  if (!S || !S.running || !d) return;
  const [x, y] = localPoint(e);
  release(S, d.moved ? d.from : null, hit(x, y), tray.pct);
  tray.update(S);
});
canvas.addEventListener('pointercancel', () => {
  scene.drag = null;
});

tray.onRatioInput(() => tray.tick(S));
for (const k of Object.keys(tray.buttons) as ItemKind[]) {
  tray.buttons[k].addEventListener('click', () => {
    if (!S) return;
    useItem(S, k);
    tray.update(S);
  });
}

document.addEventListener('keydown', (e) => {
  if (story.open && (e.key === 'Enter' || e.key === ' ')) {
    e.preventDefault();
    story.next();
  } else if (e.key === 'Escape' && S && S.running) togglePause(true);
});

// ---------- overlays ----------
function hideAll(): void {
  for (const id of ['title', 'story', 'result', 'pause']) $('#' + id).hidden = true;
}

function fmtTime(sec: number): string {
  const s = Math.floor(sec);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function showResult(S: GameState): void {
  const def = S.stage;
  const win = S.result === 'win';
  const i = S.i;
  if (win) {
    recordWin(progress, i, STAGES.length);
    saveProgress(storage, progress);
  }
  const stamp = $('#resStamp');
  stamp.textContent = win ? '勝利' : '敗北';
  stamp.className = 'stamp ' + (win ? 'win' : 'lose');
  $('#resTitle').textContent = `${def.no}　${def.name}`;
  $('#resText').textContent = win ? '黒氷社の旗はすべて降りた。' : '自軍の基地をすべて失った。態勢を立て直そう。';
  $('#resTime').textContent = fmtTime(S.t);
  $('#resCap').textContent = String(S.captured);
  const btns = $('#resBtns');
  btns.replaceChildren();
  const add = (label: string, cls: string, fn: () => void) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = cls;
    b.textContent = label;
    b.addEventListener('click', fn);
    btns.appendChild(b);
  };
  const last = i === STAGES.length - 1;
  if (win) {
    add(last ? '結末を見る' : '物語を進める', 'primary', () => {
      $('#result').hidden = true;
      story.play(def.post, () => (last ? showTitle() : startStage(i + 1)));
    });
  } else {
    add('もう一度挑む', 'primary', () => startStage(i));
  }
  add('章を選ぶ', 'secondary', showTitle);
  $('#result').hidden = false;
}

function togglePause(force?: boolean): void {
  if (!S || S.over || (!S.running && !S.paused)) return;
  const on = force ?? !S.paused;
  S.paused = on;
  S.running = !on;
  $('#pause').hidden = !on;
}
$('#pauseBtn').addEventListener('click', () => togglePause());
$('#resumeBtn').addEventListener('click', () => togglePause(false));
$('#retryBtn').addEventListener('click', () => {
  if (S) startStage(S.i);
});
$('#toTitleBtn').addEventListener('click', showTitle);
document.addEventListener('visibilitychange', () => {
  if (document.hidden && S && S.running) togglePause(true);
});

function showTitle(): void {
  hideAll();
  if (S) {
    S.running = false;
    S.paused = false;
  }
  const list = $('#chapters');
  list.replaceChildren();
  STAGES.forEach((st, i) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    const locked = i + 1 > progress.unlocked;
    const done = progress.cleared.includes(i);
    b.disabled = locked;
    const span = (cls: string, text: string) => {
      const el = document.createElement('span');
      el.className = cls;
      el.textContent = text;
      return el;
    };
    b.append(
      span('no', st.no),
      span('nm', locked ? '？？？' : st.name),
      span(done ? 'st done' : 'st', done ? '奪還' : locked ? '未開放' : '挑戦できる'),
    );
    b.addEventListener('click', () => startStage(i));
    li.appendChild(b);
    list.appendChild(li);
  });
  const next = nextChapter(progress, STAGES.length);
  const start = $<HTMLButtonElement>('#startBtn');
  start.textContent = progress.cleared.length === 0 ? '出動する' : `つづきから（${STAGES[next]?.no}）`;
  start.onclick = () => startStage(next);
  $('#title').hidden = false;
}

// ---------- loop ----------
/** Advance the running stage and react to its end. */
function step(dt: number): void {
  if (!S || !S.running) return;
  const selected = S.selected;
  const ended = update(S, dt);
  // an enemy took the selected base, or the stage ended
  if (S.selected !== selected || ended) tray.update(S);
  if (ended) showResult(S);
}

let last = performance.now();
function frame(now: number): void {
  const dt = Math.min(MAX_DT, (now - last) / 1000);
  last = now;
  step(dt);
  if (!scene.palette) {
    // the stylesheet was not applied yet when the game started: try again
    scene.palette = readPalette();
    rebuildTerrain();
  }
  render(scene, S, now / 1000);
  tray.tick(S);
  requestAnimationFrame(frame);
}

new ResizeObserver(resize).observe(field);
resize();
tray.update(S);
showTitle();
requestAnimationFrame(frame);
// After the first screen is up: install the Service Worker, then (once it controls
// the page, so the responses get cached) fetch the fonts for all game text.
window.addEventListener(
  'load',
  () => {
    if (!registerServiceWorker(navigator, location.protocol, import.meta.env.PROD)) return;
    const css = document.querySelector<HTMLLinkElement>('link[rel="stylesheet"][href*="fonts.googleapis.com"]');
    void whenControlled(navigator.serviceWorker).then(() =>
      warmFonts(document.fonts, __GAME_CHARS__, () => (css ? fetch(css.href, { mode: 'cors' }) : Promise.resolve())),
    );
  },
  { once: true },
);

// small hook for automated checks
declare global {
  interface Window {
    __game: unknown;
  }
}
window.__game = {
  get state() {
    return S;
  },
  STAGES,
  startStage,
  select: (id: number) => {
    const c = S?.castles[id];
    if (S && c) select(S, c);
  },
  aiThink: (owner: AiOwner) => S && aiThink(S, owner),
  toS: (x: number, y: number) => toS(view, x, y),
  step(sec: number) {
    const n = Math.round(sec / MAX_DT);
    for (let k = 0; k < n && S && S.running; k++) step(MAX_DT);
  },
  skipStory: () => story.skip(),
};
