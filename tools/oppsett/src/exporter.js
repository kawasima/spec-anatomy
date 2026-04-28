import { triggerDownload } from "./storage.js";
import { buildScreenMd } from "./screen-md-writer.js";

const OVERLAY_STYLE = `
.oppsett-overlay-rect {
  position: absolute;
  border: 2px solid #e11d48;
  pointer-events: none;
  box-sizing: border-box;
  z-index: 99998;
}
.oppsett-overlay-badge {
  position: absolute;
  background: #e11d48;
  color: #fff;
  font: bold 12px/1 sans-serif;
  padding: 2px 6px;
  border-radius: 10px;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 99999;
}
`;

export function exportOverlayHtml(store) {
  const state = store.get();
  if (!state.designHtml) return;
  const parser = new DOMParser();
  const doc = parser.parseFromString(state.designHtml, "text/html");

  const styleEl = doc.createElement("style");
  styleEl.textContent = OVERLAY_STYLE;
  doc.head.appendChild(styleEl);

  ensureBodyRelative(doc);

  state.items.forEach((it, idx) => {
    if (!it.rect) return;
    const r = { left: it.rect.x, top: it.rect.y, width: it.rect.w, height: it.rect.h };
    const box = doc.createElement("div");
    box.className = "oppsett-overlay-rect";
    box.style.left = r.left + "px";
    box.style.top = r.top + "px";
    box.style.width = r.width + "px";
    box.style.height = r.height + "px";
    doc.body.appendChild(box);

    const badge = doc.createElement("div");
    badge.className = "oppsett-overlay-badge";
    badge.style.left = r.left + "px";
    badge.style.top = r.top + "px";
    badge.textContent = String(idx + 1);
    doc.body.appendChild(badge);
  });

  const html = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  triggerDownload(blob, "overlay.html");
}

function ensureBodyRelative(doc) {
  const styleEl = doc.createElement("style");
  styleEl.textContent = "body { position: relative; }";
  doc.head.appendChild(styleEl);
}

// iframe 内の DOM に一時的にオーバーレイを注入する。除去用の関数を返す。
function injectOverlayIntoFrame(iframe, items) {
  const doc = iframe.contentDocument;
  if (!doc) return () => {};
  const style = doc.createElement("style");
  style.setAttribute("data-oppsett-injected", "1");
  style.textContent = OVERLAY_STYLE + "\nbody { position: relative; }";
  doc.head.appendChild(style);

  const injectedNodes = [style];
  items.forEach((it, idx) => {
    if (!it.rect) return;
    const box = doc.createElement("div");
    box.className = "oppsett-overlay-rect";
    box.setAttribute("data-oppsett-injected", "1");
    box.style.left = it.rect.x + "px";
    box.style.top = it.rect.y + "px";
    box.style.width = it.rect.w + "px";
    box.style.height = it.rect.h + "px";
    doc.body.appendChild(box);
    injectedNodes.push(box);

    const badge = doc.createElement("div");
    badge.className = "oppsett-overlay-badge";
    badge.setAttribute("data-oppsett-injected", "1");
    badge.style.left = it.rect.x + "px";
    badge.style.top = it.rect.y + "px";
    badge.textContent = String(idx + 1);
    doc.body.appendChild(badge);
    injectedNodes.push(badge);
  });

  return () => {
    for (const n of injectedNodes) n.parentNode?.removeChild(n);
  };
}

export async function exportOverlayPng(store) {
  if (typeof window.html2canvas !== "function") {
    alert("html2canvas が読み込まれていません");
    return;
  }
  const state = store.get();
  const iframe = document.getElementById("design-frame");
  const doc = iframe?.contentDocument;
  if (!doc) {
    alert("デザインHTML が読み込まれていません");
    return;
  }

  const cleanup = injectOverlayIntoFrame(iframe, state.items);
  try {
    const target = doc.documentElement;
    const canvas = await window.html2canvas(target, {
      backgroundColor: "#ffffff",
      useCORS: true,
      logging: false,
      width: target.scrollWidth,
      height: target.scrollHeight,
      windowWidth: target.scrollWidth,
      windowHeight: target.scrollHeight,
    });
    const filename = deriveFileName(state, "overlay.png");
    await new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (blob) {
          triggerDownload(blob, filename);
        }
        resolve();
      }, "image/png");
    });
    const variant = state.screenMeta?.layoutVariant || "PC版";
    store.set((s) => ({
      ...s,
      screenMeta: {
        ...(s.screenMeta || {}),
        layoutImageMap: {
          ...((s.screenMeta || {}).layoutImageMap || {}),
          [variant]: `layout/${filename}`,
        },
      },
    }));
  } catch (e) {
    alert("PNG の生成に失敗しました: " + e.message);
  } finally {
    cleanup();
  }
}

