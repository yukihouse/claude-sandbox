/**
 * Register the Service Worker that makes the game installable and playable
 * offline. Skipped in development (`npm run dev`) and when the built file is
 * opened straight from disk (file://), where Service Workers do not run.
 */
export function registerServiceWorker(
  nav: { serviceWorker?: Pick<ServiceWorkerContainer, 'register'> },
  protocol: string,
  isProd: boolean,
  url = './sw.js',
): boolean {
  if (!isProd || !nav.serviceWorker || !['https:', 'http:'].includes(protocol)) return false;
  nav.serviceWorker.register(url).catch((err: unknown) => {
    console.warn('Service Worker registration failed; the game still works online.', err);
  });
  return true;
}

/** The web-font faces the game uses (see index.html and style.css). */
export const FONT_FACES = [
  '700 16px "Shippori Mincho B1"',
  '800 16px "Shippori Mincho B1"',
  '400 16px "Zen Kaku Gothic New"',
  '700 16px "Zen Kaku Gothic New"',
] as const;

/** Every distinct character in `texts`, as one string. */
export const uniqueChars = (texts: Iterable<string>): string =>
  [...new Set([...texts].join('').replace(/\s/g, ''))].join('');

/**
 * Ask the browser for the font files covering all of the game's text, so the
 * Service Worker caches them while online. Google serves Japanese fonts in
 * many small pieces and the browser normally only fetches the ones on screen;
 * without this, later chapters would fall back to the system font offline.
 * Returns how many faces loaded; failures (e.g. offline) are ignored.
 */
export async function warmFonts(fonts: Pick<FontFaceSet, 'load'>, text: string): Promise<number> {
  const results = await Promise.allSettled(FONT_FACES.map((face) => fonts.load(face, text)));
  return results.filter((r) => r.status === 'fulfilled').length;
}
