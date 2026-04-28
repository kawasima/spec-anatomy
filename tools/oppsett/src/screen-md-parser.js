import { makeGroup, makeItem } from "./state.js";

// screen.md → state パーツ
// 戻り値: {
//   frontmatter: { ... },
//   layoutVariant: "PC版",
//   groups: [...],
//   items: [...],   // selector/rect は null。後で DOM 照合で埋める。
//   rawSections: string,  // フロントマターを除いた本文（## レイアウトバリアント節も含む全文）。書き戻し時に「## レイアウトバリアント」前後を切り出す。
// }

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n?/;

function parseFrontmatter(text) {
  const m = text.match(FRONTMATTER_RE);
  if (!m) return { frontmatter: {}, body: text };
  const yaml = m[1];
  const fm = {};
  for (const line of yaml.split("\n")) {
    const idx = line.indexOf(":");
    if (idx < 0) continue;
    const k = line.slice(0, idx).trim();
    let v = line.slice(idx + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    fm[k] = v;
  }
  return { frontmatter: fm, body: text.slice(m[0].length) };
}

function splitTableRow(line) {
  // 「| a | b | c |」を ["a", "b", "c"] に分解。エスケープされたパイプ \| はそのまま戻す。
  const trimmed = line.trim();
  if (!trimmed.startsWith("|")) return null;
  const inner = trimmed.replace(/^\|/, "").replace(/\|$/, "");
  const parts = [];
  let buf = "";
  for (let i = 0; i < inner.length; i++) {
    const ch = inner[i];
    if (ch === "\\" && inner[i + 1] === "|") {
      buf += "|";
      i++;
      continue;
    }
    if (ch === "|") {
      parts.push(buf.trim());
      buf = "";
    } else {
      buf += ch;
    }
  }
  parts.push(buf.trim());
  return parts;
}

function isSeparatorRow(parts) {
  return parts.every((c) => /^[-:\s]+$/.test(c));
}

function unescapeCell(s) {
  if (s == null) return "";
  return s.replace(/<br>/gi, "\n").replace(/\\\|/g, "|");
}

function isVariantHeader(line) {
  return /^### (PC版|スマホ版|タブレット版|スマホ版（[^）]+）|タブレット版（[^）]+）)\s*$/.test(line);
}

function isGroupHeader(line) {
  return /^####\s*画面項目グループ\s*[::]\s*(.+)$/.test(line);
}

function extractGroupName(line) {
  const m = line.match(/^####\s*画面項目グループ\s*[::]\s*(.+)$/);
  return m ? m[1].trim() : "";
}

// レイアウトバリアント節を構造化トークンに分解する。
// state.screenMeta.layoutSections の形：
//   {
//     preface: string,                       // ## レイアウトバリアント直後の散文
//     variants: [
//       {
//         name: "PC版",
//         preface: string,                   // ### PC版 直後の散文
//         groups: [
//           { id, name, preface }            // #### グループヘッダ直後の散文（テーブルは除外）
//         ]
//       }
//     ]
//   }
// items は groupId で各グループに紐づく。テーブル行は items に展開される。

function flushPrefaceLines(lines) {
  // 末尾の連続空行を削る。先頭の空行も1行だけ削る。
  let s = lines.join("\n");
  s = s.replace(/\n+$/, "");
  s = s.replace(/^\n/, "");
  return s;
}

export function parseScreenMd(text) {
  const { frontmatter, body } = parseFrontmatter(text);
  const lines = body.split("\n");

  const groups = [];
  const items = [];

  const layoutSections = {
    preface: "",
    variants: [],
  };

  let inVariant = false; // ## レイアウトバリアント節の中か
  let currentVariant = null; // layoutSections.variants の最後の要素
  let currentGroup = null; // layoutSections.variants[*].groups の最後の要素
  let prefaceBuf = []; // 散文蓄積バッファ
  // prefaceTarget: "section" | "variant" | "group-preface" | "group-postface" | null
  let prefaceTarget = null;
  let inTable = false;
  let headerCells = null;

  const flushPreface = () => {
    if (!prefaceTarget) {
      prefaceBuf = [];
      return;
    }
    const text = flushPrefaceLines(prefaceBuf);
    if (prefaceTarget === "section") {
      layoutSections.preface = text;
    } else if (prefaceTarget === "variant" && currentVariant) {
      currentVariant.preface = text;
    } else if (prefaceTarget === "group-preface" && currentGroup) {
      currentGroup.preface = text;
    } else if (prefaceTarget === "group-postface" && currentGroup) {
      currentGroup.postface = text;
    }
    prefaceBuf = [];
    prefaceTarget = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // ## h2 行の検出（レイアウトバリアント節の開始/終了）
    if (line.startsWith("## ") && !line.startsWith("### ")) {
      flushPreface();
      if (line.startsWith("## レイアウトバリアント")) {
        inVariant = true;
        prefaceTarget = "section";
      } else {
        inVariant = false;
        prefaceTarget = null;
      }
      currentVariant = null;
      currentGroup = null;
      inTable = false;
      headerCells = null;
      continue;
    }

    if (!inVariant) continue;

    // ### バリアント行
    if (isVariantHeader(line)) {
      flushPreface();
      const name = line.replace(/^###\s*/, "").trim();
      currentVariant = { name, preface: "", groups: [] };
      layoutSections.variants.push(currentVariant);
      currentGroup = null;
      inTable = false;
      headerCells = null;
      prefaceTarget = "variant";
      continue;
    }

    // #### 画面項目グループ行
    if (isGroupHeader(line)) {
      flushPreface();
      const name = extractGroupName(line);
      const group = makeGroup(name);
      groups.push(group);
      // バリアントが宣言されていない場合のフォールバック
      if (!currentVariant) {
        currentVariant = { name: "PC版", preface: "", groups: [] };
        layoutSections.variants.push(currentVariant);
      }
      currentGroup = { id: group.id, name, preface: "", postface: "" };
      currentVariant.groups.push(currentGroup);
      inTable = false;
      headerCells = null;
      prefaceTarget = "group-preface";
      continue;
    }

    // テーブル行
    if (currentGroup && line.trim().startsWith("|")) {
      // テーブルが始まるので、それまでの散文を確定する
      flushPreface();
      const parts = splitTableRow(line);
      if (!parts) continue;

      if (!inTable) {
        if (parts.includes("項目名")) {
          headerCells = parts;
          inTable = true;
        }
        continue;
      }

      if (isSeparatorRow(parts)) continue;

      // データ行
      const map = {};
      headerCells.forEach((h, idx) => {
        map[h] = unescapeCell(parts[idx] || "");
      });
      const requiredCell = (map["必須"] || "").trim();
      const required = requiredCell === "○" || requiredCell.startsWith("○");
      const item = makeItem({
        selector: null,
        rect: null,
        name: map["項目名"] || "",
        kind: map["種別"] || "label",
        groupId: currentGroup.id,
      });
      const norm = (s) => {
        const t = (s || "").trim();
        return t === "−" || t === "-" || t === "(空)" || t === "(空)" ? "" : t;
      };
      item.source = norm(map["派生元"]);
      item.editSpec = norm(map["編集仕様"]);
      item.required = required;
      item.requiredNote = required && requiredCell !== "○" ? requiredCell : "";
      item.defaultValue = norm(map["初期値"]);
      item.visibleCondition = norm(map["表示条件"]);
      items.push(item);
      continue;
    }

    // テーブルが終了
    if (inTable && !line.trim().startsWith("|")) {
      inTable = false;
      headerCells = null;
      // テーブル終了直後は postface としてグループに紐付ける
      if (currentGroup) {
        prefaceTarget = "group-postface";
      }
    }

    // それ以外の行は散文として蓄積
    if (prefaceTarget) {
      prefaceBuf.push(line);
    }
  }

  // 末尾の散文を確定
  flushPreface();

  // 後方互換のために layoutVariant も提供
  const layoutVariant = layoutSections.variants[0]?.name || "PC版";

  return {
    frontmatter,
    layoutVariant,
    layoutSections,
    groups,
    items,
    rawSections: body,
  };
}

// 名前で iframe 内 DOM 要素を探す
function findElementByName(doc, name) {
  if (!name) return null;
  const target = name.replace(/\s+/g, "").toLowerCase();

  // 1. data-item 属性での厳密一致を最優先
  const dataItemMatch = doc.querySelector(`[data-item="${CSS.escape(name)}"]`);
  if (dataItemMatch) return dataItemMatch;

  // 2. テキスト・属性での部分一致
  const candidates = doc.querySelectorAll(
    "label, th, button, a, input, select, textarea, td, dt, dd, span",
  );
  for (const el of candidates) {
    const t = (el.tagName === "INPUT" || el.tagName === "TEXTAREA")
      ? (el.getAttribute("placeholder") || el.getAttribute("aria-label") || el.getAttribute("name") || "")
      : el.textContent;
    const norm = (t || "").replace(/\s+/g, "").toLowerCase();
    if (norm && (norm === target || norm.includes(target) || target.includes(norm))) {
      return el;
    }
  }
  return null;
}

function buildSelector(el) {
  if (!el) return null;
  if (el.tagName === "BODY") return "body";
  const parts = [];
  let cur = el;
  while (cur && cur.nodeType === 1 && cur.tagName !== "BODY" && cur.tagName !== "HTML") {
    const parent = cur.parentElement;
    if (!parent) break;
    const sameTag = Array.from(parent.children).filter((c) => c.tagName === cur.tagName);
    const idx = sameTag.indexOf(cur) + 1;
    parts.unshift(`${cur.tagName.toLowerCase()}:nth-of-type(${idx})`);
    cur = parent;
  }
  return ["body", ...parts].join(" > ");
}

// パース結果の items に対し iframe document で要素位置を埋める
export function attachElementPositions(items, doc, win) {
  if (!doc) return items;
  const sx = win?.scrollX || 0;
  const sy = win?.scrollY || 0;
  return items.map((it) => {
    if (it.selector && it.rect) return it;
    const el = findElementByName(doc, it.name);
    if (!el) return it;
    const r = el.getBoundingClientRect();
    return {
      ...it,
      selector: buildSelector(el),
      rect: { x: r.left + sx, y: r.top + sy, w: r.width, h: r.height },
    };
  });
}
