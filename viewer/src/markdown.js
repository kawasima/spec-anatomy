// ScreenLayout の独自ブロック記法。
//
// Markdown 内で次のように書く：
//
//   :::layout src="layout/SCREEN-BT-02-pc.html" height="800px"
//   :::
//
// または1行記法：
//
//   :::layout layout/SCREEN-BT-02-pc.html 800px
//
// これを iframe + 「oppsett で編集」リンク + 「HTML を別タブで開く」リンクに置き換える。
// 通常の `<ScreenLayout ... />` 形式も後方互換でサポート。

const LAYOUT_BLOCK_RE =
  /:::\s*layout\s+([^\n]+?)\s*\n([\s\S]*?):::\s*\n?/g;
const LAYOUT_LINE_RE = /:::\s*layout\s+([^\n]+)\n/g;
// 属性中に / を含み得る (例: src="layout/SCREEN-BT-02-pc.html") ので、
// 終端は \s*/?>\s* で受ける。改行は跨がない。
const VUE_TAG_RE = /<ScreenLayout\b([^>\n]*?)\/?>/g;

export function renderScreenLayoutBlocks(md, currentPath) {
  // <ScreenLayout src="..." height="..." /> 形式
  md = md.replace(VUE_TAG_RE, (_, attrs) => {
    const src = pickAttr(attrs, "src");
    const height = pickAttr(attrs, "height") || "600px";
    return src ? renderBlock(src, height, currentPath) : "";
  });
  // :::layout ... :::
  md = md.replace(LAYOUT_BLOCK_RE, (_, header) => {
    const { src, height } = parseHeader(header);
    return src ? renderBlock(src, height || "600px", currentPath) : "";
  });
  // :::layout src=... 単独
  md = md.replace(LAYOUT_LINE_RE, (_, header) => {
    const { src, height } = parseHeader(header);
    return src ? renderBlock(src, height || "600px", currentPath) : "";
  });
  return md;
}

function pickAttr(attrs, name) {
  const m = attrs.match(new RegExp(`${name}\\s*=\\s*"([^"]+)"`));
  return m ? m[1] : null;
}

function parseHeader(s) {
  // src="..." height="..." 形式
  let src = pickAttr(s, "src");
  let height = pickAttr(s, "height");
  // 単純なスペース区切り (1 番目: src, 2 番目: height) も許容
  if (!src) {
    const tokens = s.trim().split(/\s+/);
    src = tokens[0];
    if (!height && tokens[1]) height = tokens[1];
  }
  return { src, height };
}

function renderBlock(src, height, currentPath) {
  // src は HTML パス。PNG パスは同じ basename + .overlay.png として推測する。
  const absHtml = "/" + resolveAbsolute(src, currentPath);
  const absPng = absHtml.replace(/\.html?$/i, ".overlay.png");
  const oppsettUrl = buildOppsettUrl(absHtml, "/" + currentPath);
  // キャッシュバスター（ブラウザの古いPNGを表示しないように、保存時に rerender するときの URL を変えやすくする）
  const cacheBust = "?t=" + Date.now();
  return `
<div class="screen-layout" data-png="${escapeAttr(absPng)}" data-html="${escapeAttr(absHtml)}">
  <div class="screen-layout-toolbar">
    <span class="screen-layout-label">レイアウトプレビュー</span>
    <a class="open-oppsett" href="${escapeAttr(oppsettUrl)}" data-oppsett-url="${escapeAttr(oppsettUrl)}" target="_blank" rel="noopener">マークアップする ↗</a>
    <a class="open-html" href="${escapeAttr(absHtml)}" target="_blank" rel="noopener">HTML を別タブで開く ↗</a>
  </div>
  <div class="screen-layout-body">
    <img class="screen-layout-png" src="${escapeAttr(absPng + cacheBust)}" alt="レイアウト画像" loading="lazy"
      onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
    <div class="screen-layout-fallback" style="display:none">
      <p class="screen-layout-fallback-msg">レイアウトPNGがまだ生成されていません。<br>「マークアップする」を押して oppsett で編集・保存すると生成されます。<br>下にデザインHTMLを表示します。</p>
      <iframe src="${escapeAttr(absHtml)}" style="height:${escapeAttr(height)};width:100%;border:none;display:block;background:#fff" sandbox="allow-same-origin" loading="lazy"></iframe>
    </div>
  </div>
</div>
`;
}

function buildOppsettUrl(htmlAbs, mdAbs) {
  const params = new URLSearchParams();
  params.set("html", htmlAbs);
  params.set("md", mdAbs);
  return `/tools/oppsett/index.html?${params.toString()}`;
}

// currentPath: "docs/examples/.../foo.md" のようなリポジトリ相対パス
// rel: "layout/SCREEN-BT-02-pc.html" または "../foo/bar.md" のような相対パス
// 戻り値: "docs/examples/.../layout/SCREEN-BT-02-pc.html" のような絶対正規化パス
function resolveAbsolute(rel, currentPath) {
  if (rel.startsWith("/")) return rel.slice(1);
  if (/^https?:/.test(rel)) return rel;
  const dir = currentPath.split("/").slice(0, -1).join("/");
  const parts = (dir ? `${dir}/${rel}` : rel).split("/");
  const stack = [];
  for (const p of parts) {
    if (p === "..") stack.pop();
    else if (p && p !== ".") stack.push(p);
  }
  return stack.join("/");
}

// 内部 Markdown リンク (例: ../foo.md, ./bar/README.md, /docs/.../baz.md) を
// hash ベースのルートに書き換える。ファイル拡張子が .md のもののみ対象。
// その他のリンク (.html, .png, 外部URL) はそのまま。
export function rewriteMarkdownLinks(html, currentPath) {
  // <a href="..."> を全部見て .md なら #/... に書き換え
  return html.replace(/<a([^>]*?)href="([^"]+)"([^>]*?)>/g, (m, pre, href, post) => {
    if (/^https?:/i.test(href)) return m;
    if (href.startsWith("#")) return m;
    if (href.startsWith("/")) {
      // 絶対パス内 .md は hash に変換
      if (href.endsWith(".md")) {
        return `<a${pre}href="#${href}"${post}>`;
      }
      return m;
    }
    if (!href.endsWith(".md")) return m;
    // 相対パス .md → 正規化して hash に
    const abs = resolveAbsolute(href, currentPath);
    return `<a${pre}href="#/${abs}"${post}>`;
  });
}

function escapeAttr(s) {
  return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}
