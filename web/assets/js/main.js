/* =============================================================================
   Daily Tech Pulse — main.js
   Vanilla, no dependencies. Lazy-friendly. Respects prefers-reduced-motion.
   ============================================================================= */

(() => {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------------------------------------------------------------------------
  // 1. Footer year
  // ---------------------------------------------------------------------------
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // ---------------------------------------------------------------------------
  // 2. Mobile nav toggle
  // ---------------------------------------------------------------------------
  const toggle = document.querySelector('.nav__toggle');
  const drawer = document.getElementById('mobile-menu');
  if (toggle && drawer) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      if (open) {
        drawer.hidden = true;
      } else {
        drawer.hidden = false;
        drawer.querySelector('a, button')?.focus({ preventScroll: true });
      }
    });
    // Close on link click (single-page anchors)
    drawer.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        toggle.setAttribute('aria-expanded', 'false');
        drawer.hidden = true;
      });
    });
    // Close on Esc
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && !drawer.hidden) {
        toggle.setAttribute('aria-expanded', 'false');
        drawer.hidden = true;
        toggle.focus();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 3. Reveal on scroll (IntersectionObserver, staggered per section)
  // ---------------------------------------------------------------------------
  const revealEls = document.querySelectorAll('[data-reveal]');
  if (revealEls.length && 'IntersectionObserver' in window && !reducedMotion) {
    const io = new IntersectionObserver(
      entries => {
        entries.forEach((entry, i) => {
          if (entry.isIntersecting) {
            // Stagger items in the same observer batch
            entry.target.style.transitionDelay = `${Math.min(i, 6) * 60}ms`;
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.05 }
    );
    revealEls.forEach(el => io.observe(el));
  } else {
    // Fallback: just show everything
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  // ---------------------------------------------------------------------------
  // 4. Filter tabs (visual-only client side; backend hooks up real data)
  // ---------------------------------------------------------------------------
  const filters = document.querySelectorAll('.filter');
  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      filters.forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      // Hook for future: dispatch a custom event so a data layer can re-render
      document.dispatchEvent(
        new CustomEvent('tp:filter', { detail: { value: btn.textContent.trim() } })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // 5. Magnetic primary CTA (subtle cursor-follow translate)
  // ---------------------------------------------------------------------------
  if (!reducedMotion && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.btn--primary.btn--lg').forEach(btn => {
      const STR = 8; // max translate in px
      btn.addEventListener('pointermove', e => {
        const r = btn.getBoundingClientRect();
        const dx = ((e.clientX - r.left) / r.width  - 0.5) * 2;
        const dy = ((e.clientY - r.top)  / r.height - 0.5) * 2;
        btn.style.transform = `translate(${dx * STR}px, ${dy * STR - 1}px)`;
      });
      btn.addEventListener('pointerleave', () => { btn.style.transform = ''; });
    });
  }

  // ---------------------------------------------------------------------------
  // 6. Newsletter form (placeholder — wire to your backend)
  // ---------------------------------------------------------------------------
  const form = document.querySelector('.newsletter__form');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      const btn   = form.querySelector('button[type="submit"]');
      if (!input.value || !input.checkValidity()) {
        input.focus();
        input.style.outline = '2px solid #ef4444';
        return;
      }
      input.style.outline = '';
      btn.textContent = 'Subscribed ✓';
      btn.disabled = true;
      input.value = '';
      // TODO: POST to your provider, e.g. Mailchimp / Buttondown / ConvertKit
      setTimeout(() => { btn.disabled = false; btn.textContent = 'Subscribe'; }, 4000);
    });
  }

  // ---------------------------------------------------------------------------
  // 7. Sticky-nav shadow on scroll
  // ---------------------------------------------------------------------------
  const navWrap = document.querySelector('.nav-wrap');
  if (navWrap) {
    let scrolled = false;
    const onScroll = () => {
      const isScrolled = window.scrollY > 12;
      if (isScrolled !== scrolled) {
        scrolled = isScrolled;
        navWrap.style.background = isScrolled
          ? 'linear-gradient(to bottom, rgba(6,7,11,0.95), rgba(6,7,11,0.7))'
          : 'linear-gradient(to bottom, rgba(6,7,11,0.8), rgba(6,7,11,0))';
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
  }
})();
