export function parentOf(el) {
  const p = el.parentElement;
  if (!p || p.tagName === "HTML") return null;
  return p;
}

export function firstChildOf(el) {
  return el.firstElementChild || null;
}

export function prevSiblingOf(el) {
  return el.previousElementSibling || null;
}

export function nextSiblingOf(el) {
  return el.nextElementSibling || null;
}

export function selectorPath(el) {
  if (!el || el.nodeType !== 1) return "";
  if (el.tagName === "BODY") return "body";
  if (el.tagName === "HTML") return "html";

  const parts = [];
  let cur = el;
  while (cur && cur.nodeType === 1 && cur.tagName !== "BODY" && cur.tagName !== "HTML") {
    const parent = cur.parentElement;
    if (!parent) break;
    const sameTag = Array.from(parent.children).filter(
      (c) => c.tagName === cur.tagName,
    );
    const idx = sameTag.indexOf(cur) + 1;
    parts.unshift(`${cur.tagName.toLowerCase()}:nth-of-type(${idx})`);
    cur = parent;
  }
  return ["body", ...parts].join(" > ");
}

export function resolveSelector(doc, selector) {
  if (!selector) return null;
  try {
    return doc.querySelector(selector);
  } catch {
    return null;
  }
}
