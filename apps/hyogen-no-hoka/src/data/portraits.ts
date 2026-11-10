import type { CharId } from '../types';

/*
 * Ukiyo-e style bust portraits (大首絵) for the story scenes, drawn as inline
 * SVG so they stay sharp, cost a few KB and work offline.
 *
 * The look borrows from woodblock prints: flat colours with no shading, a
 * sumi (ink-black) outline, slit eyes and small red lips, a pale gofun face,
 * snow falling over an indigo ground as in Hiroshige's snow scenes, and a
 * cartouche with the name in the corner. Everyone wears the orange or teal
 * cold-weather gear of a modern Antarctic expedition.
 */

const SUMI = '#1d1a17';
const GOFUN = '#f4e7d2';
const BENI = '#b8322a';
const LINE = `stroke="${SUMI}" stroke-linecap="round" stroke-linejoin="round"`;

/** Falling snow: the same scatter on every portrait, from a fixed list. */
const SNOW = [
  [6, 8], [15, 4], [27, 9], [47, 6], [55, 14], [4, 22], [52, 27], [8, 37], [56, 40], [3, 52],
  [11, 15], [36, 3], [57, 52], [44, 16], [21, 18],
]
  .map(([x, y], k) => `<circle cx="${x}" cy="${y}" r="${k % 3 ? 0.9 : 1.4}" fill="#fff" opacity="0.9"/>`)
  .join('');

/** The name cartouche in the top right corner, one character per row. */
function cartouche(name: string): string {
  const chars = [...name];
  const text = chars
    .map((c, k) => `<text x="52.5" y="${10.6 + k * 8}" font-size="7" font-weight="700" text-anchor="middle" fill="${SUMI}" font-family="'Shippori Mincho B1',serif">${c}</text>`)
    .join('');
  return `<rect x="48" y="3" width="9" height="${chars.length * 8 + 3}" fill="#f6efd9" stroke="${SUMI}" stroke-width="0.8"/>${text}`;
}

/** Ichimonji bokashi: the dark band fading down from the top edge of a print. */
const bokashi = (id: string, colour: string): string =>
  `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${colour}"/><stop offset="1" stop-color="${colour}" stop-opacity="0"/></linearGradient></defs>` +
  `<rect width="60" height="22" fill="url(#${id})"/>`;

interface Look {
  /** Background colour behind the snow. */
  ground: string;
  /** Parka colour, and the darker colour of its folds. */
  coat: string;
  fold: string;
  /** Hair (or cap) drawn under the hood, then anything drawn over the face. */
  hair: string;
  extra: string;
  /** Eyebrows and eye-corner lines for age and mood. */
  brows: string;
  name: string;
  /** Unique id for the gradient inside the SVG. */
  id: string;
}

