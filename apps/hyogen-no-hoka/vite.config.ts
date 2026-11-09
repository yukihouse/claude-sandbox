import { defineConfig } from 'vitest/config';
import { viteSingleFile } from 'vite-plugin-singlefile';

// The build inlines all JS and CSS into dist/index.html, so the game still
// runs by opening one file in a browser (file:// included), as before.
export default defineConfig({
  plugins: [viteSingleFile()],
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      // Game rules, data, save and view math are covered to 100%.
      // Canvas drawing and DOM wiring (render/draw, render/terrain, ui/, main)
      // are checked by playing the built game in a browser instead.
      include: ['src/game/**', 'src/data/**', 'src/save.ts', 'src/render/view.ts'],
      reporter: ['text'],
      thresholds: { 100: true },
    },
  },
});
