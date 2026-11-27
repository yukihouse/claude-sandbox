/** Names given to penguins; a repeated name gets a ２世, ３世… suffix. */
export const NAMES: readonly string[] = [
  'ペンタ', 'ギンジ', 'コオリ', 'ユキ', 'ミゾレ', 'アラレ', 'シモ', 'フブキ', 'ツララ', 'ハヤテ',
  'オーロ', 'クリル', 'イワシ', 'カイ', 'ナミ', 'シオ', 'ソラ', 'ホシ', 'ヒョウ', 'ヒサメ',
  'ポポ', 'ピピ', 'トト', 'モモ', 'ルル', 'ココ', 'チャチャ', 'ペペ', 'ノノ', 'キキ',
  'ハク', 'ルリ', 'アオ', 'シロ', 'クロ', 'コハク', 'マシロ', 'ミナト', 'ウミ', 'カゼ',
];

const KANJI_DIGITS = '０１２３４５６７８９';

/** Full-width number, e.g. 12 → "１２". */
export const zenkaku = (n: number): string =>
  String(n).replace(/\d/g, (d) => KANJI_DIGITS[Number(d)] as string);
