/* =============================================================================
   data-loader.js — fetches /data/daily.json and renders the homepage cards.
   Falls back silently to the SSR HTML if the file is missing or malformed,
   so the page never breaks during deployments.
   ============================================================================= */

(() => {
  'use strict';

  const DATA_URL = '/data/daily.json';

  // Escape helper for safe insertion into innerHTML.
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
    c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));

  // Relative-time formatter (Today / X hours ago / Mon)
  const relTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 3600)    return `${Math.max(1, Math.round(diff / 60))} min ago`;
    if (diff < 86400)   return `${Math.round(diff / 3600)}h ago`;
    if (diff < 604800)  return `${Math.round(diff / 86400)}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  // -------------------- Renderers --------------------

  function renderFeatured(a) {
    if (!a) return '';
    return `
      <div class="featured-card__media" aria-hidden="true">
        <div class="featured-card__media-grad" style="background:
          radial-gradient(circle at 30% 30%, ${esc(a.thumbnail?.c1 || '#00d4ff')}99, transparent 55%),
          radial-gradient(circle at 70% 70%, ${esc(a.thumbnail?.c2 || '#7c5cff')}aa, transparent 55%),
          linear-gradient(135deg, #0e1018, #1a1d2e)"></div>
        <span class="chip chip--accent">Featured</span>
      </div>
      <div class="featured-card__body">
        <div class="meta">
          <span class="chip">${esc(a.category)}</span>
          <span class="meta__sep" aria-hidden="true">·</span>
          <time datetime="${esc(a.published_at)}">${relTime(a.published_at)}</time>
          <span class="meta__sep" aria-hidden="true">·</span>
          <span>${esc(a.reading_time_min || 5)} min read</span>
        </div>
        <h2 class="featured-card__title">${esc(a.title)}</h2>
        <p class="featured-card__excerpt">${esc(a.tldr || a.excerpt || '')}</p>
        <a href="${esc(a.permalink)}" class="link-arrow">Read full briefing
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        </a>
      </div>
    `;
  }

  function renderCard(a) {
    return `
      <article class="card" data-reveal>
        <a href="${esc(a.permalink)}" class="card__link" aria-label="Read article">
          <div class="card__media">
            <div class="card__thumb" style="--c1:${esc(a.thumbnail?.c1 || '#00d4ff')};--c2:${esc(a.thumbnail?.c2 || '#7c5cff')}"></div>
            <span class="chip card__chip">${esc(a.category)}</span>
          </div>
          <div class="card__body">
            <h3 class="card__title">${esc(a.title)}</h3>
            <p class="card__excerpt">${esc(a.excerpt || a.tldr || '')}</p>
            <div class="meta">
              <time datetime="${esc(a.published_at)}">${relTime(a.published_at)}</time>
              <span class="meta__sep">·</span>
              <span>${esc(a.reading_time_min || 4)} min read</span>
            </div>
          </div>
        </a>
      </article>
    `;
  }

  function renderRepo(r) {
    const release = r.is_release ? 'chip--success' : '';
    return `
      <article class="repo" data-reveal>
        <div class="repo__top">
          <a class="repo__name" href="${esc(r.url)}" target="_blank" rel="noopener">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 1 18 0 9 9 0 0 1-18 0z"/></svg>
            <span>${esc(r.repo.split('/')[0])}/<b>${esc(r.repo.split('/').slice(1).join('/'))}</b></span>
          </a>
          ${r.latest_release ? `<span class="chip ${release}">${esc(r.latest_release)}${r.is_release ? ' release' : ''}</span>` : ''}
        </div>
        <p class="repo__desc">${esc(r.description || '')}</p>
        <div class="repo__meta">
          ${r.language ? `<span class="lang"><span class="lang__dot" style="background:${esc(r.language_color || '#7c5cff')}"></span>${esc(r.language)}</span>` : ''}
          ${r.stars_total ? `<span class="repo__stat">★ ${formatStars(r.stars_total)}</span>` : ''}
          ${r.stars_today ? `<span class="repo__stat repo__stat--accent">+${r.stars_today} today</span>` : ''}
        </div>
      </article>
    `;
  }

  function formatStars(n) {
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
    return String(n);
  }

  function renderCategory(c) {
    return `
      <a href="/categories/${esc(c.slug)}" class="cat" data-reveal style="--cat-c1:${esc(c.color_from || '#7c5cff')};--cat-c2:${esc(c.color_to || '#00d4ff')}">
        <span class="cat__icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg>
        </span>
        <h3>${esc(c.name)}</h3>
        <p>${esc(c.description || '')}</p>
        ${typeof c.article_count_today === 'number'
          ? `<span class="chip" style="margin-top:0.5rem">${c.article_count_today} today</span>` : ''}
      </a>
    `;
  }

  function renderStats(stats) {
    if (!stats) return '';
    return `
      <div class="stat"><span class="stat__num">${formatStars(stats.articles_published_total || 0).replace('.0','')}</span><span class="stat__label">Articles published</span></div>
      <div class="stat"><span class="stat__num">${stats.sources_monitored || 50}</span><span class="stat__label">Sources monitored</span></div>
      <div class="stat"><span class="stat__num">${esc(stats.daily_update_time || '08:00')}</span><span class="stat__label">Daily update</span></div>
      <div class="stat"><span class="stat__num">${stats.automation_percent || 100}%</span><span class="stat__label">AI-generated</span></div>
    `;
  }

  function renderCommunityPulse(pulse) {
    if (!pulse || !pulse.best_takes || !pulse.best_takes.length) return '';
    const items = pulse.best_takes.slice(0, 4).map(t => `
      <blockquote class="take">
        <p>${esc(t.quote)}</p>
        <footer>
          <span class="take__src">${esc(t.source || '')}${t.subreddit_or_handle ? ' · ' + esc(t.subreddit_or_handle) : ''}</span>
          ${t.engagement ? `<span class="take__eng">${esc(t.engagement)}</span>` : ''}
          ${t.url ? `<a href="${esc(t.url)}" target="_blank" rel="noopener">View →</a>` : ''}
        </footer>
      </blockquote>
    `).join('');
    return `
      <section class="section container community-pulse">
        <header class="section__header">
          <div>
            <span class="eyebrow">Community pulse</span>
            <h2 class="section__title">What people are actually saying</h2>
          </div>
        </header>
        <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr))">${items}</div>
      </section>
    `;
  }

  // -------------------- Boot --------------------

  async function load() {
    try {
      const res = await fetch(DATA_URL, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('[data-loader] daily.json not loaded; keeping SSR HTML.', err);
      return null;
    }
  }

  function hydrate(data) {
    if (!data) return;

    // Featured
    const featured = document.querySelector('[data-slot="featured"]');
    if (featured && data.featured) featured.innerHTML = renderFeatured(data.featured);

    // Latest grid
    const latest = document.querySelector('[data-slot="latest"]');
    if (latest && Array.isArray(data.latest)) {
      latest.innerHTML = data.latest.map(renderCard).join('');
    }

    // GitHub
    const gh = document.querySelector('[data-slot="github"]');
    if (gh && Array.isArray(data.github_trending)) {
      gh.innerHTML = data.github_trending.map(renderRepo).join('');
    }

    // Categories
    const cats = document.querySelector('[data-slot="categories"]');
    if (cats && Array.isArray(data.categories)) {
      cats.innerHTML = data.categories.map(renderCategory).join('');
    }

    // Stats
    const stats = document.querySelector('[data-slot="stats"]');
    if (stats && data.stats) stats.innerHTML = renderStats(data.stats);

    // Community Pulse (optional — only renders if data exists)
    const pulse = document.querySelector('[data-slot="community-pulse"]');
    if (pulse && data.community_pulse) {
      pulse.innerHTML = renderCommunityPulse(data.community_pulse);
    }

    // Replay reveal observer for the newly-injected nodes
    if (window.__reapplyReveal) window.__reapplyReveal();

    // Set "generated at" footer line
    const ga = document.querySelector('[data-slot="generated-at"]');
    if (ga && data.generated_at) {
      ga.textContent = `Updated ${new Date(data.generated_at).toLocaleString()}`;
    }
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => load().then(hydrate));
  } else {
    load().then(hydrate);
  }
})();
