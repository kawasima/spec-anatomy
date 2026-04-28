import { marked } from "marked";
import { NAV } from "./nav.js";
import { renderScreenLayoutBlocks, rewriteMarkdownLinks } from "./markdown.js";

// ハッシュベースのシンプルなルーター。
// URL は #/<path> 形式 (例: #/docs/spec-set/README.md)。
// ブラウザの絶対パスベースだと「SPA 全リンクを intercept する」問題が出やすいので、
// hash で完全に切り離す。

const articleEl = document.getElementById("article");
const navEl = document.getElementById("nav");

// サイドバーを描画
function renderNav() {
  navEl.innerHTML = "";
  for (const entry of NAV) {
    navEl.appendChild(renderNavEntry(entry, 0));
  }
}

function renderNavEntry(entry, depth) {
  const wrap = document.createElement("div");
  wrap.className = `nav-entry depth-${depth}`;

  if (entry.path) {
    const a = document.createElement("a");
    a.className = "nav-link";
    a.href = `#/${entry.path}`;
    a.textContent = entry.text;
    a.dataset.path = entry.path;
    wrap.appendChild(a);
  } else if (entry.external) {
    const a = document.createElement("a");
    a.className = "nav-link external";
    a.href = entry.external;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = entry.text + " ↗";
    wrap.appendChild(a);
  } else {
    const span = document.createElement("span");
    span.className = "nav-section";
    span.textContent = entry.text;
    wrap.appendChild(span);
  }

  if (entry.items?.length) {
    const sub = document.createElement("div");
    sub.className = "nav-sub";
    for (const it of entry.items) {
      sub.appendChild(renderNavEntry(it, depth + 1));
    }
    wrap.appendChild(sub);
  }
  return wrap;
}

// アクティブなリンクをハイライト
function highlightActive(path) {
  for (const a of navEl.querySelectorAll(".nav-link")) {
    a.classList.toggle("active", a.dataset.path === path);
  }
}

// 現在の hash からパスを取り出す。空なら README.md。
function currentPath() {
  const h = window.location.hash || "";
  const m = h.match(/^#\/(.+)$/);
  return m ? decodeURIComponent(m[1]) : "README.md";
}

// Markdown を fetch してレンダリング
async function load(path) {
  articleEl.innerHTML = '<p class="loading">読み込み中…</p>';
  try {
    const res = await fetch("/" + path);
    if (!res.ok) {
      articleEl.innerHTML = `<h1>404</h1><p>${escapeHtml(path)} が見つかりません</p>`;
      return;
    }
    let md = await res.text();
    md = stripFrontmatter(md);
    md = renderScreenLayoutBlocks(md, path);
    const html = marked.parse(md, { gfm: true, breaks: false });
    const rewritten = rewriteMarkdownLinks(html, path);
    articleEl.innerHTML = rewritten;
    articleEl.scrollTo?.(0, 0);
    document.querySelector(".content")?.scrollTo(0, 0);
    window.scrollTo(0, 0);
    highlightActive(path);
    document.title = extractTitle(md) + " — Spec Anatomy";
  } catch (e) {
    articleEl.innerHTML = `<h1>Error</h1><pre>${escapeHtml(e.message)}</pre>`;
  }
}

function stripFrontmatter(md) {
  // 先頭の --- ... --- ブロックを除去
  const m = md.match(/^---\n[\s\S]*?\n---\n?/);
  return m ? md.slice(m[0].length) : md;
}

function extractTitle(md) {
  const m = md.match(/^#\s+(.+)$/m);
  return m ? m[1].trim() : "Spec Anatomy";
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// hash 変更で再描画
function onRouteChange() {
  load(currentPath());
}

// `target="_blank"` で開いた oppsett に名前を付けて、再度クリックしたとき
// 同じウィンドウを再利用するようにする
articleEl.addEventListener("click", (ev) => {
  const a = ev.target.closest("a.open-oppsett");
  if (!a) return;
  // target="oppsett-window" にすることで2回目以降は同じウィンドウを使う
  a.target = "oppsett-window";
});

// oppsett からの保存完了通知を受信して再描画
window.addEventListener("message", (ev) => {
  if (ev.origin !== window.location.origin) return;
  if (ev.data?.type !== "oppsett:saved") return;
  // 現在開いているページをリロード
  load(currentPath());
});

renderNav();
window.addEventListener("hashchange", onRouteChange);
onRouteChange();
