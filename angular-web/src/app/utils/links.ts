/**
 * Helpers for translating the Python backend's permalink strings
 * (e.g. "/posts/2026-06-11/claude-fable-5-launch.html") into Angular
 * router commands (["/posts", "2026-06-11", "claude-fable-5-launch"]).
 */
export function permalinkToRoute(permalink: string): string[] {
  const clean = permalink.replace(/\.html?$/i, '').replace(/^\/+/, '');
  const parts = clean.split('/').filter(Boolean);
  return ['/', ...parts].length ? ['/' + parts.join('/')] : ['/'];
}

/** Returns ["/posts", date, slug] from a permalink, for routerLink arrays. */
export function permalinkToCommands(permalink: string): string[] {
  const clean = permalink.replace(/\.html?$/i, '').replace(/^\/+/, '');
  return clean.split('/').filter(Boolean).map((p, i) => (i === 0 ? '/' + p : p));
}
