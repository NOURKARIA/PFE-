// DOM extractor to run inside page.evaluate()
(function() {
  function isVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity || '1') === 0) return false;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return false;
    return true;
  }

  const tags = ['button','input','a','select','textarea','label','option'];
  const candidates = Array.from(document.querySelectorAll(tags.join(',')));

  const nodes = candidates
    .filter(isVisible)
    .map(el => {
      const r = el.getBoundingClientRect();
      const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('alt') || '').toString().trim();
      return {
        tag: el.tagName.toLowerCase(),
        text: text || null,
        x: r.left + window.scrollX,
        y: r.top + window.scrollY,
        width: r.width,
        height: r.height,
        id: el.id || null,
        class: el.className || null,
        name: el.getAttribute('name') || null,
        role: el.getAttribute('role') || null
      };
    });

  return nodes;
})();
