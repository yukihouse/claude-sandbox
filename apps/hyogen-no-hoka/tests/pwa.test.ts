import { describe, expect, it, vi } from 'vitest';
import { FONT_FACES, registerServiceWorker, uniqueChars, warmFonts } from '../src/pwa';

const nav = (register = vi.fn(() => Promise.resolve({} as ServiceWorkerRegistration))) => ({
  serviceWorker: { register },
});

describe('registerServiceWorker', () => {
  it('registers the worker for a production build served over http(s)', () => {
    for (const protocol of ['https:', 'http:']) {
      const n = nav();
      expect(registerServiceWorker(n, protocol, true)).toBe(true);
      expect(n.serviceWorker.register).toHaveBeenCalledWith('./sw.js');
    }
  });

  it('skips dev builds, files opened from disk, and browsers without support', () => {
    const n = nav();
    expect(registerServiceWorker(n, 'https:', false)).toBe(false);
    expect(registerServiceWorker(n, 'file:', true)).toBe(false);
    expect(registerServiceWorker({}, 'https:', true)).toBe(false);
    expect(n.serviceWorker.register).not.toHaveBeenCalled();
  });

  it('keeps the game running when registration fails', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const err = new Error('blocked');
    expect(registerServiceWorker(nav(vi.fn(() => Promise.reject(err))), 'https:', true)).toBe(true);
    await vi.waitFor(() => expect(warn).toHaveBeenCalledWith(expect.any(String), err));
    warn.mockRestore();
  });
});

describe('uniqueChars', () => {
  it('keeps each character once and drops whitespace', () => {
    expect(uniqueChars(['氷原の 烽火', '氷原\nの基地'])).toBe('氷原の烽火基地');
    expect(uniqueChars([])).toBe('');
  });
});

describe('warmFonts', () => {
  it('requests every face for the given text and counts the ones that loaded', async () => {
    const load = vi.fn((face: string) =>
      face.includes('800') ? Promise.reject(new Error('offline')) : Promise.resolve([] as FontFace[]),
    );
    expect(await warmFonts({ load }, '烽火')).toBe(FONT_FACES.length - 1);
    expect(load.mock.calls).toEqual(FONT_FACES.map((face) => [face, '烽火']));
  });
});
