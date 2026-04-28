const KEY = "oppsett:project";

function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

export function setupAutoSave(store) {
  const save = debounce(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(store.get()));
    } catch (e) {
      console.warn("autosave failed", e);
    }
  }, 500);
  store.subscribe(save);
}

export function loadFromLocalStorage() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return migrate(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function migrate(state) {
  if (!state || typeof state !== "object") return state;
  // 旧形式（groups なし）→ 新形式へ
  if (!Array.isArray(state.groups)) {
    const defaultGroup = { id: "g-default", name: "未分類" };
    state.groups = [defaultGroup];
    state.selectedGroupId = defaultGroup.id;
    if (Array.isArray(state.items)) {
      state.items = state.items.map((it) => ({ ...it, groupId: defaultGroup.id }));
    }
  }
  if (!state.screenMeta) {
    state.screenMeta = { frontmatter: {}, rawSections: "", layoutVariant: "PC版" };
  }
  return state;
}

export function clearLocalStorage() {
  localStorage.removeItem(KEY);
}

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`;
}

export function exportProject(store) {
  const blob = new Blob([JSON.stringify(store.get(), null, 2)], {
    type: "application/json",
  });
  triggerDownload(blob, `oppsett-project-${timestamp()}.json`);
}

export function importProject(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(reader.result));
      } catch (e) {
        reject(e);
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}
