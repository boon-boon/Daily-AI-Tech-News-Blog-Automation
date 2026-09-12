import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export type ThemePreference = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'techpulse-theme';

/**
 * Light/dark theme preference.
 *
 * 'system' is the default and stamps no attribute, letting the
 * prefers-color-scheme media query in styles.css decide. An explicit choice
 * stamps data-theme on <html>, which overrides that query in both directions.
 *
 * The initial attribute is applied by an inline script in index.html so the
 * page never flashes the wrong theme; this service keeps it in sync afterwards.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly isBrowser = isPlatformBrowser(this.platformId);

  readonly preference = signal<ThemePreference>(this.read());

  /** Cycles system → light → dark → system. */
  cycle(): void {
    const next: Record<ThemePreference, ThemePreference> = {
      system: 'light',
      light: 'dark',
      dark: 'system',
    };
    this.set(next[this.preference()]);
  }

  set(pref: ThemePreference): void {
    this.preference.set(pref);
    if (!this.isBrowser) return;

    const root = document.documentElement;
    if (pref === 'system') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', pref);
    }

    try {
      if (pref === 'system') localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, pref);
    } catch {
      // Storage can be unavailable (private mode); the in-page theme still applies.
    }
  }

  private read(): ThemePreference {
    if (!this.isBrowser) return 'system';
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'light' || stored === 'dark') return stored;
    } catch {
      // ignore
    }
    return 'system';
  }
}
