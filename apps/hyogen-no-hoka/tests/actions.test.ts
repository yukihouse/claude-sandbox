import { describe, expect, it } from 'vitest';
import { GALE_SECONDS, REINFORCE_TROOPS, WALL_SECONDS } from '../src/config';
import {
  applyItem,
  deselect,
  galeLeft,
  release,
  select,
  selectedCastle,
  sendCount,
  sendRatio,
  tapInItemMode,
  useItem,
} from '../src/game/actions';
import { castleAt } from '../src/game/rules';
import { state } from './helpers';

const setup = () =>
  state([
    [0, 0, 1, 1, 20],
    [0.3, 0, 1, 1, 10],
    [1, 0, 2, 1, 10],
  ]);

describe('selection', () => {
  it('selects, reads back and clears', () => {
    const S = setup();
    S.mode = 'wall';
    expect(selectedCastle(S)).toBeNull();
    select(S, castleAt(S, 1));
    expect(selectedCastle(S)).toBe(castleAt(S, 1));
    expect(S.mode).toBeNull();
    deselect(S);
    expect(S.selected).toBeNull();
  });
});

describe('sending', () => {
  it('sends a percentage, rounded down', () => {
    const S = setup();
    expect(sendCount(castleAt(S, 0), 55)).toBe(11);
    expect(sendRatio(S, castleAt(S, 0), castleAt(S, 2), 50)).toBe(true);
    expect(S.armies[0]?.n).toBe(10);
  });

  it('says so when there are not enough crew', () => {
    const S = setup();
    castleAt(S, 0).troops = 1.5;
    expect(sendRatio(S, castleAt(S, 0), castleAt(S, 2), 50)).toBe(false);
    expect(S.floaters).toEqual([expect.objectContaining({ text: '隊員が足りない', tone: 'ink' })]);
  });
});

describe('items', () => {
  it('ignores presses while stopped or out of stock', () => {
    const S = setup();
    S.running = false;
    useItem(S, 'gale');
    expect(S.items.gale).toBe(1);
    S.running = true;
    S.items.wall = 0;
    useItem(S, 'wall');
    expect(S.mode).toBeNull();
  });

  it('starts 雪上車 at once and stacks its time', () => {
    const S = setup();
    S.items.gale = 2;
    S.t = 3;
    useItem(S, 'gale');
    expect(S.galeUntil).toBe(3 + GALE_SECONDS);
    expect(galeLeft(S)).toBe(GALE_SECONDS);
    useItem(S, 'gale');
    expect(S.galeUntil).toBe(3 + GALE_SECONDS * 2);
    expect(S.items.gale).toBe(0);
  });

  it('waits for a target when nothing is selected, and cancels on a second press', () => {
    const S = setup();
    useItem(S, 'reinforce');
    expect(S.mode).toBe('reinforce');
    useItem(S, 'reinforce');
    expect(S.mode).toBeNull();
    expect(S.items.reinforce).toBe(1);
  });

  it('applies straight to the selected base', () => {
    const S = setup();
    select(S, castleAt(S, 1));
    useItem(S, 'reinforce');
    expect(castleAt(S, 1).troops).toBe(10 + REINFORCE_TROOPS);
    expect(S.items.reinforce).toBe(0);
    expect(S.floaters[0]).toMatchObject({ text: `+${REINFORCE_TROOPS}`, tone: 'player' });
  });

  it('raises and extends a wall', () => {
    const S = setup();
    S.items.wall = 2;
    S.t = 5;
    applyItem(S, 'wall', castleAt(S, 0));
    expect(castleAt(S, 0).wallUntil).toBe(5 + WALL_SECONDS);
    applyItem(S, 'wall', castleAt(S, 0));
    expect(castleAt(S, 0).wallUntil).toBe(5 + WALL_SECONDS * 2);
    expect(S.floaters[0]).toMatchObject({ text: '防寒壁', tone: 'player' });
  });

  it('only helps the player’s own bases, and only while in stock', () => {
    const S = setup();
    S.mode = 'wall';
    applyItem(S, 'wall', castleAt(S, 2));
    expect(castleAt(S, 2).wallUntil).toBe(0);
    expect(S.mode).toBe('wall');
    S.items.wall = 0;
    applyItem(S, 'wall', castleAt(S, 0));
    expect(castleAt(S, 0).wallUntil).toBe(0);
  });

  it('uses a waiting item on the tapped base, or cancels it', () => {
    const S = setup();
    S.mode = 'reinforce';
    tapInItemMode(S, 'reinforce', castleAt(S, 2));
    expect(S.mode).toBeNull();
    S.mode = 'reinforce';
    tapInItemMode(S, 'reinforce', null);
    expect(S.mode).toBeNull();
    S.mode = 'reinforce';
    tapInItemMode(S, 'reinforce', castleAt(S, 0));
    expect(castleAt(S, 0).troops).toBe(20 + REINFORCE_TROOPS);
    expect(S.mode).toBeNull();
  });
});

describe('release', () => {
  it('sends along a drag and clears the selection', () => {
    const S = setup();
    S.selected = 1;
    release(S, castleAt(S, 0), castleAt(S, 2), 50);
    expect(S.armies[0]).toMatchObject({ n: 10, to: 2 });
    expect(S.selected).toBeNull();
  });

  it('does not send a drag dropped on its start, on nothing, or from a lost base', () => {
    const S = setup();
    release(S, castleAt(S, 0), castleAt(S, 0), 50);
    release(S, castleAt(S, 0), null, 50);
    castleAt(S, 1).owner = 2;
    release(S, castleAt(S, 1), castleAt(S, 2), 50);
    expect(S.armies).toEqual([]);
  });

  it('taps: select own base, then tap a target to send', () => {
    const S = setup();
    release(S, null, castleAt(S, 2), 50);
    expect(S.selected).toBeNull();
    release(S, null, castleAt(S, 0), 50);
    expect(S.selected).toBe(0);
    release(S, null, castleAt(S, 2), 50);
    expect(S.armies[0]).toMatchObject({ owner: 1, n: 10, to: 2 });
    expect(S.selected).toBeNull();
  });

  it('taps: the selected base again, or empty ground, deselects', () => {
    const S = setup();
    S.selected = 0;
    castleAt(S, 0).troops = 1;
    release(S, null, castleAt(S, 0), 50);
    expect(S.selected).toBeNull();
    expect(S.floaters).toEqual([]);
    S.selected = 0;
    release(S, null, null, 50);
    expect(S.selected).toBeNull();
  });

  it('taps: moves the selection off a base the player no longer owns', () => {
    const S = setup();
    S.selected = 1;
    castleAt(S, 1).owner = 2;
    release(S, null, castleAt(S, 0), 50);
    expect(S.selected).toBe(0);
    expect(S.armies).toEqual([]);
  });
});
