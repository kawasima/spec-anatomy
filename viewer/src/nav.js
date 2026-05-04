// サイドバー構造の定義。
//
// このリポジトリは「Spec Anatomy ツール本体（ビューア + oppsett）+ 同梱資料（規約集とサンプル）」
// として位置付けています。実プロジェクトでは利用者が examples/ 配下に自分の仕様を書き、
// 同梱の reference/ を参照しながら作業します。
//
// サイドバーの上から下へ：
//   1. サンプル (= examples/)                      — 出張申請 / トークン課金
//   2. 参考: 規約 (= reference/spec-set/)          — 同梱の規約集
//   3. ツール (= tools/oppsett/)
//   4. このリポジトリについて                      — メタ情報

export const NAV = [
  {
    text: "サンプル: 出張申請",
    items: [
      { text: "概要", path: "examples/business-trip/README.md" },
      {
        text: "Core (仕様モデル)",
        items: [
          { text: "出張申請（最終形）", path: "examples/business-trip/spec-model/business-trip.md" },
          { text: "出張申請（初期形）", path: "examples/business-trip/spec-model/business-trip-initial.md" },
        ],
      },
      {
        text: "Shell",
        items: [
          { text: "API", path: "examples/business-trip/shell/api/business-trip-api.md" },
          { text: "永続", path: "examples/business-trip/shell/persistence/business-trip-table.md" },
          { text: "画面一覧", path: "examples/business-trip/shell/ui/screen-catalog.md" },
          { text: "画面遷移", path: "examples/business-trip/shell/ui/screen-transitions.md" },
          { text: "BT-01 出張申請一覧", path: "examples/business-trip/shell/ui/SCREEN-BT-01-business-trip-list.md" },
          { text: "BT-02 詳細(事前承認)", path: "examples/business-trip/shell/ui/business-trip-detail-screen.md" },
          { text: "BT-03 作成・編集", path: "examples/business-trip/shell/ui/SCREEN-BT-03-business-trip-create.md" },
          { text: "BT-04 実績登録", path: "examples/business-trip/shell/ui/SCREEN-BT-04-business-trip-actuals.md" },
          { text: "BT-05 最終承認", path: "examples/business-trip/shell/ui/SCREEN-BT-05-business-trip-final-approve.md" },
        ],
      },
      {
        text: "AI Collaboration プロンプト",
        items: [
          { text: "Refactoring プロンプト", path: "examples/business-trip/ai-collaboration/refactoring-prompt.md" },
          { text: "Core 生成プロンプト", path: "examples/business-trip/ai-collaboration/core-generation-prompt.md" },
          { text: "Shell 生成プロンプト", path: "examples/business-trip/ai-collaboration/shell-generation-prompt.md" },
        ],
      },
    ],
  },
  {
    text: "サンプル: トークン課金",
    items: [
      { text: "概要", path: "examples/token-billing/README.md" },
      {
        text: "Core (仕様モデル)",
        items: [
          { text: "トークン課金", path: "examples/token-billing/spec-model/token-billing.md" },
        ],
      },
      {
        text: "Shell",
        items: [
          { text: "API", path: "examples/token-billing/shell/api/token-billing-api.md" },
          { text: "永続", path: "examples/token-billing/shell/persistence/token-billing-table.md" },
        ],
      },
      {
        text: "Spec Tests",
        items: [
          { text: "全域性", path: "examples/token-billing/spec-tests/totality.md" },
          { text: "不変条件", path: "examples/token-billing/spec-tests/invariants.md" },
        ],
      },
      {
        text: "AI Collaboration",
        items: [
          { text: "評価レポート", path: "examples/token-billing/ai-collaboration/evaluation.md" },
          { text: "ソース素材", path: "examples/token-billing/ai-collaboration/source-material.md" },
        ],
      },
    ],
  },
  {
    text: "参考: 規約 (Spec Set)",
    items: [
      { text: "概要", path: "reference/spec-set/README.md" },
      { text: "設計方針", path: "reference/spec-set/design.md" },
      {
        text: "Core (仕様モデル) の書き方",
        items: [
          { text: "概要", path: "reference/spec-set/spec-model/README.md" },
          { text: "ユビキタス言語", path: "reference/spec-set/spec-model/ubiquitous-language.md" },
          { text: "data の書き方", path: "reference/spec-set/spec-model/data/README.md" },
          { text: "behavior の書き方", path: "reference/spec-set/spec-model/behavior/README.md" },
          { text: "workflow の書き方", path: "reference/spec-set/spec-model/workflow/README.md" },
        ],
      },
      {
        text: "Spec Tests",
        items: [
          { text: "概要", path: "reference/spec-set/spec-tests/README.md" },
          { text: "不変条件", path: "reference/spec-set/spec-tests/invariants/README.md" },
          { text: "全域性", path: "reference/spec-set/spec-tests/totality/README.md" },
          { text: "状態遷移", path: "reference/spec-set/spec-tests/state-transitions/README.md" },
        ],
      },
      {
        text: "Shell",
        items: [
          { text: "概要", path: "reference/spec-set/shell/README.md" },
          { text: "API", path: "reference/spec-set/shell/api/README.md" },
          { text: "永続", path: "reference/spec-set/shell/persistence/README.md" },
          { text: "UI", path: "reference/spec-set/shell/ui/README.md" },
          { text: "メッセージング", path: "reference/spec-set/shell/messaging/README.md" },
        ],
      },
      {
        text: "AI Collaboration",
        items: [
          { text: "概要", path: "reference/spec-set/ai-collaboration/README.md" },
          { text: "Refactoring with Agents", path: "reference/spec-set/ai-collaboration/refactoring-with-agents.md" },
          { text: "Core Generation", path: "reference/spec-set/ai-collaboration/core-generation.md" },
          { text: "Shell Generation", path: "reference/spec-set/ai-collaboration/shell-generation.md" },
          { text: "Verification Loop", path: "reference/spec-set/ai-collaboration/verification-loop.md" },
        ],
      },
      { text: "ADRs", path: "reference/spec-set/adrs/README.md" },
    ],
  },
  {
    text: "ツール",
    items: [
      { text: "oppsett を起動", external: "/tools/oppsett/index.html" },
      { text: "oppsett README", path: "tools/oppsett/README.md" },
    ],
  },
  {
    text: "このリポジトリについて",
    items: [
      { text: "README", path: "README.md" },
      { text: "sdd.md", path: "sdd.md" },
      { text: "sdd-vs-traditional-design-docs.md", path: "sdd-vs-traditional-design-docs.md" },
    ],
  },
];
