import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SeoService } from '../../services/seo.service';

/**
 * Methodology page.
 *
 * Every story here is written by a language model, so saying so plainly —
 * along with where the material comes from and what is checked automatically —
 * is the honest baseline for a news site. Content is static prose, so it lives
 * in the template rather than in the article JSON pipeline.
 */
@Component({
  selector: 'app-about',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="container prose-page">
      <span class="kicker" style="margin-top:8px;display:inline-block">About</span>
      <h1 class="article-title">How TechPulse is made</h1>
      <p class="article-dek">
        An automated daily brief on AI and developer news. Here is exactly
        where the stories come from, how they are written, and what we check
        before anything is published.
      </p>

      <div class="prose">
        <h2>What this is</h2>
        <p>
          TechPulse publishes a short digest of the most consequential AI,
          programming, and open-source news from the previous 24 hours. It
          refreshes every morning at 8:00 AM Malaysia time (MYT). Between five
          and eight stories are kept each day.
        </p>

        <h2>Where the stories come from</h2>
        <p>
          Every cycle pulls from a fixed set of primary and community sources
          rather than the open web:
        </p>
        <ul>
          <li><strong>Hacker News</strong> — the day's top stories, used as a signal of what developers are actually discussing.</li>
          <li><strong>GitHub</strong> — the trending page, plus releases for Angular, React, Vue, CPython, Node.js, TypeScript, Next.js, Svelte, Bun, and Deno.</li>
          <li>
            <strong>Official vendor and project feeds</strong> — the Angular,
            React, Python, Node.js, OpenAI, Google AI, Hugging Face, and
            Anthropic blogs, plus TechCrunch.
          </li>
        </ul>
        <p>
          Stories older than 24 hours are dropped. Duplicates covering the same
          underlying event are collapsed in favour of the most authoritative
          source. Cosmetic patch bumps, rumour pieces, listicles, and paywalled
          press releases are filtered out.
        </p>

        <h2>How articles are written</h2>
        <p>
          Articles are written by a large language model (Claude) from the
          fetched source material, then rendered into this site by a static
          build. There is no human author behind any byline, and no story is
          hand-edited before it goes live. Each article links its sources at the
          top and bottom of the page — those links, not this summary, are the
          authority for any claim.
        </p>

        <h2>What is checked automatically</h2>
        <p>
          Two gates run before anything deploys:
        </p>
        <ul>
          <li>
            <strong>Schema validation</strong> — every article must match a
            fixed JSON schema (required fields, category from a closed list, at
            least one source) or the build stops.
          </li>
          <li>
            <strong>Source-link verification</strong> — every cited URL is
            fetched and must resolve. Links that return 404, or whose domain
            does not exist, fail the build. This is the check that catches an
            invented citation.
          </li>
        </ul>

        <h2>What is not checked</h2>
        <p>
          These gates prove that an article is well-formed and that its sources
          are real and reachable. They do not prove the article's claims are
          true. Model-written summaries can misread a source, overstate a
          result, or garble a detail — and nothing here catches that
          automatically. Treat TechPulse as a pointer to primary sources, not as
          a replacement for them. If a story matters to you, follow its links.
        </p>

        <h2>Corrections</h2>
        <p>
          Articles are regenerated from source data, so a correction is made by
          fixing the underlying article and rebuilding. If you find an error,
          open an issue on the
          <a
            href="https://github.com/boon-boon/Daily-AI-Tech-News-Blog-Automation"
            target="_blank"
            rel="noopener"
            >project repository</a
          >.
        </p>

        <h2>Following along</h2>
        <p>
          Every story ever published is in the
          <a routerLink="/archive">archive</a>, which is searchable by headline,
          topic, and tag. There is also an
          <a href="feed.xml" target="_blank" rel="noopener">RSS feed</a>.
        </p>
      </div>
    </div>
  `,
})
export class AboutComponent implements OnInit {
  private readonly seo = inject(SeoService);

  ngOnInit(): void {
    this.seo.clearJsonLd();
    this.seo.setTags({
      title: 'How TechPulse is made — TechPulse Daily',
      description:
        'Where TechPulse stories come from, how they are written, and what is verified before publishing.',
      type: 'website',
    });
  }
}
