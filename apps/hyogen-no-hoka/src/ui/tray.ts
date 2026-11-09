import { GALE_SECONDS } from '../config';
import { galeLeft, selectedCastle, sendCount } from '../game/actions';
import type { GameState, ItemKind } from '../types';
import { $ } from './dom';

const ITEMS: readonly ItemKind[] = ['reinforce', 'gale', 'wall'];
const IDLE_HINT = '自軍の基地（青）をタップして出動';
const MODE_HINT = {
  reinforce: '補給便を届ける自軍の基地をタップ（もう一度押すと取り消し）',
  wall: '防寒壁を張る自軍の基地をタップ（もう一度押すと取り消し）',
} as const;
const GALE_DESC = `移動が${GALE_SECONDS}秒間 2倍速`;

/** The command tray under the map: send ratio and item buttons. */
export class Tray {
  private readonly order = $('#order');
  private readonly hint = $('#hint');
  private readonly sendbar = $('#sendbar');
  private readonly ratio = $<HTMLInputElement>('#ratio');
  private readonly ratioOut = $<HTMLOutputElement>('#ratioOut');
  readonly buttons: Readonly<Record<ItemKind, HTMLButtonElement>> = {
    reinforce: $<HTMLButtonElement>('#it-reinforce'),
    gale: $<HTMLButtonElement>('#it-gale'),
    wall: $<HTMLButtonElement>('#it-wall'),
  };
  private lastTick = 0;

  /** Percentage of a base's crew to send (10–100). */
  get pct(): number {
    return Number(this.ratio.value);
  }

  onRatioInput(fn: () => void): void {
    this.ratio.addEventListener('input', fn);
  }

  /** Redraw everything that depends on selection, mode and item counts. */
  update(S: GameState | null): void {
    const sel = S ? selectedCastle(S) : null;
    this.order.classList.toggle('selecting', !!sel);
    this.order.classList.toggle('targeting', !!S?.mode);
    this.sendbar.hidden = !sel;
    this.hint.hidden = !!sel;
    this.hint.textContent = S?.mode ? MODE_HINT[S.mode] : IDLE_HINT;
    const galeOn = !!S && galeLeft(S) > 0;
    for (const k of ITEMS) {
      const b = this.buttons[k];
      const n = S ? S.items[k] : 0;
      $('.icount', b).textContent = String(n);
      b.disabled = n <= 0 && !(k === 'gale' && galeOn);
      b.classList.toggle('active', !!S && (S.mode === k || (k === 'gale' && galeOn)));
    }
  }

  /** Per-frame refresh of the live numbers. */
  tick(S: GameState | null): void {
    if (!S) return;
    const sel = selectedCastle(S);
    if (sel) this.ratioOut.textContent = `${this.pct}%・${sendCount(sel, this.pct)}人`;
    const left = galeLeft(S);
    $('.idesc', this.buttons.gale).textContent = left > 0 ? `発動中 あと${left}秒` : GALE_DESC;
    if (S.t - this.lastTick > 0.5 || S.t < this.lastTick) {
      this.lastTick = S.t;
      this.update(S);
    }
  }
}
