import { selectorPath, parentOf, firstChildOf, prevSiblingOf, nextSiblingOf } from "./dom-walker.js";
import { inferName, inferKind } from "./inspector.js";
import { makeItem } from "./state.js";

export function setupCanvas({ iframe, store, overlay }) {
  let tentative = null;

  function setTentative(el) {
    tentative = el;
    overlay.drawTentative(el);
  }

  function clearTentative() {
    tentative = null;
    overlay.drawTentative(null);
  }

  function loadHtml(html) {
    store.set((s) => ({ ...s, designHtml: html, items: [], selectedId: null }));
    iframe.srcdoc = html;
  }

  iframe.addEventListener("load", () => {
    const doc = iframe.contentDocument;
    if (!doc) return;

    const win = iframe.contentWindow;

    doc.addEventListener("mouseover", (ev) => {
      const t = ev.target;
      if (!t || t.nodeType !== 1) return;
      if (t === doc.documentElement || t === doc.body) return;
      setTentative(t);
    });

    doc.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      if (!tentative) {
        const t = ev.target;
        if (t && t.nodeType === 1) setTentative(t);
      }
      commitTentative();
    }, true);

    doc.addEventListener("scroll", () => overlay.refresh(), true);
    win.addEventListener("scroll", () => overlay.refresh());
    win.addEventListener("resize", () => overlay.refresh());

    const ro = new ResizeObserver(() => {
      const h = doc.documentElement.scrollHeight;
      iframe.style.height = h + "px";
      overlay.refresh();
    });
    ro.observe(doc.documentElement);

    overlay.refresh();
  });

  function commitTentative() {
    if (!tentative) return;
    const sel = selectorPath(tentative);
    const win = iframe.contentWindow;
    const r = tentative.getBoundingClientRect();
    const rect = {
      x: r.left + (win?.scrollX || 0),
      y: r.top + (win?.scrollY || 0),
      w: r.width,
      h: r.height,
    };

    const currentState = store.get();

    // 選択中の項目が「未配置」（selector が無い）であれば、その項目に位置を割り当てる
    const selected = currentState.items.find((it) => it.id === currentState.selectedId);
    if (selected && !selected.selector) {
      store.set((s) => ({
        ...s,
        items: s.items.map((it) =>
          it.id === selected.id ? { ...it, selector: sel, rect } : it,
        ),
      }));
      clearTentative();
      return;
    }

    const existing = currentState.items.find((it) => it.selector === sel);
    if (existing) {
      store.set((s) => ({ ...s, selectedId: existing.id }));
      clearTentative();
      return;
    }

    const groupId = currentState.selectedGroupId || currentState.groups[0]?.id || null;
    const item = makeItem({
      selector: sel,
      rect,
      name: inferName(tentative),
      kind: inferKind(tentative),
      groupId,
    });
    store.set((s) => ({ ...s, items: [...s.items, item], selectedId: item.id }));
    clearTentative();
  }

  function moveTentative(dir) {
    if (!tentative) return;
    let next = null;
    if (dir === "up") next = parentOf(tentative);
    else if (dir === "down") next = firstChildOf(tentative);
    else if (dir === "left") next = prevSiblingOf(tentative);
    else if (dir === "right") next = nextSiblingOf(tentative);
    if (next) setTentative(next);
  }

  window.addEventListener("keydown", (ev) => {
    if (isEditingFormControl(ev.target)) return;
    if (ev.key === "ArrowUp") { ev.preventDefault(); moveTentative("up"); }
    else if (ev.key === "ArrowDown") { ev.preventDefault(); moveTentative("down"); }
    else if (ev.key === "ArrowLeft") { ev.preventDefault(); moveTentative("left"); }
    else if (ev.key === "ArrowRight") { ev.preventDefault(); moveTentative("right"); }
    else if (ev.key === "Enter") { ev.preventDefault(); commitTentative(); }
    else if (ev.key === "Escape") { clearTentative(); }
  });

  return { loadHtml };
}

function isEditingFormControl(el) {
  if (!el) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (el.isContentEditable) return true;
  return false;
}