function figure(l: Look): string {
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" role="img" aria-label="${l.name}">`,
    `<rect width="60" height="80" fill="${l.ground}"/>`,
    bokashi(`bk-${l.id}`, '#101820'),
    // a band of snowy ground behind the shoulders
    `<path d="M0 62 Q15 57 30 60 T60 58 V80 H0Z" fill="#e9eef0"/>`,
    SNOW,
    // shoulders and parka, with the folds cut as flat shapes
    `<path d="M4 80 C6 66 14 60 22 58 L38 58 C46 60 54 66 56 80Z" fill="${l.coat}" ${LINE} stroke-width="1.2"/>`,
    `<path d="M22 66 L20 80 M40 66 L42 80" fill="none" stroke="${l.fold}" stroke-width="2"/>`,
    `<path d="M28 60 L29 80" ${LINE} stroke-width="0.9"/>`,
    // the head is drawn large, as in a 大首絵, so it is scaled up around the neck
    '<g transform="translate(30 60) scale(1.18) translate(-30 -60)">',
    // fur-trimmed hood, edged with scallops like stylised clouds
    `<path d="M14 58 C10 40 14 20 30 17 C46 20 50 40 46 58 C42 62 18 62 14 58Z" fill="${l.coat}" ${LINE} stroke-width="1.2"/>`,
    `<path d="M17 56 C13 42 16 25 30 22 C44 25 47 42 43 56 C39 59 21 59 17 56Z" fill="#c9b48e" ${LINE} stroke-width="1"/>`,
    `<path d="M18 50 q-2 -3 0 -6 q-2 -3 0 -6 q-1 -3 1 -6 q0 -3 3 -5 q1 -3 4 -3 q2 -2 5 -1 q3 -1 5 1 q3 0 4 3 q3 2 3 5 q2 3 1 6 q2 3 0 6 q2 3 0 6" fill="none" stroke="#8f7a55" stroke-width="0.9"/>`,
    l.hair,
    // face: three-quarter view looking right, gofun white with a sumi outline
    `<path d="M22 34 C21 44 23 51 30 54 C36 53 39 48 39.5 42 L41 39.5 L39.6 38 C40 33 37 28 31 27 C26 27 22.5 30 22 34Z" fill="${GOFUN}" ${LINE} stroke-width="1"/>`,
    // ear
    `<path d="M22.4 38 c-2 -1 -3 2 -1 4 c1 1 1.5 1 1.6 0.5" fill="${GOFUN}" ${LINE} stroke-width="0.8"/>`,
    // slit eyes with small pupils, the ukiyo-e way
    `<path d="M27 38.6 q2.5 -1.6 5 0.2 M34.4 38.4 q2 -1.4 3.8 0" fill="none" ${LINE} stroke-width="1"/>`,
    `<circle cx="30.3" cy="38.8" r="0.8" fill="${SUMI}"/><circle cx="36.6" cy="38.6" r="0.7" fill="${SUMI}"/>`,
    l.brows,
    // nose (one hooked line) and small red lips
    `<path d="M38.4 39 q1.2 3.4 -0.6 4.4" fill="none" ${LINE} stroke-width="0.8"/>`,
    `<path d="M33 47.6 q2 -0.9 4 0 q-2 1.4 -4 0Z" fill="${BENI}"/>`,
    l.extra,
    '</g>',
    cartouche(l.name),
    '</svg>',
  ].join('');
}

/** Short black hair swept to one side, for 凪. */
const NAGI_HAIR =
  `<path d="M21.5 36 C20 27 26 23 32 23.5 C38 24 41 28 40.5 34 C37 31 33 29.5 29 31 C27 31.5 24 33 21.5 36Z" fill="${SUMI}"/>` +
  `<path d="M25 31 q4 -4 10 -3 M28 30 q4 -2 9 0" fill="none" stroke="#4a4540" stroke-width="0.5"/>`;

/** A knit cap with a folded brim, for 源. */
const GEN_CAP =
  `<path d="M21 35 C20 25 26 21 31 21 C37 21 41 25 41 34 Z" fill="#6b4a33" ${LINE} stroke-width="1"/>` +
  `<path d="M21 35 C26 31.5 36 31 41 34 L41 31 C36 28.5 26 28.5 21 32Z" fill="#8a6446" ${LINE} stroke-width="0.8"/>` +
  `<path d="M24 26 v4 M27 24 v5 M30 23 v6 M33 23 v6 M36 24 v5 M39 26 v4" stroke="#4e3524" stroke-width="0.5"/>`;

/** A white beard in flowing brush strokes, deep lines at the eyes, for 源. */
const GEN_FACE =
  `<path d="M26 46 C25 52 28 58 32 60 C35 58 39 55 39.5 47 C37 49.5 35 50 33 49.6 C31 49.4 28 48 26 46Z" fill="#f7f5ef" ${LINE} stroke-width="0.8"/>` +
  `<path d="M28 50 q1 4 3 7 M31 50 q1 4 2 8 M34 50 q0.5 4 0 7 M37 49 q-0.5 3 -1.5 5" fill="none" stroke="#b7b2a8" stroke-width="0.5"/>` +
  `<path d="M31 46.4 q3 -1.6 7 -0.4" fill="none" stroke="#f7f5ef" stroke-width="2.2" stroke-linecap="round"/>` +
  `<path d="M31 46.4 q3 -1.6 7 -0.4" fill="none" ${LINE} stroke-width="0.6"/>` +
  `<path d="M26 41 q1.5 1 3 0.6 M33 31.5 q3 -0.6 5 0.6" fill="none" ${LINE} stroke-width="0.5"/>`;

/** Short hair and a radio headset with a boom microphone, for 湊. */
const MINATO_HAIR =
  `<path d="M21.5 36 C20.5 28 25 23.5 31 23.5 C37 23.5 41 27.5 40.6 33.5 C38 30 35 29 31 29.3 C27 29.6 24 32 21.5 36Z" fill="${SUMI}"/>` +
  `<path d="M22 34 C22 24 40 22 40.6 32" fill="none" stroke="#3a3a3a" stroke-width="1.6"/>`;
