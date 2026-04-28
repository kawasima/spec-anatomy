import { indexOfItem, makeGroup } from "./state.js";
import { resolveSelector } from "./dom-walker.js";

const KIND_OPTIONS = [
  "label",
  "text",
  "textarea",
  "select_pulldown",
  "radio",
  "checkbox",
  "hidden",
  "file",
  "button",
  "link",
  "image",
];

const FIELDS = [
  { key: "groupId", label: "グループ", type: "groupSelect" },
  { key: "name", label: "項目名", type: "text" },
  { key: "kind", label: "種別", type: "kindSelect" },
  { key: "source", label: "派生元", type: "text" },
  { key: "editSpec", label: "編集仕様", type: "textarea" },
  { key: "required", label: "必須", type: "checkbox" },
  { key: "defaultValue", label: "初期値", type: "text" },
  { key: "visibleCondition", label: "表示条件", type: "text" },
];

export function setupSidepanel({ groupListEl, listEl, formEl, iframe, store }) {
  let currentFormItemId = null;
  let formInputs = {};

  function renderGroupList() {
    const state = store.get();
    groupListEl.innerHTML = "";
    state.groups.forEach((g) => {
      const row = document.createElement("div");
      row.className = "group-row";
      if (g.id === state.selectedGroupId) row.classList.add("selected");
      row.draggable = true;
      row.dataset.id = g.id;

      const nameInput = document.createElement("input");
      nameInput.className = "group-name-input";
      nameInput.value = g.name;
      nameInput.placeholder = "(グループ名)";
      nameInput.addEventListener("input", () => {
        renameGroup(g.id, nameInput.value);
      });
      nameInput.addEventListener("focus", () => selectGroup(g.id));
      nameInput.addEventListener("click", (ev) => ev.stopPropagation());

      const countSpan = document.createElement("span");
      countSpan.className = "group-count";
      const count = state.items.filter((it) => it.groupId === g.id).length;
      countSpan.textContent = `(${count})`;

      const delBtn = document.createElement("button");
      delBtn.className = "group-del";
      delBtn.textContent = "×";
      delBtn.title = "グループ削除（所属項目は未分類へ）";
      delBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        deleteGroup(g.id);
      });

      row.append(nameInput, countSpan, delBtn);
      row.addEventListener("click", () => selectGroup(g.id));

      row.addEventListener("dragstart", (ev) => {
        ev.dataTransfer.setData("text/plain", "group:" + g.id);
        ev.dataTransfer.effectAllowed = "move";
      });
      row.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        row.classList.add("drag-over");
      });
      row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
      row.addEventListener("drop", (ev) => {
        ev.preventDefault();
        row.classList.remove("drag-over");
        const data = ev.dataTransfer.getData("text/plain");
        if (data.startsWith("group:")) {
          const fromId = data.slice("group:".length);
          if (fromId !== g.id) reorderGroup(fromId, g.id);
        }
      });

      groupListEl.appendChild(row);
    });

    const addBtn = document.createElement("button");
    addBtn.className = "group-add";
    addBtn.textContent = "+ グループを追加";
    addBtn.addEventListener("click", addGroup);
    groupListEl.appendChild(addBtn);
  }

  function renderList() {
    const state = store.get();
    listEl.innerHTML = "";

    const unplaced = state.items.filter((it) => !it.selector);
    if (unplaced.length > 0) {
      const header = document.createElement("div");
      header.className = "list-section-header";
      header.textContent = `未配置項目 (${unplaced.length}) — クリックして選択し、デザインHTML上でホバー+Enterで配置`;
      listEl.appendChild(header);
      unplaced.forEach((it) => {
        const allIdx = indexOfItem(state, it.id);
        const row = document.createElement("div");
        row.className = "list-row unplaced";
        if (it.id === state.selectedId) row.classList.add("selected");
        const noCell = document.createElement("span");
        noCell.className = "cell-no";
        noCell.textContent = String(allIdx + 1);
        const nameCell = document.createElement("span");
        nameCell.className = "cell-name";
        nameCell.textContent = it.name || "(未入力)";
        const kindCell = document.createElement("span");
        kindCell.className = "cell-kind";
        kindCell.textContent = it.kind || "";
        const delBtn = document.createElement("button");
        delBtn.className = "cell-del";
        delBtn.textContent = "×";
        delBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          deleteItem(it.id);
        });
        row.append(noCell, nameCell, kindCell, delBtn);
        row.addEventListener("click", () => selectItem(it.id));
        listEl.appendChild(row);
      });
    }

    const groupId = state.selectedGroupId;
    const items = state.items.filter((it) => it.groupId === groupId && it.selector);
    if (items.length === 0 && unplaced.length === 0) {
      const empty = document.createElement("div");
      empty.className = "list-empty";
      empty.textContent = "このグループには項目がありません";
      listEl.appendChild(empty);
      return;
    }
    if (items.length === 0) return;

    if (unplaced.length > 0) {
      const header = document.createElement("div");
      header.className = "list-section-header";
      header.textContent = "配置済み";
      listEl.appendChild(header);
    }

    items.forEach((it) => {
      const allIdx = indexOfItem(state, it.id);
      const row = document.createElement("div");
      row.className = "list-row";
      if (it.id === state.selectedId) row.classList.add("selected");
      row.draggable = true;
      row.dataset.id = it.id;

      const noCell = document.createElement("span");
      noCell.className = "cell-no";
      noCell.textContent = String(allIdx + 1);
      const nameCell = document.createElement("span");
      nameCell.className = "cell-name";
      nameCell.textContent = it.name || "(未入力)";
      const kindCell = document.createElement("span");
      kindCell.className = "cell-kind";
      kindCell.textContent = it.kind || "";
      const delBtn = document.createElement("button");
      delBtn.className = "cell-del";
      delBtn.textContent = "×";
      delBtn.title = "削除";
      delBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        deleteItem(it.id);
      });

      row.append(noCell, nameCell, kindCell, delBtn);
      row.addEventListener("click", () => selectItem(it.id));

      row.addEventListener("dragstart", (ev) => {
        ev.dataTransfer.setData("text/plain", "item:" + it.id);
        ev.dataTransfer.effectAllowed = "move";
      });
      row.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        row.classList.add("drag-over");
      });
      row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
      row.addEventListener("drop", (ev) => {
        ev.preventDefault();
        row.classList.remove("drag-over");
        const data = ev.dataTransfer.getData("text/plain");
        if (data.startsWith("item:")) {
          const fromId = data.slice("item:".length);
          if (fromId !== it.id) reorderItem(fromId, it.id);
        }
      });

      listEl.appendChild(row);
    });
  }

  function buildForm(itemId) {
    formEl.innerHTML = "";
    formInputs = {};
    currentFormItemId = itemId;

    if (!itemId) {
      const empty = document.createElement("div");
      empty.className = "form-empty";
      empty.textContent = "項目を選択してください";
      formEl.appendChild(empty);
      return;
    }

    const header = document.createElement("div");
    header.className = "form-header";
    header.dataset.role = "form-header";
    formEl.appendChild(header);

    for (const f of FIELDS) {
      const wrap = document.createElement("label");
      wrap.className = "form-field";
      const lbl = document.createElement("span");
      lbl.className = "form-label";
      lbl.textContent = f.label;
      wrap.appendChild(lbl);

      let input;
      if (f.type === "textarea") {
        input = document.createElement("textarea");
        input.rows = 2;
      } else if (f.type === "checkbox") {
        input = document.createElement("input");
        input.type = "checkbox";
      } else if (f.type === "kindSelect") {
        input = document.createElement("select");
        for (const k of KIND_OPTIONS) {
          const opt = document.createElement("option");
          opt.value = k;
          opt.textContent = k;
          input.appendChild(opt);
        }
      } else if (f.type === "groupSelect") {
        input = document.createElement("select");
        // options are populated in syncFormValues
      } else {
        input = document.createElement("input");
        input.type = "text";
      }
      input.className = "form-input";
      input.addEventListener("input", () => {
        if (!currentFormItemId) return;
        const value = f.type === "checkbox" ? input.checked : input.value;
        updateItem(currentFormItemId, { [f.key]: value });
      });
      input.addEventListener("change", () => {
        if (!currentFormItemId) return;
        const value = f.type === "checkbox" ? input.checked : input.value;
        updateItem(currentFormItemId, { [f.key]: value });
      });
      formInputs[f.key] = input;
      wrap.appendChild(input);
      formEl.appendChild(wrap);
    }
  }

  function syncFormValues() {
    const state = store.get();
    const item = state.items.find((x) => x.id === currentFormItemId);
    if (!item) return;
    const idx = indexOfItem(state, item.id);
    const header = formEl.querySelector('[data-role="form-header"]');
    if (header) header.textContent = `No. ${idx + 1}`;

    for (const f of FIELDS) {
      const input = formInputs[f.key];
      if (!input) continue;

      if (f.type === "groupSelect") {
        rebuildGroupOptions(input, state, item.groupId);
        if (document.activeElement !== input) {
          if (input.value !== (item.groupId || "")) input.value = item.groupId || "";
        }
        continue;
      }

      if (document.activeElement === input) continue;
      const value = item[f.key];
      if (f.type === "checkbox") {
        const next = !!value;
        if (input.checked !== next) input.checked = next;
      } else {
        const next = value == null ? "" : String(value);
        if (input.value !== next) input.value = next;
      }
    }
  }

  function rebuildGroupOptions(select, state, currentGroupId) {
    const wantedIds = state.groups.map((g) => g.id);
    const existingIds = Array.from(select.options).map((o) => o.value);
    const sameOrder =
      existingIds.length === wantedIds.length &&
      existingIds.every((id, i) => id === wantedIds[i]);
    if (sameOrder) {
      Array.from(select.options).forEach((opt, i) => {
        const g = state.groups[i];
        const label = g.name || "(無名)";
        if (opt.textContent !== label) opt.textContent = label;
      });
      return;
    }
    select.innerHTML = "";
    state.groups.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = g.id;
      opt.textContent = g.name || "(無名)";
      select.appendChild(opt);
    });
    if (currentGroupId) select.value = currentGroupId;
  }

  function renderForm() {
    const state = store.get();
    const targetId = state.selectedId;
    if (targetId !== currentFormItemId) {
      buildForm(targetId);
    }
    if (targetId) syncFormValues();
  }

  function selectGroup(id) {
    store.set((s) => ({ ...s, selectedGroupId: id }));
  }

  function selectItem(id) {
    const state = store.get();
    const item = state.items.find((x) => x.id === id);
    const patch = { selectedId: id };
    if (item && item.groupId) patch.selectedGroupId = item.groupId;
    store.set((s) => ({ ...s, ...patch }));
    scrollIframeTo(id);
  }

  function addGroup() {
    const g = makeGroup("");
    store.set((s) => ({ ...s, groups: [...s.groups, g], selectedGroupId: g.id }));
  }

  function renameGroup(id, name) {
    store.set((s) => ({
      ...s,
      groups: s.groups.map((g) => (g.id === id ? { ...g, name } : g)),
    }));
  }

  function deleteGroup(id) {
    const state = store.get();
    if (state.groups.length <= 1) {
      alert("最後のグループは削除できません");
      return;
    }
    const fallback = state.groups.find((g) => g.id !== id)?.id || null;
    store.set((s) => ({
      ...s,
      groups: s.groups.filter((g) => g.id !== id),
      items: s.items.map((it) => (it.groupId === id ? { ...it, groupId: fallback } : it)),
      selectedGroupId: s.selectedGroupId === id ? fallback : s.selectedGroupId,
    }));
  }

  function reorderGroup(fromId, toId) {
    store.set((s) => {
      const groups = s.groups.slice();
      const fromIdx = groups.findIndex((g) => g.id === fromId);
      const toIdx = groups.findIndex((g) => g.id === toId);
      if (fromIdx < 0 || toIdx < 0) return s;
      const [moved] = groups.splice(fromIdx, 1);
      groups.splice(toIdx, 0, moved);
      return { ...s, groups };
    });
  }

  function deleteItem(id) {
    store.set((s) => ({
      ...s,
      items: s.items.filter((x) => x.id !== id),
      selectedId: s.selectedId === id ? null : s.selectedId,
    }));
  }

  function updateItem(id, patch) {
    store.set((s) => ({
      ...s,
      items: s.items.map((x) => (x.id === id ? { ...x, ...patch } : x)),
    }));
  }

  function reorderItem(fromId, toId) {
    store.set((s) => {
      const items = s.items.slice();
      const fromIdx = items.findIndex((x) => x.id === fromId);
      const toIdx = items.findIndex((x) => x.id === toId);
      if (fromIdx < 0 || toIdx < 0) return s;
      const [moved] = items.splice(fromIdx, 1);
      items.splice(toIdx, 0, moved);
      return { ...s, items };
    });
  }

  function scrollIframeTo(id) {
    const state = store.get();
    const item = state.items.find((x) => x.id === id);
    if (!item || !iframe.contentDocument) return;
    const el = resolveSelector(iframe.contentDocument, item.selector);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  store.subscribe(() => {
    renderGroupList();
    renderList();
    renderForm();
  });

  renderGroupList();
  renderList();
  renderForm();
}
