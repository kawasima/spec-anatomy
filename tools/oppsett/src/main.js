import { createStore } from "./state.js";
import { setupCanvas } from "./canvas.js";
import { setupOverlay } from "./overlay.js";
import { setupSidepanel } from "./sidepanel.js";
import {
  setupAutoSave,
  loadFromLocalStorage,
  exportProject,
  importProject,
  readFileAsText,
  clearLocalStorage,
  migrate,
} from "./storage.js";
import { exportOverlayHtml, exportOverlayPng, exportScreenMd, saveToRepository } from "./exporter.js";
import { parseScreenMd, attachElementPositions } from "./screen-md-parser.js";

function $(id) {
  return document.getElementById(id);
}

function init() {
  const iframe = $("design-frame");
  const overlayLayer = $("overlay-layer");
  const groupListEl = $("group-list");
  const listEl = $("item-list");
  const formEl = $("item-form");

  const store = createStore();

  const overlay = setupOverlay({ layer: overlayLayer, iframe, store });
  const canvas = setupCanvas({ iframe, store, overlay });
  setupSidepanel({ groupListEl, listEl, formEl, iframe, store });
  setupAutoSave(store);

  const restored = loadFromLocalStorage();
  if (restored && restored.designHtml) {
    store.set(restored);
    iframe.srcdoc = restored.designHtml;
  }

  bindToolbar({ store, canvas });
  loadFromUrlParams({ store, canvas, iframe });
}

function stripLeadingSlash(p) {
  return p && p.startsWith("/") ? p.slice(1) : p;
}

async function loadFromUrlParams({ store, canvas, iframe }) {
  const params = new URLSearchParams(window.location.search);
  const htmlPath = params.get("html");
  const mdPath = params.get("md");
  if (!htmlPath && !mdPath) return;

  // URLパラメータから来た時はリポジトリへの保存ボタンを表示
  const saveBtn = document.getElementById("btn-save-to-repo");
  if (saveBtn) saveBtn.hidden = false;

  if (htmlPath) {
    try {
      const res = await fetch(htmlPath);
      if (res.ok) {
        const text = await res.text();
        canvas.loadHtml(text);
        // designHtmlPath はリポジトリ相対パスで保持
        store.set((s) => ({ ...s, designHtmlPath: stripLeadingSlash(htmlPath) }));
      } else {
        console.warn(`oppsett: ${htmlPath} の取得に失敗 (status=${res.status})`);
      }
    } catch (e) {
      console.warn(`oppsett: ${htmlPath} の取得でエラー`, e);
    }
  }

  if (mdPath) {
    try {
      const res = await fetch(mdPath);
      if (res.ok) {
        const text = await res.text();
        const parsed = parseScreenMd(text);
        // iframe のロード完了を待ってから DOM 照合
        await new Promise((r) => setTimeout(r, 200));
        const doc = iframe.contentDocument;
        const win = iframe.contentWindow;
        const itemsWithPos = attachElementPositions(parsed.items, doc, win);
        store.set((s) => ({
          ...s,
          screenMeta: {
            frontmatter: parsed.frontmatter,
            layoutVariant: parsed.layoutVariant,
            layoutSections: parsed.layoutSections,
            rawSections: parsed.rawSections,
            // 保存先パスを覚えておく（リポジトリ相対）
            mdRepoPath: stripLeadingSlash(mdPath),
          },
          groups: parsed.groups.length > 0 ? parsed.groups : s.groups,
          items: itemsWithPos,
          selectedId: null,
          selectedGroupId: parsed.groups[0]?.id || s.selectedGroupId,
        }));
      }
    } catch (e) {
      console.warn(`oppsett: ${mdPath} の取得でエラー`, e);
    }
  }
}

function bindToolbar({ store, canvas }) {
  $("btn-load-html").addEventListener("click", () => $("file-html").click());
  $("file-html").addEventListener("change", async (ev) => {
    const file = ev.target.files?.[0];
    if (!file) return;
    const text = await readFileAsText(file);
    canvas.loadHtml(text);
    ev.target.value = "";
  });

  $("drop-zone").addEventListener("dragover", (ev) => {
    ev.preventDefault();
    ev.currentTarget.classList.add("drag-over");
  });
  $("drop-zone").addEventListener("dragleave", (ev) => {
    ev.currentTarget.classList.remove("drag-over");
  });
  $("drop-zone").addEventListener("drop", async (ev) => {
    ev.preventDefault();
    ev.currentTarget.classList.remove("drag-over");
    const file = ev.dataTransfer?.files?.[0];
    if (!file) return;
    const text = await readFileAsText(file);
    canvas.loadHtml(text);
  });

  $("btn-save-project").addEventListener("click", () => exportProject(store));
  $("btn-load-project").addEventListener("click", () => $("file-project").click());
  $("file-project").addEventListener("change", async (ev) => {
    const file = ev.target.files?.[0];
    if (!file) return;
    try {
      const raw = await importProject(file);
      if (raw && typeof raw === "object") {
        const data = migrate(raw);
        store.set(data);
        const iframe = $("design-frame");
        if (data.designHtml) iframe.srcdoc = data.designHtml;
      }
    } catch (e) {
      alert("プロジェクトファイルの読み込みに失敗しました: " + e.message);
    }
    ev.target.value = "";
  });

  $("btn-export-overlay").addEventListener("click", () => exportOverlayHtml(store));
  $("btn-export-overlay-png").addEventListener("click", () => exportOverlayPng(store));
  $("btn-save-to-repo").addEventListener("click", async () => {
    const btn = $("btn-save-to-repo");
    const orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = "保存中…";
    try {
      const written = await saveToRepository(store);
      btn.textContent = "✓ 保存しました";
      // 親ウィンドウ (viewer) に通知
      try {
        if (window.opener && !window.opener.closed) {
          window.opener.postMessage(
            { type: "oppsett:saved", written },
            window.location.origin,
          );
        }
      } catch (_) { /* noop */ }
      setTimeout(() => {
        btn.textContent = orig;
        btn.disabled = false;
      }, 2000);
    } catch (e) {
      btn.textContent = orig;
      btn.disabled = false;
      alert("保存に失敗しました: " + e.message);
    }
  });
  $("btn-export-screen-md").addEventListener("click", () => exportScreenMd(store));

  $("btn-load-screen-md").addEventListener("click", () => $("file-screen-md").click());
  $("file-screen-md").addEventListener("change", async (ev) => {
    const file = ev.target.files?.[0];
    if (!file) return;
    try {
      const text = await readFileAsText(file);
      const parsed = parseScreenMd(text);
      const iframe = $("design-frame");
      const doc = iframe.contentDocument;
      const win = iframe.contentWindow;
      const itemsWithPos = attachElementPositions(parsed.items, doc, win);
      store.set((s) => ({
        ...s,
        screenMeta: {
          frontmatter: parsed.frontmatter,
          layoutVariant: parsed.layoutVariant,
          layoutSections: parsed.layoutSections,
          rawSections: parsed.rawSections,
        },
        groups: parsed.groups.length > 0 ? parsed.groups : s.groups,
        items: itemsWithPos,
        selectedId: null,
        selectedGroupId: parsed.groups[0]?.id || s.selectedGroupId,
      }));
    } catch (e) {
      alert("screen.md の読み込みに失敗しました: " + e.message);
    }
    ev.target.value = "";
  });

  $("btn-reset").addEventListener("click", () => {
    if (!confirm("作業中のプロジェクトを破棄します。よろしいですか？")) return;
    clearLocalStorage();
    location.reload();
  });
}

init();
