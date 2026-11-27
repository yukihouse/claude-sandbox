import { defineConfig } from 'vitest/config';
import { viteSingleFile } from 'vite-plugin-singlefile';

// The build inlines all JS and CSS into dist/index.html, so the game runs by
// opening one file in a browser (file:// included).
export default defineConfig({
  base: './',
  plugins: [viteSingleFile()],
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      // Game rules, data and save are covered to 100%. Canvas drawing and DOM
      // wiring (render/, main.ts) are checked by playing the built game instead.
      include: ['src/game/**', 'src/data/**', 'src/save.ts'],
      reporter: ['text'],
      thresholds: { 100: true },
    },
  },
});
