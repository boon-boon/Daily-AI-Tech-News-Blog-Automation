import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ThemeService } from './services/theme.service';

/**
 * Root shell: sticky header, routed content, and footer.
 * Kept template-inline since the markup is small and self-contained.
 */
@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <a class="skip-link" href="#main">Skip to content</a>

    <header class="site-header">
      <div class="container header-inner">
        <a routerLink="/" class="brand" aria-label="TechPulse home">TechPulse<span class="brand-dot">.</span></a>

        <nav class="primary-nav" aria-label="Primary">
          <a routerLink="/" routerLinkActive="active"
             [routerLinkActiveOptions]="{ exact: true }">Today</a>
          <a routerLink="/category/ai-ml" routerLinkActive="active">AI &amp; ML</a>
          <a routerLink="/category/developer-tools" routerLinkActive="active">Developer Tools</a>
          <a routerLink="/category/cloud" routerLinkActive="active">Cloud &amp; Infra</a>
          <a routerLink="/category/open-source" routerLinkActive="active">Open Source</a>
          <a routerLink="/archive" routerLinkActive="active" class="nav-search">
            <span aria-hidden="true">⌕</span> Search
          </a>
        </nav>

        <button
          type="button"
          class="theme-toggle"
          (click)="theme.cycle()"
          [attr.aria-label]="'Theme: ' + theme.preference() + '. Change theme.'"
          [title]="'Theme: ' + theme.preference()"
        >
          <span aria-hidden="true">{{ themeIcon() }}</span>
        </button>
      </div>
    </header>

    <main id="main" class="site-main">
      <router-outlet />
    </main>

    <footer class="site-footer">
      <div class="container">
        <p class="footer-brand">TechPulse<span class="brand-dot">.</span></p>
        <p class="footer-note">
          A daily digest of AI and developer news, refreshed every morning at
          8:00 AM Malaysia time. Stories are written and SEO-tuned by an LLM
          pipeline from official sources.
        </p>
        <nav class="footer-links" aria-label="Footer">
          <a routerLink="/">Today</a>
          <a routerLink="/archive">Archive</a>
          <a routerLink="/about">How it's made</a>
          <a href="feed.xml" target="_blank" rel="noopener">RSS</a>
        </nav>
        <p class="footer-meta">© {{ year }} TechPulse</p>
      </div>
    </footer>
  `,
})
export class App {
  protected readonly year = new Date().getFullYear();
  protected readonly theme = inject(ThemeService);

  protected themeIcon(): string {
    return { system: '◐', light: '☀', dark: '☾' }[this.theme.preference()];
  }
}
