import { defineConfig } from 'vitest/config';
import { viteSingleFile } from 'vite-plugin-singlefile';

// The build inlines all JS and CSS into dist/index.html, so the game still
// runs by opening one file in a browser (file:// included), as before.
export default defineConfig({
  // Relative URLs, so the build works from any path (GitHub Pages serves it
  // under /<repo>/) and still opens from disk.
  base: './',
  plugins: [viteSingleFile()],
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      // Game rules, data, save and view math are covered to 100%.
      // Canvas drawing and DOM wiring (render/draw, render/terrain, ui/, main)
      // are checked by playing the built game in a browser instead.
      include: ['src/game/**', 'src/data/**', 'src/save.ts', 'src/render/view.ts', 'src/pwa.ts'],
      reporter: ['text'],
      thresholds: { 100: true },
    },
  },
});
