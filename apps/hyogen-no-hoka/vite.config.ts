import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { defineConfig } from 'vitest/config';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { uniqueChars } from './src/pwa';

// Every character that can appear on screen comes from the source or index.html.
// The game preloads font pieces for all of them so text keeps its font offline.
const sources = ['index.html', ...readdirSync('src', { recursive: true, encoding: 'utf8' }).map((f) => join('src', f))]
  .filter((f) => /\.(ts|html)$/.test(f))
  .map((f) => readFileSync(f, 'utf8'));

// The build inlines all JS and CSS into dist/index.html, so the game still
// runs by opening one file in a browser (file:// included), as before.
export default defineConfig({
  // Relative URLs, so the build works from any path (GitHub Pages serves it
  // under /<repo>/) and still opens from disk.
  base: './',
  define: { __GAME_CHARS__: JSON.stringify(uniqueChars(sources)) },
  plugins: [viteSingleFile()],
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      // Game rules, data, save, view math and PWA helpers are covered to 100%.
      // Canvas drawing, DOM wiring (render/draw, render/terrain, ui/, main) and
      // public/sw.js are checked by playing the built game in a browser instead.
      include: ['src/game/**', 'src/data/**', 'src/save.ts', 'src/render/view.ts', 'src/pwa.ts'],
      reporter: ['text'],
      thresholds: { 100: true },
    },
  },
});
