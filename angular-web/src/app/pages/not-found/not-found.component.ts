import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="container state">
      <span class="kicker">Error 404</span>
      <h1 class="article-title">This page doesn’t exist</h1>
      <p>The story may have moved or the link is wrong. Head back to today’s stories.</p>
      <a class="btn-pill" routerLink="/">Back to home</a>
    </div>
  `,
})
export class NotFoundComponent {}