const MINATO_SET =
  `<circle cx="29.8" cy="38.8" r="2.7" fill="none" ${LINE} stroke-width="0.6"/>` +
  `<circle cx="36.6" cy="38.6" r="2.3" fill="none" ${LINE} stroke-width="0.6"/>` +
  `<path d="M32.5 38.4 q1.1 -0.6 1.8 0 M27.1 38.4 L23 37.4" fill="none" ${LINE} stroke-width="0.6"/>` +
  `<rect x="19.6" y="35.5" width="4" height="6" rx="1.5" fill="#3a3a3a" ${LINE} stroke-width="0.6"/>` +
  `<path d="M22 41 Q25 50 32.5 49.5" fill="none" stroke="#3a3a3a" stroke-width="0.9"/>` +
  `<circle cx="33" cy="49.4" r="1.1" fill="#3a3a3a"/>`;

const BROWS_YOUNG = `<path d="M26.6 35.4 q3 -1.6 5.8 -0.6 M34.4 35 q2.2 -1 4 0" fill="none" ${LINE} stroke-width="0.7"/>`;
const BROWS_OLD =
  `<path d="M26.2 35.4 q3 -2.4 6.4 -1 M34 35 q2.6 -1.8 4.6 -0.2" fill="none" stroke="#e8e4da" stroke-width="1.8" stroke-linecap="round"/>` +
  `<path d="M26.2 35.4 q3 -2.4 6.4 -1 M34 35 q2.6 -1.8 4.6 -0.2" fill="none" ${LINE} stroke-width="0.5"/>`;

/** A still life for the expedition diaries: an open notebook, a pencil and a candle. */
const LOG =
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" role="img" aria-label="日誌">` +
  `<rect width="60" height="80" fill="#9c7a43"/>` +
  bokashi('bk-log', '#3b2a14') +
  // candle and flame
  `<rect x="9" y="22" width="7" height="22" fill="#f1ead6" ${LINE} stroke-width="0.9"/>` +
  `<path d="M12.5 21 q-3 -5 0 -10 q3 5 0 10Z" fill="#e8a33a" ${LINE} stroke-width="0.7"/>` +
  `<path d="M12.5 21 q-1.2 -2.5 0 -5 q1.2 2.5 0 5Z" fill="#fbe7a6"/>` +
  `<rect x="6" y="44" width="13" height="3" fill="#5b4a3a" ${LINE} stroke-width="0.7"/>` +
  // open notebook, its lines written in brush strokes
  `<path d="M6 58 L30 52 L54 58 L54 74 L30 69 L6 74Z" fill="#f4ecd6" ${LINE} stroke-width="1"/>` +
  `<path d="M30 52 V69" ${LINE} stroke-width="0.8"/>` +
  `<path d="M10 60 L26 56.4 M10 63.5 L26 60 M10 67 L24 63.8 M34 56.4 L50 60 M34 60 L50 63.5 M34 63.6 L46 66.4" stroke="#5d564c" stroke-width="0.7"/>` +
  // pencil
  `<path d="M35 49 L55 41 L56.2 43.6 L36.2 51.6Z" fill="#c7492f" ${LINE} stroke-width="0.7"/>` +
  `<path d="M35 49 L32.2 51.2 L36.2 51.6Z" fill="#e6c9a0" ${LINE} stroke-width="0.6"/>` +
  cartouche('日誌') +
  '</svg>';

/** One portrait per speaker; the narrator has none. */
export const PORTRAITS: Readonly<Record<Exclude<CharId, 'narr'>, string>> = {
  nagi: figure({ id: 'nagi', name: '凪', ground: '#2c4a6e', coat: '#d9582b', fold: '#a8401d', hair: NAGI_HAIR, extra: '', brows: BROWS_YOUNG }),
  minato: figure({ id: 'minato', name: '湊', ground: '#35605c', coat: '#2f7f8a', fold: '#235f68', hair: MINATO_HAIR, extra: MINATO_SET, brows: BROWS_YOUNG }),
  gen: figure({ id: 'gen', name: '源', ground: '#4b4038', coat: '#d9582b', fold: '#a8401d', hair: GEN_CAP, extra: GEN_FACE, brows: BROWS_OLD }),
  log: LOG,
};
