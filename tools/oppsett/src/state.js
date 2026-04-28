const DEFAULT_GROUP_NAME = "未分類";

const initialState = () => {
  const defaultGroup = makeGroup(DEFAULT_GROUP_NAME);
  return {
    designHtml: "",
    designHtmlPath: null,
    screenMeta: {
      frontmatter: {},
      rawSections: "",
      layoutVariant: "PC版",
    },
    groups: [defaultGroup],
    items: [],
    selectedId: null,
    selectedGroupId: defaultGroup.id,
    hoverSelector: null,
  };
};

export function createStore() {
  let state = initialState();
  const listeners = new Set();

  const get = () => state;

  const set = (updater) => {
    const next = typeof updater === "function" ? updater(state) : updater;
    state = next;
    for (const fn of listeners) fn(state);
  };

  const subscribe = (fn) => {
    listeners.add(fn);
    return () => listeners.delete(fn);
  };

  return { get, set, subscribe };
}

export function uid() {
  return "id-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

export function makeGroup(name) {
  return { id: uid(), name: name || "" };
}

export function makeItem({ selector, rect, name, kind, groupId }) {
  return {
    id: uid(),
    selector,
    rect,
    groupId: groupId || null,
    name: name || "",
    kind: kind || "",
    source: "",
    editSpec: "",
    required: false,
    defaultValue: "",
    visibleCondition: "",
  };
}

export function indexOfItem(state, id) {
  return state.items.findIndex((it) => it.id === id);
}

export function getOrCreateDefaultGroup(state) {
  if (state.groups.length === 0) {
    const g = makeGroup(DEFAULT_GROUP_NAME);
    return {
      next: { ...state, groups: [g], selectedGroupId: state.selectedGroupId || g.id },
      group: g,
    };
  }
  return { next: state, group: state.groups[0] };
}

export function ensureItemGroup(state, item) {
  if (item.groupId && state.groups.some((g) => g.id === item.groupId)) return state;
  const targetId = state.selectedGroupId || state.groups[0]?.id;
  if (!targetId) return state;
  return {
    ...state,
    items: state.items.map((it) =>
      it.id === item.id ? { ...it, groupId: targetId } : it,
    ),
  };
}
