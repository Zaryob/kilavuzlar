/* Keep the directory compact on phones without hiding it when JS is disabled. */
(() => {
  const tree = document.querySelector('.guide-tree');
  const narrow = matchMedia('(max-width: 760px)');
  const update = () => { if (tree) tree.open = !narrow.matches; };
  update();
  narrow.addEventListener('change', update);
})();
