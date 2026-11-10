import type { Character, CharId } from '../types';

// 凪・湊・源 are fictional. The history they tell in src/data/stages.ts is real.
export const CHARS: Readonly<Record<CharId, Character>> = {
  narr:     { name: '', role: '', mark: '', color: 'transparent' },
  nagi:     { name: '凪', role: '新人越冬隊員', mark: '凪', color: '#2a63a8' },
  minato:   { name: '湊', role: '通信・作戦担当', mark: '湊', color: '#2f7f8a' },
  gen:      { name: '源', role: '越冬十回のベテラン隊員', mark: '源', color: '#5b6470' },
  // Only for words that were really written down at the time (translated).
  log:      { name: '日誌', role: '当時の記録より', mark: '記', color: '#7a5c3e' },
};
