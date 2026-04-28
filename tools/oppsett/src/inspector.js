const INPUT_KIND_MAP = {
  text: "text",
  search: "text",
  email: "text",
  tel: "text",
  url: "text",
  password: "text",
  number: "text",
  date: "text",
  "datetime-local": "text",
  time: "text",
  checkbox: "checkbox",
  radio: "radio",
  file: "file",
  hidden: "hidden",
  submit: "button",
  button: "button",
  reset: "button",
};

function trimText(s, max = 40) {
  if (!s) return "";
  const t = s.replace(/\s+/g, " ").trim();
  return t.length > max ? t.slice(0, max) : t;
}

function findLabelFor(el) {
  if (!el.id) return null;
  const doc = el.ownerDocument;
  return doc.querySelector(`label[for="${CSS.escape(el.id)}"]`);
}

function findEnclosingLabel(el) {
  let cur = el.parentElement;
  while (cur) {
    if (cur.tagName === "LABEL") return cur;
    cur = cur.parentElement;
  }
  return null;
}

function findHeaderForCell(cell) {
  const row = cell.parentElement;
  if (!row) return "";
  const idx = Array.from(row.children).indexOf(cell);
  if (idx < 0) return "";
  const table = cell.closest("table");
  if (!table) return "";
  const headRow = table.querySelector("thead tr") || table.querySelector("tr");
  if (!headRow || headRow === row) return "";
  const th = headRow.children[idx];
  if (!th) return "";
  return trimText(th.textContent);
}

function findNearbyLabelText(el) {
  const prev = el.previousElementSibling;
  if (prev && (prev.tagName === "LABEL" || prev.tagName === "TH" || prev.tagName === "SPAN")) {
    const t = trimText(prev.textContent);
    if (t) return t;
  }
  const cell = el.closest("td");
  if (cell) {
    const t = findHeaderForCell(cell);
    if (t) return t;
  }
  return "";
}

export function inferName(el) {
  if (!el) return "";
  const tag = el.tagName;

  if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
    const lab = findLabelFor(el) || findEnclosingLabel(el);
    if (lab) {
      const t = trimText(lab.textContent);
      if (t) return t;
    }
    const placeholder = el.getAttribute("placeholder");
    if (placeholder) return trimText(placeholder);
    const aria = el.getAttribute("aria-label");
    if (aria) return trimText(aria);
    const nearby = findNearbyLabelText(el);
    if (nearby) return nearby;
    const name = el.getAttribute("name");
    if (name) return trimText(name);
    return "";
  }

  if (tag === "TH") {
    return trimText(el.textContent);
  }

  if (tag === "TD") {
    const headerText = findHeaderForCell(el);
    if (headerText) return headerText;
    return trimText(el.textContent);
  }

  if (tag === "BUTTON" || tag === "A") {
    return trimText(el.textContent);
  }

  if (tag === "LABEL") {
    return trimText(el.textContent);
  }

  if (tag === "IMG") {
    const alt = el.getAttribute("alt");
    if (alt) return trimText(alt);
    return "画像";
  }

  return trimText(el.textContent);
}

export function inferKind(el) {
  if (!el) return "label";
  const tag = el.tagName;
  if (tag === "INPUT") {
    const type = (el.getAttribute("type") || "text").toLowerCase();
    return INPUT_KIND_MAP[type] || "text";
  }
  if (tag === "SELECT") return "select_pulldown";
  if (tag === "TEXTAREA") return "textarea";
  if (tag === "BUTTON") return "button";
  if (tag === "A") return "link";
  if (tag === "IMG") return "image";
  return "label";
}
