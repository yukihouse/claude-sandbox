import { describe, expect, it } from 'vitest';
import { newGame } from '../src/game/rules';
import { autoplay } from './helpers';

// Plays 40 games with a simple, never-changing strategy (tests/helpers.ts).
// A thoughtful player should do better; this guards against the game becoming
// unwinnable, trivially easy, or far too long after a numbers change.
describe('balance', () => {
  const games = Array.from({ length: 40 }, (_, i) => autoplay(newGame(i + 1), 1200));
  const wins = games.filter((s) => s.over === 'win');

  it('a simple strategy wins some games and loses others', () => {
    expect(wins.length).toBeGreaterThanOrEqual(8);
    expect(wins.length).toBeLessThanOrEqual(32);
  });

  it('a win takes decades of seasons, not forever', () => {
    const avg = wins.reduce((a, s) => a + s.turn, 0) / wins.length;
    expect(avg).toBeGreaterThan(80);
    expect(avg).toBeLessThan(300);
  });

  it('every game ends one way or the other', () => {
    expect(games.every((s) => s.over !== null)).toBe(true);
  });
});
