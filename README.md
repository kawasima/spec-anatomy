# Spec Anatomy

## このリポジトリについて

仕様（Spec）とは、システムに対する知識の集合体であり、それをエンコードしてプログラムになる。

エンコードを人間ではなくAIが担う時代になって、「では仕様に何を書くか」が問い直されている。Spec-Driven Development（SDD）の立場は明快で、AIに良いプログラムを出させるには、エンコード前に仕様へ全知識を書ききって与える必要があるというものになる。

これに対しKent Beckは、エンコードせずに全知識を書き出せるものか? と疑義を呈する。そこでサイクルとフィードバックループをSDDに組み込む、Structured Prompt-Driven Development（SPDD）なるものも提唱されている。

が、そもそもの「仕様」に対する解像度が低いままであるし、システムの全知識をMarkdownに書ける由もなし。([ソフトウェア唯識論](https://zenn.dev/kawasima/books/software-yogacara)参照)

そこで

1. 仕様駆動開発で「仕様」として考えていそうなものと、従来のSIerで仕様として書いていたものとをまず突き合わせを行う。
2. 両者ともに欠けているものを洗い出す。
3. 開発プロセスから見直し、コーディングエージェント時代の高い解像度での「仕様」を定義する。

を考えるのが本リポジトリの目的である。

## 構成

このリポジトリはツール本体（ビューア + oppsett）と、それに同梱する規約集・サンプルから成ります。利用者は将来的にパッケージとしてインストールして自分のプロジェクトの `docs/` を可視化・編集する想定です。

- [sdd.md](sdd.md): Living Documentation／Spec-Driven Development の世界観の整理（現状分析）
- [sdd-vs-traditional-design-docs.md](sdd-vs-traditional-design-docs.md): Traditional SI設計書と sdd の突き合わせ（現状分析）
- [examples/](examples/): Spec Setの適用例。開発時の動作確認にも使う
  - [examples/business-trip/](examples/business-trip/): 出張申請（本リポジトリの標準サンプル。`docs/` から移動）
    - `spec-model/`: Core（仕様DSL：data と behavior）
    - `shell/`: Shell（API・永続・UI・メッセージング）
    - `ai-collaboration/`: エージェント協業のプロンプト集
  - [examples/token-billing/](examples/token-billing/): トークン課金システム（[gszhangwei/token-billing](https://github.com/gszhangwei/token-billing) を題材に）
    - `spec-model/`: 仕様モデル（`data 請求 = 枠内請求 OR 超過込み請求` など）
    - `shell/api/`, `shell/persistence/`: Shell 仕様
    - `spec-tests/`: 全域性・不変条件
    - `ai-collaboration/`: source-material.md、3フェーズのプロンプト、generated/（生成コード）、evaluation.md
- [reference/](reference/): 同梱資料（規約・テンプレート・参考サンプル）
  - [reference/spec-set/](reference/spec-set/): Spec Set 規約本体（Core/Shell/Spec Tests/AI Collaboration/ADR の書き方）
- [tools/](tools/): Spec Set を書くための支援ツール
  - [tools/oppsett/](tools/oppsett/): デザインHTMLから screen.md（画面項目表）を生成するインタラクティブツール
- [viewer/](viewer/): ドキュメントビューア（Vite + marked）
- [traditional-design-schema.dsl](traditional-design-schema.dsl): Traditional SI 設計書（Nablarch開発標準）の構造化DSL

## ローカルでのプレビュー

軽量な Vite + marked のビューア (`viewer/`) でドキュメント全体をレンダリングします。screen.md ではレイアウトHTMLが iframe でインライン表示され、`tools/oppsett/` も同じ dev サーバ経由で起動できます。

```sh
npm install
npm run dev
# http://localhost:5173 で開く
```

screen.md のレイアウト図セクションには「マークアップする」ボタンが付いており、対応するデザインHTMLと screen.md を自動ロードした状態で oppsett が起動します。

## 仕様モデル駆動設計の流れ

仕様モデルを先に書き、実装はそこから派生させる。このリポジトリで想定する開発フロー：

1. **仕様モデルを書く** — `examples/<project>/spec-model/` に `data` と `behavior`
2. **画面/API/永続の規約に沿って Shell を書く** — `examples/<project>/shell/` （oppsett を使うと楽）
3. **エージェントに Core 実装を生成させる** — [examples/business-trip/ai-collaboration/core-generation-prompt.md](examples/business-trip/ai-collaboration/core-generation-prompt.md)
4. **エージェントに Shell 実装を生成させる** — [examples/business-trip/ai-collaboration/shell-generation-prompt.md](examples/business-trip/ai-collaboration/shell-generation-prompt.md)
5. **仕様テストで検証** — 仕様テストの軸は規約 [reference/spec-set/spec-tests/](reference/spec-set/spec-tests/) を参照（具体ツールは別リポジトリ specifico との統合で扱う予定）

既存システムから始める場合は [examples/business-trip/ai-collaboration/refactoring-prompt.md](examples/business-trip/ai-collaboration/refactoring-prompt.md) で仕様モデルを抽出。

## AI協業評価（token-billing サンプル）

[examples/token-billing/ai-collaboration/evaluation.md](examples/token-billing/ai-collaboration/evaluation.md) は、3フェーズのプロンプト（refactoring → core-generation → shell-generation）を実際に走らせた結果の評価記録だ。ソースは [gszhangwei/token-billing](https://github.com/gszhangwei/token-billing) の要件定義書とDDLのみ（本リポジトリのSpec Setは入力に含めていない）。

評価で確認できた主な点：

- refactoring-prompt は `当月の枠消費状況 = 枠未消費 OR 枠一部消費 OR 枠使い切り` という3状態モデルを提案した。元のソースは `remaining_tokens` 列の数値で状態を判断する設計だったが、生成されたモデルはその状態を型として分離している
- core-generation-prompt は Java の sealed interface + record で `Bill = InQuota | WithOverage` を生成した。overage_tokens = 0 のセンチネル値パターンには戻っていない
- shell-generation-prompt は Raoh の `Decoder`/`Encoder` パターンに沿って Controller → Service → Repository の薄い連鎖を生成し、`BillEncoder` で InQuota レスポンスから charge フィールドを構造的に除外した

## Spec Setの判断基準

何を Spec Set に含めるかの判断基準は「**コーディングエージェントに伝えないと実装できないか**」の一点です。エージェントに渡せばエージェントが補える情報、コードや既存ライブラリから推論できる情報、運用記録に置き換えられる情報は、Spec Setに含めません。

詳細は [reference/spec-set/](reference/spec-set/) を参照してください。
