import katex from 'katex';
import { memo } from 'react';

const escapeHtml = (s) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function renderTex(tex, displayMode = false) {
  return katex.renderToString(tex, { displayMode, throwOnError: false, strict: 'ignore' });
}

// Plain text with **bold** and $inline math$ → HTML
function renderInline(text) {
  return text
    .split(/(\$[^$]+\$)/g)
    .map((part) => {
      if (part.length > 2 && part.startsWith('$') && part.endsWith('$')) return renderTex(part.slice(1, -1));
      return escapeHtml(part).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    })
    .join('');
}

export const MathText = memo(function MathText({ text, as: Tag = 'span', className }) {
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: renderInline(text || '') }} />;
});

export const MathBlock = memo(function MathBlock({ tex, className = 'math-block' }) {
  if (!tex) return null;
  return <div className={className} dangerouslySetInnerHTML={{ __html: renderTex(tex, true) }} />;
});
