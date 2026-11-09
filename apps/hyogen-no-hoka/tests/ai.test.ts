import { describe, expect, it } from 'vitest';
import { aiThink } from '../src/game/ai';
import { castleAt } from '../src/game/rules';
import { state } from './helpers';

describe('aiThink', () => {
  it('does nothing for a faction with no bases', () => {
    const S = state([[0, 0, 1, 1, 10]]);
    aiThink(S, 2);
    expect(S.armies).toEqual([]);
  });

  describe('1. defend', () => {
    it('sends the nearest strong base to a base about to fall', () => {
      const S = state([
        [1, 0, 2, 1, 5],
        [1.4, 0, 2, 1, 30], // farther helper
        [1.2, 0, 2, 1, 30], // nearest helper
        [1.05, 0, 2, 1, 12], // close but too weak to help
        [0, 0, 1, 1, 10],
      ]);
      S.armies = [
        { owner: 1, n: 20, to: 0, x: 0.5, y: 0 },
        { owner: 2, n: 3, to: 0, x: 1.1, y: 0 },
      ];
      aiThink(S, 2);
      // shortfall 20 - 3 - 5 = 12 → min(30 - 4, 12 + 6) = 18
      expect(S.armies[2]).toMatchObject({ owner: 2, n: 18, to: 0 });
      expect(castleAt(S, 2).troops).toBe(12);
      expect(castleAt(S, 1).troops).toBe(30);
    });

    it('counts the wall when judging the danger', () => {
      const S = state([
        [1, 0, 2, 1, 10],
        [1.2, 0, 2, 1, 5],
        [0, 0, 1, 1, 1],
      ]);
      S.armies = [{ owner: 1, n: 15, to: 0, x: 0.5, y: 0 }];
      castleAt(S, 0).wallUntil = 99;
      aiThink(S, 2);
      // 15 vs 10×2: safe, no helper strong enough elsewhere, nothing to attack
      expect(S.armies).toHaveLength(1);
    });

    it('gives up when the only helper is too far away', () => {
      const S = state([
        [0.2, 0, 2, 1, 5],
        [1.0, 0, 2, 1, 13],
        [0, 0, 1, 3, 90],
      ]);
      S.armies = [{ owner: 1, n: 40, to: 0, x: 0.1, y: 0 }];
      aiThink(S, 2);
      expect(S.armies).toHaveLength(1);
    });
  });

  describe('2. attack', () => {
    it('picks the best-value target it can take', () => {
      const S = state([
        [1, 0.5, 2, 1, 30],
        [0.8, 0.5, 0, 1, 5], // close neutral: best
        [1.3, 0.1, 0, 1, 6], // farther neutral: worse score
        [0, 0.5, 1, 2, 40], // player: too strong
        [1.5, 0.9, 2, 1, 4], // AI base with too few troops to attack
      ]);
      aiThink(S, 2);
      // reserve 9 → 21 available; need ceil(5 × 1.2) + 3 = 9
      expect(S.armies).toEqual([expect.objectContaining({ owner: 2, n: 9, to: 1 })]);
    });

    it('values the player by focus and rivals above neutrals', () => {
      const castles = [
        [1, 0.5, 2, 1, 30],
        [0.8, 0.5, 1, 1, 2],
        [1.2, 0.5, 3, 1, 2],
        [1, 0.3, 0, 1, 2],
      ] as const;
      const focused = state([...castles], { ai: { interval: 4, greed: 1.2, focus: 2 } });
      aiThink(focused, 2);
      expect(focused.armies[0]?.to).toBe(1);

      const calm = state([...castles], { ai: { interval: 4, greed: 1.2, focus: 0 } });
      aiThink(calm, 2);
      expect(calm.armies[0]?.to).toBe(2);
    });

    it('skips targets already being taken by its own armies', () => {
      const S = state([
        [1, 0.5, 2, 1, 30],
        [0.9, 0.5, 0, 1, 5],
        [0.5, 0.5, 0, 1, 8],
      ]);
      S.armies = [{ owner: 2, n: 20, to: 1, x: 0.95, y: 0.5 }];
      aiThink(S, 2);
      expect(S.armies[1]).toMatchObject({ owner: 2, to: 2 });
    });

    it('expects enemy bases to grow and armies to reinforce them on the way', () => {
      const S = state([
        [1, 0.5, 2, 1, 20],
        [0.8, 0.5, 1, 1, 1],
      ]);
      S.armies = [{ owner: 1, n: 3, to: 1, x: 0.5, y: 0.5 }];
      aiThink(S, 2);
      // est = 1 + 0.8 × (0.2 / 0.11) + 3 ≈ 5.45 → ceil(6.55) + 3 = 10
      expect(S.armies[1]).toMatchObject({ owner: 2, n: 10, to: 1 });
    });
  });

  describe('3. move to the front', () => {
    const front = (rearTroops: number) =>
      state([
        [1.0, 0.5, 2, 1, 2], // frontline
        [1.4, 0.5, 2, 1, rearTroops], // rear
        [0.2, 0.5, 1, 3, 90],
      ]);

    it('moves a full rear base towards the enemy', () => {
      const S = front(30);
      aiThink(S, 2);
      expect(S.armies).toEqual([expect.objectContaining({ owner: 2, n: 18, to: 0 })]);
    });

    it('keeps a rear base that is still filling up', () => {
      const S = front(20);
      aiThink(S, 2);
      expect(S.armies).toEqual([]);
    });

    it('needs both an enemy and two bases', () => {
      const onlyNeutrals = state([
        [1.0, 0.5, 2, 1, 2],
        [1.4, 0.5, 2, 1, 30],
        [0.2, 0.5, 0, 3, 90],
      ]);
      aiThink(onlyNeutrals, 2);
      expect(onlyNeutrals.armies).toEqual([]);

      const single = state([
        [1.4, 0.5, 2, 1, 30],
        [0.2, 0.5, 1, 3, 90],
      ]);
      aiThink(single, 2);
      expect(single.armies).toEqual([]);
    });
  });
});
