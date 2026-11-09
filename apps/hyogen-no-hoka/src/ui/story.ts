import { CHARS } from '../data/chars';
import type { StoryLine } from '../types';
import { $ } from './dom';

/** The conversation overlay shown before and after each chapter. */
export class Story {
  private readonly overlay = $('#story');
  private queue: StoryLine[] = [];
  private total = 0;
  private done: (() => void) | null = null;

  constructor() {
    this.overlay.addEventListener('click', () => this.next());
    $('#skipBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.skip();
    });
  }

  get open(): boolean {
    return !this.overlay.hidden;
  }

  play(lines: readonly StoryLine[], done: () => void): void {
    this.queue = lines.slice();
    this.total = lines.length;
    this.done = done;
    this.overlay.hidden = false;
    this.next();
  }

  skip(): void {
    this.queue = [];
    this.next();
  }

  next(): void {
    const line = this.queue.shift();
    if (!line) {
      this.overlay.hidden = true;
      const d = this.done;
      this.done = null;
      d?.();
      return;
    }
    const [who, text] = line;
    const ch = CHARS[who];
    const narr = who === 'narr';
    const p = $('#portrait');
    p.textContent = ch.mark;
    p.style.background = ch.color;
    p.classList.toggle('narr', narr);
    $('#whoName').textContent = ch.name;
    $('#whoRole').textContent = ch.role;
    const el = $('#storyLine');
    el.textContent = text;
    el.classList.toggle('narr', narr);
    $('#storyProg').textContent = `${this.total - this.queue.length} / ${this.total}　タップで次へ`;
  }
}
