import { describe, expect, it, vi } from 'vitest';
import { FONT_FACES, registerServiceWorker, uniqueChars, warmFonts, whenControlled } from '../src/pwa';

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
  it('fetches the stylesheet and every face for the given text, counting successes', async () => {
    const load = vi.fn((face: string) =>
      face.includes('800') ? Promise.reject(new Error('offline')) : Promise.resolve([] as FontFace[]),
    );
    const css = vi.fn(() => Promise.resolve('ok'));
    expect(await warmFonts({ load }, '烽火', css)).toBe(1 + FONT_FACES.length - 1);
    expect(css).toHaveBeenCalledOnce();
    expect(load.mock.calls).toEqual(FONT_FACES.map((face) => [face, '烽火']));
  });

  it('counts a failed stylesheet fetch as a miss', async () => {
    const load = vi.fn(() => Promise.resolve([] as FontFace[]));
    expect(await warmFonts({ load }, 'a', () => Promise.reject(new Error('offline')))).toBe(FONT_FACES.length);
  });
});

describe('whenControlled', () => {
  const container = (controller: ServiceWorker | null) => {
    const listeners: (() => void)[] = [];
    return {
      ready: Promise.resolve({} as ServiceWorkerRegistration),
      controller,
      addEventListener: vi.fn((_type: string, fn: () => void) => void listeners.push(fn)),
      fire: () => listeners.forEach((fn) => fn()),
    };
  };

  it('resolves at once when a worker already controls the page', async () => {
    const sw = container({} as ServiceWorker);
    await whenControlled(sw);
    expect(sw.addEventListener).not.toHaveBeenCalled();
  });

  it('waits for the new worker to claim the page on a first visit', async () => {
    const sw = container(null);
    let done = false;
    const p = whenControlled(sw).then(() => (done = true));
    await vi.waitFor(() => expect(sw.addEventListener).toHaveBeenCalledWith('controllerchange', expect.any(Function), { once: true }));
    expect(done).toBe(false);
    sw.fire();
    await p;
    expect(done).toBe(true);
  });
});

describe('__GAME_CHARS__', () => {
  it('holds the characters of all story lines and UI text, from the build', () => {
    for (const text of ['南極点', '隊員が足りない', '結末を見る', 'つづきから', '作戦中断', '新人越冬隊員', '大和雪原']) {
      for (const ch of text) expect(__GAME_CHARS__).toContain(ch);
    }
  });
});