function deriveFileName(state, ext) {
  const fm = state.screenMeta?.frontmatter || {};
  const id = fm.screenId || "screen";
  const variant = (state.screenMeta?.layoutVariant || "PC版").replace(/\s+/g, "-");
  const device = variant === "PC版" ? "pc" : variant === "スマホ版" ? "mobile" : variant;
  return `${id}-${device}.${ext}`;
}

function deviceFromVariant(variant) {
  if (variant === "PC版") return "pc";
  if (variant === "スマホ版") return "mobile";
  return (variant || "pc").replace(/[^a-zA-Z0-9]+/g, "-").toLowerCase();
}

// iframe をキャプチャして PNG の base64 を返す（書き出しなし）
async function captureOverlayPngBase64(state, iframe) {
  if (typeof window.html2canvas !== "function") {
    throw new Error("html2canvas が読み込まれていません");
  }
  const doc = iframe?.contentDocument;
  if (!doc) throw new Error("デザインHTML が読み込まれていません");

  const cleanup = injectOverlayIntoFrame(iframe, state.items);
  try {
    const target = doc.documentElement;
    const canvas = await window.html2canvas(target, {
      backgroundColor: "#ffffff",
      useCORS: true,
      logging: false,
      width: target.scrollWidth,
      height: target.scrollHeight,
      windowWidth: target.scrollWidth,
      windowHeight: target.scrollHeight,
    });
    const dataUrl = canvas.toDataURL("image/png");
    // "data:image/png;base64,..." → base64 の中身だけ取り出す
    return dataUrl.split(",")[1];
  } finally {
    cleanup();
  }
}

// リポジトリに screen.md と PNG を一括保存する。
// - state.screenMeta.frontmatter.mdRepoPath: screen.md のリポジトリ相対パス（URLパラメータ ?md= から渡る）
// - state.designHtmlPath: デザインHTMLのリポジトリ相対パス（URLパラメータ ?html= から渡る）
// PNG は同じディレクトリの layout/SCREEN-XXX-{device}.overlay.png として保存。
export async function saveToRepository(store) {
  const state = store.get();
  const meta = state.screenMeta || {};
  const mdPath = meta.mdRepoPath;
  const htmlPath = state.designHtmlPath;

  if (!mdPath) {
    throw new Error("screen.md のパスが分かりません（URLパラメータ ?md= がありません）");
  }
  if (!htmlPath) {
    throw new Error("デザインHTMLのパスが分かりません（URLパラメータ ?html= がありません）");
  }

  // PNG パスは デザインHTML と同じディレクトリ + .overlay.png
  // 例: docs/examples/.../layout/SCREEN-BT-02-pc.html
  //   → docs/examples/.../layout/SCREEN-BT-02-pc.overlay.png
  const pngPath = htmlPath.replace(/\.html?$/i, ".overlay.png");

  // PNG をキャプチャ
  const iframe = document.getElementById("design-frame");
  const pngBase64 = await captureOverlayPngBase64(state, iframe);

  // PNG パスは screen.md からの相対パスとして layoutImageMap に保存
  const variant = meta.layoutVariant || "PC版";
  const mdDir = mdPath.split("/").slice(0, -1).join("/");
  const pngRelToMd = relativePath(mdDir, pngPath);

  store.set((s) => ({
    ...s,
    screenMeta: {
      ...(s.screenMeta || {}),
      layoutImageMap: {
        ...((s.screenMeta || {}).layoutImageMap || {}),
        [variant]: pngRelToMd,
      },
    },
  }));

  const md = buildScreenMd(store.get());

  // POST /api/save-screen
  const res = await fetch("/api/save-screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      md: { path: mdPath, content: md },
      png: { path: pngPath, base64: pngBase64 },
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`保存失敗: ${err.error || res.status}`);
  }
  const data = await res.json();
  return data.written || [];
}

// 簡易な相対パス計算
function relativePath(fromDir, toPath) {
  if (!fromDir) return toPath;
  const fromParts = fromDir.split("/").filter(Boolean);
  const toParts = toPath.split("/").filter(Boolean);
  let i = 0;
  while (i < fromParts.length && i < toParts.length && fromParts[i] === toParts[i]) i++;
  const ups = "../".repeat(fromParts.length - i);
  const downs = toParts.slice(i).join("/");
  return ups + downs;
}

export function exportScreenMd(store) {
  const md = buildScreenMd(store.get());
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const fm = store.get().screenMeta?.frontmatter || {};
  const filename = (fm.screenId || "screen") + ".md";
  triggerDownload(blob, filename);
}
