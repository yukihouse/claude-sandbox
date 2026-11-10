import type { Character, CharId } from '../types';

// 凪・湊・源 are fictional (faces: src/data/portraits.ts).
// The history they tell in src/data/stages.ts is real.
export const CHARS: Readonly<Record<CharId, Character>> = {
  narr:     { name: '', role: '' },
  nagi:     { name: '凪', role: '新人越冬隊員' },
  minato:   { name: '湊', role: '通信・作戦担当' },
  gen:      { name: '源', role: '越冬十回のベテラン隊員' },
  // Only for words that were really written down at the time (translated).
  log:      { name: '日誌', role: '当時の記録より' },
};
