import { resolveSelector } from "./dom-walker.js";

export function setupOverlay({ layer, iframe, store }) {
  let tentativeEl = null;

  function getIframeOffsetInLayer() {
    // overlay layer と iframe は同じ親(#drop-zone)直下にある前提。
    // iframe の offsetLeft/offsetTop は overlay layer の親基準と同じ。
    return { left: iframe.offsetLeft, top: iframe.offsetTop };
  }

  function rectFromEl(el) {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const off = getIframeOffsetInLayer();
    return {
      left: r.left + off.left,
      top: r.top + off.top,
      width: r.width,
      height: r.height,
    };
  }

  function clearChildren() {
    while (layer.firstChild) layer.removeChild(layer.firstChild);
  }

  function render() {
    clearChildren();
    const doc = iframe.contentDocument;
    if (!doc) return;
    const state = store.get();

    state.items.forEach((it, idx) => {
      const el = resolveSelector(doc, it.selector);
      const r = el ? rectFromEl(el) : positionFromCachedRect(it);
      if (!r) return;
      const box = document.createElement("div");
      box.className = "overlay-rect";
      if (it.id === state.selectedId) box.classList.add("selected");
      box.style.left = r.left + "px";
      box.style.top = r.top + "px";
      box.style.width = r.width + "px";
      box.style.height = r.height + "px";
      box.dataset.itemId = it.id;
      layer.appendChild(box);

      const badge = document.createElement("div");
      badge.className = "overlay-badge";
      if (it.id === state.selectedId) badge.classList.add("selected");
      badge.style.left = r.left + "px";
      badge.style.top = r.top + "px";
      badge.textContent = String(idx + 1);
      badge.title = "クリックで選択";
      badge.addEventListener("click", (ev) => {
        ev.stopPropagation();
        store.set((s) => ({ ...s, selectedId: it.id }));
      });
      layer.appendChild(badge);
    });

    if (tentativeEl) {
      const r = rectFromEl(tentativeEl);
      if (r) {
        const box = document.createElement("div");
        box.className = "overlay-tentative";
        box.style.left = r.left + "px";
        box.style.top = r.top + "px";
        box.style.width = r.width + "px";
        box.style.height = r.height + "px";
        layer.appendChild(box);
      }
    }
  }

  function positionFromCachedRect(it) {
    if (!it.rect) return null;
    const off = getIframeOffsetInLayer();
    const win = iframe.contentWindow;
    const sx = win?.scrollX || 0;
    const sy = win?.scrollY || 0;
    return {
      left: it.rect.x + off.left - sx,
      top: it.rect.y + off.top - sy,
      width: it.rect.w,
      height: it.rect.h,
    };
  }

  function drawTentative(el) {
    tentativeEl = el;
    render();
  }

  function refresh() {
    render();
  }

  store.subscribe(() => render());

  return { refresh, drawTentative };
}
