/* Keep the directory compact on phones without hiding it when JS is disabled. */
(() => {
  const tree = document.querySelector('.guide-tree');
  const narrow = matchMedia('(max-width: 760px)');
  const update = () => { if (tree) tree.open = !narrow.matches; };
  update();
  narrow.addEventListener('change', update);
})();

(() => {
  const article = document.querySelector('.guide-article-layout > article');
  const headings = article?.querySelectorAll('h2[id], h3[id]');
  if (!headings || headings.length < 2) return;

  const nav = document.createElement('nav');
  nav.className = 'guide-toc';
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  const label = article.lang === 'en' ? 'On this page' : 'Bu sayfada';
  nav.setAttribute('aria-label', label);
  summary.textContent = label;
  const list = document.createElement('ul');
  let parent;
  for (const heading of headings) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${encodeURIComponent(heading.id)}`;
    link.textContent = heading.textContent.trim();
    item.append(link);
    if (heading.tagName === 'H3' && parent) {
      const children = parent.querySelector('ul') || parent.appendChild(document.createElement('ul'));
      children.append(item);
    } else {
      list.append(item);
      parent = heading.tagName === 'H2' ? item : null;
    }
  }
  details.append(summary, list);
  nav.append(details);

  const wide = matchMedia('(min-width: 1280px)');
  const medium = matchMedia('(min-width: 760px)');
  const title = article.querySelector('h1');
  const placeToc = () => {
    details.open = medium.matches;
    if (wide.matches) article.after(nav);
    else if (title) title.after(nav);
    else article.prepend(nav);
  };
  placeToc();
  wide.addEventListener('change', placeToc);
  medium.addEventListener('change', placeToc);
})();

document.addEventListener('DOMContentLoaded', () => {
  for (const block of document.querySelectorAll('.guide-content article .console-code')) {
    const code = block.querySelector('pre > code');
    const copy = block.querySelector('.console-copy');
    const language = [...(code.closest('.highlighter-rouge') || code).classList]
      .find(name => name.startsWith('language-'))?.slice('language-'.length);
    const filename = code.closest('[data-filename]')?.dataset.filename;

    const bar = document.createElement('div');
    bar.className = 'guide-code-bar';
    const badge = document.createElement('span');
    badge.className = 'guide-code-language';
    badge.textContent = language && language !== 'plaintext' ? language : 'text';
    bar.append(badge);
    if (filename) {
      const name = document.createElement('span');
      name.className = 'guide-code-filename';
      name.textContent = filename;
      bar.append(name);
    }
    if (copy) bar.append(copy);
    block.prepend(bar);
  }
});
