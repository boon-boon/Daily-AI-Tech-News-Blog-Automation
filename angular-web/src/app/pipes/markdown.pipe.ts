import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

/**
 * Renders Markdown (the article body_markdown) to sanitized HTML.
 *
 * Content originates from the trusted Python/LLM pipeline, but we still pass it
 * through Angular's DomSanitizer. We bypass only because marked output is HTML
 * we generated ourselves; if you ingest third-party Markdown, swap in a
 * sanitizer such as DOMPurify before trusting it.
 */
@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  private readonly sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';
    const html = marked.parse(value, { async: false, gfm: true }) as string;
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
