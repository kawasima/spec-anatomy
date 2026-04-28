// state → screen.md の文字列を組み立てる。
// rawSections（読み込み時に保持した手書きセクション）がある場合は
// 「## レイアウトバリアント」より前後の部分を活かして書き戻し、
// 中央のレイアウトバリアント節（画面項目グループ + 表）だけ oppsett が組み立てる。

const VARIANT_HEADER_RE = /^## レイアウトバリアント\s*$/m;
const NEXT_H2_AFTER_VARIANT = /\n## /;

function escapeCell(s) {
  if (s == null) return "";
  return String(s).replace(/\|/g, "\\|").replace(/\r?\n/g, "<br>");
}

function frontmatterToYaml(fm) {
  if (!fm || Object.keys(fm).length === 0) return "";
  const lines = ["---"];
  for (const [k, v] of Object.entries(fm)) {
    if (v == null) continue;
    const value = typeof v === "string" ? v : JSON.stringify(v);
    lines.push(`${k}: ${value}`);
  }
  lines.push("---");
  return lines.join("\n") + "\n\n";
}

function renderItemRow(no, it) {
  const requiredCell = it.required
    ? (it.requiredNote && it.requiredNote.trim() !== "○" ? it.requiredNote : "○")
    : "−";
  return (
    "| " +
    [
      String(no),
      escapeCell(it.name),
      escapeCell(it.kind),
      escapeCell(it.source) || "−",
      escapeCell(it.editSpec) || "−",
      requiredCell,
      escapeCell(it.defaultValue) || "−",
      escapeCell(it.visibleCondition) || "−",
    ].join(" | ") +
    " |"
  );
}

function renderItemTable(items, startNo) {
  const lines = [];
  lines.push("| No | 項目名 | 種別 | 派生元 | 編集仕様 | 必須 | 初期値 | 表示条件 |");
  lines.push("| -- | ------ | ---- | ------ | -------- | ---- | ------ | -------- |");
  let no = startNo - 1;
  for (const it of items) {
    no += 1;
    lines.push(renderItemRow(no, it));
  }
  return lines.join("\n");
}

function buildVariantSectionFromTokens(state) {
  const sections = state.screenMeta?.layoutSections;
  if (!sections || !Array.isArray(sections.variants) || sections.variants.length === 0) {
    return null;
  }
  const lines = [];
  lines.push("## レイアウトバリアント");
  lines.push("");
  if (sections.preface) {
    lines.push(sections.preface);
    lines.push("");
  }

  // バリアント名 → 画像パス。PNG 出力時に書き込まれる。
  const imageMap = state.screenMeta?.layoutImageMap || {};

  for (const variant of sections.variants) {
    lines.push(`### ${variant.name}`);
    lines.push("");
    const hasImageHint = variant.preface && /(!\[|レイアウト図)/.test(variant.preface);
    const imagePath = imageMap[variant.name];
    if (imagePath && !hasImageHint) {
      lines.push(`![${variant.name} レイアウト](${imagePath})`);
      lines.push("");
    }
    if (variant.preface) {
      lines.push(variant.preface);
      lines.push("");
    }
    let no = 0;
    for (const grp of variant.groups) {
      lines.push(`#### 画面項目グループ: ${grp.name || "(無名)"}`);
      lines.push("");
      if (grp.preface) {
        lines.push(grp.preface);
        lines.push("");
      }
      const items = state.items.filter((it) => it.groupId === grp.id);
      if (items.length > 0) {
        lines.push(renderItemTable(items, no + 1));
        lines.push("");
        no += items.length;
      }
      if (grp.postface) {
        lines.push(grp.postface);
        lines.push("");
      }
    }
  }
  return lines.join("\n");
}

function buildVariantSectionDefault(state) {
  const variant = state.screenMeta?.layoutVariant || "PC版";
  const lines = [];
  lines.push("## レイアウトバリアント");
  lines.push("");
  lines.push(`### ${variant}`);
  lines.push("");

  let no = 0;
  for (const g of state.groups) {
    const items = state.items.filter((it) => it.groupId === g.id);
    if (items.length === 0) continue;
    lines.push(`#### 画面項目グループ: ${g.name || "(無名)"}`);
    lines.push("");
    lines.push(renderItemTable(items, no + 1));
    lines.push("");
    no += items.length;
  }
  return lines.join("\n");
}

function buildVariantSection(state) {
  return buildVariantSectionFromTokens(state) || buildVariantSectionDefault(state);
}

function buildDefaultPreSection(state) {
  const fm = state.screenMeta?.frontmatter || {};
  const name = fm.name || "<画面の業務的名前>";
  const description = fm.description || "<この画面が業務上提供すること>";
  const screenId = fm.screenId || "SCREEN-XXX";
  const lines = [];
  lines.push(`# ${screenId} ${name}`);
  lines.push("");
  lines.push("## この画面の業務的役割");
  lines.push("");
  lines.push(description);
  lines.push("");
  return lines.join("\n");
}

function buildDefaultPostSection() {
  const lines = [];
  lines.push("## 画面イベント");
  lines.push("");
  lines.push(
    "| イベント名 | 発生タイミング | サーバ通信 | 対応する behavior / API | 正常時遷移先 |",
  );
  lines.push(
    "| ---------- | -------------- | ---------- | ----------------------- | ------------ |",
  );
  lines.push("");
  lines.push("## 受け入れ基準");
  lines.push("");
  lines.push("| ケース | 操作 | 期待結果 |");
  lines.push("| ------ | ---- | -------- |");
  lines.push("");
  return lines.join("\n");
}

export function buildScreenMd(state) {
  const fm = { ...(state.screenMeta?.frontmatter || {}) };
  if (state.designHtmlPath && !fm["oppsett-design-html"]) {
    fm["oppsett-design-html"] = state.designHtmlPath;
  } else if (state.designHtmlPath) {
    fm["oppsett-design-html"] = state.designHtmlPath;
  }

  const yaml = frontmatterToYaml(fm);

  const raw = state.screenMeta?.rawSections || "";
  let pre = "";
  let post = "";
  if (raw) {
    const m = raw.match(VARIANT_HEADER_RE);
    if (m) {
      pre = raw.slice(0, m.index);
      const after = raw.slice(m.index + m[0].length);
      const nextH2 = after.match(NEXT_H2_AFTER_VARIANT);
      post = nextH2 ? after.slice(nextH2.index + 1) : "";
    } else {
      pre = raw;
    }
  } else {
    pre = buildDefaultPreSection(state);
    post = buildDefaultPostSection();
  }

  const variantSection = buildVariantSection(state);

  const parts = [];
  if (yaml) parts.push(yaml.replace(/\n+$/, "\n"));
  if (pre) {
    parts.push(pre.replace(/\n+$/, ""));
    parts.push("");
  }
  parts.push(variantSection.replace(/\n+$/, ""));
  parts.push("");
  if (post) {
    parts.push(post.replace(/\n+$/, ""));
    parts.push("");
  }
  return parts.join("\n").replace(/\n{3,}/g, "\n\n");
}
