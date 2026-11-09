import type { Character, CharId } from '../types';

export const CHARS: Readonly<Record<CharId, Character>> = {
  narr:     { name: '', role: '', mark: '', color: 'transparent' },
  nagi:     { name: '凪', role: 'オーロラ隊 隊長', mark: '凪', color: '#2a63a8' },
  minato:   { name: '湊', role: '通信・作戦担当', mark: '湊', color: '#2f7f8a' },
  gen:      { name: '源', role: '越冬十回のベテラン隊員', mark: '源', color: '#5b6470' },
  kuki:     { name: '九鬼', role: '黒氷社 現場指揮官', mark: '鬼', color: '#b8432c' },
  saku:     { name: '朔', role: '漂流団の頭', mark: '朔', color: '#ad7e1a' },
  himuro:   { name: '氷室', role: '黒氷社 総帥', mark: '氷', color: '#3a3340' },
};
