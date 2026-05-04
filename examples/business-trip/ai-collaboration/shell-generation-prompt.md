---
name: Shell 生成プロンプト（出張申請）
description: Core を呼び出す Shell（API・永続・UI）をエージェントに生成させる Policy & Discretion プロンプト
status: approved
last-reviewed: 2026-04-28
---

# Shell 生成プロンプト（出張申請）

[../shell/](../shell/) の規約に従い、エージェントに **API・永続・UI を含む Shell の実装** を生成させる完成形プロンプトです。Core 側は Strict Spec で曖昧さゼロに渡しますが、Shell は **Policy & Discretion** で「方針は明示するが選択は委ねる」スタイルで進めます。

規約は [../../reference/spec-set/ai-collaboration/shell-generation.md](../../reference/spec-set/ai-collaboration/shell-generation.md) を参照。

## このプロンプトを使う場面

- Core 実装ができたので、その上の API/永続/UI を生成したい
- Shell の一部だけ作り直したい（API 層だけ、Repository だけ、画面だけ）
- 別フレームワーク（Express → Hono → NestJS）に置き換えたい

## プロンプトは3パートで構成

Shell は領域が広いので、1つのプロンプトでまとめずに、層別に分けます。

1. **永続層（Repository）** — Core の data を DB に出し入れ
2. **API 層** — Core の behavior を HTTP エンドポイントに公開
3. **UI 層** — 画面項目テーブルから React コンポーネントを生成

各パートは Core を **不変前提** とし、Core の型を直接 import して使います。

---

## パート 1: 永続層（Repository）の生成

````text
あなたは仕様モデル駆動設計（SMDD）の Shell 実装エージェントです。
次の Core 型定義に対応する Repository（永続層）を実装してください。

## Core の型定義（不変）

[エージェントが先に生成した Core の型定義ファイルの内容を貼り付け]

## 永続規約（このプロジェクトの方針）

[../shell/persistence/business-trip-table.md の内容を貼り付け]

このプロジェクトでは Data Mapper パターンを採用しています。
永続モデルとドメインモデルを別の型として持ち、Mapper で双方向に変換します。

## 実装方針（Policy）

- 言語: TypeScript
- DB: PostgreSQL（pg ライブラリを使用）
- マイグレーション: drizzle-kit または sql ファイル直書きのどちらでも可
- トランザクション境界: Repository.save の単位
- 関連の永続化:
  - 出張申請 ⇔ 予定費用 / 実績費用: 単方向 + Eager Load + 差分検出
  - 出張申請 → 申請者 / 承認者: ID参照のみ

## 制約

- Core の型は一切変更しない
- Mapper のエラーは Result 型 (`{ kind: 'Err', error: ... }`) で返す（例外を投げない）
- SQL は Repository の中だけに書く（呼び出し側に漏らさない）
- Repository インターフェースは [../shell/persistence/business-trip-table.md](../shell/persistence/business-trip-table.md) のセクション「Repository インターフェース」のとおり

## 裁量（Discretion）

次は実装者の判断で選んでよい：
- ORM を使うか生 SQL か
- 採番方式（連番 / UUID / ULID）
- インデックス設計の具体的なカラム
- マイグレーションファイルの分割粒度
- テストデータの fixtures 形式

ただし、選択した理由は ADR として `docs/adrs/ADR-XXX-{title}.md` に書き残してください。

## 成果物

1. **`shell/persistence/business-trip-record.ts`** — 永続モデルの型
2. **`shell/persistence/business-trip-mapper.ts`** — Core <-> 永続モデルの双方向変換
3. **`shell/persistence/business-trip-repository.ts`** — Repository 実装
4. **`shell/persistence/migrations/XXXX-create-business-trips.sql`** — マイグレーション

## 検証

- `tsc --noEmit` で型エラーなし
- Mapper の往復テスト（Core → 永続 → Core で同値）が通る
- Repository の主要メソッド（findById、save）に統合テストを書く（実 DB に接続する）
````

---

## パート 2: API 層の生成

````text
あなたは Shell の API 層実装エージェントです。
次の Core の behavior を HTTP API として公開する Express ハンドラを実装してください。

## Core の behavior 定義

[エージェントが先に生成した Core の behavior 実装ファイルの内容を貼り付け]

## API 規約

[../shell/api/business-trip-api.md の内容を貼り付け]

## 実装方針（Policy）

- フレームワーク: Express
- 認証: JWT（Bearer Token）。`req.user.employeeId` でログイン社員番号を取得
- 認可: ロールに応じて `req.user.role` で判定
- バリデーション: zod スキーマで境界での型変換
- エラーハンドリング:
  - Core の Result の Err 枝 → HTTP ステータスにマッピング
    - 検証エラー → 400
    - 権限エラー → 403
    - 状態不整合 → 409
    - NotFound → 404
- ロギング: pino 構造化ログ

## エンドポイントと behavior の対応

[../shell/api/business-trip-api.md の表を貼り付け]

## 制約

- Core の関数を呼び出す形でエンドポイントを実装する（業務ロジックを Shell に書かない）
- 業務ロジックが必要になったら Core に戻る（refactoring プロンプトを使う）
- 永続化は Repository に委譲する（Core / API 層では SQL を書かない）

## 裁量（Discretion）

- リクエストパースの構造（zod の組み立て方）
- エラーレスポンスの JSON 構造の細部（規約に書かれていない部分）
- ロギングの詳細レベル
- レート制限の有無

## 成果物

1. **`shell/api/business-trip-router.ts`** — Express ルーター
2. **`shell/api/business-trip-schemas.ts`** — リクエスト/レスポンスの zod スキーマ
3. **`shell/api/error-mapper.ts`** — Core の Err → HTTP ステータスマッピング

## 検証

- `tsc --noEmit` で型エラーなし
- 契約テスト（supertest）で各エンドポイントの正常系・異常系を網羅
- API 仕様書（OpenAPI）と実装の整合性チェック
````

---

## パート 3: UI 層の生成

````text
あなたは Shell の UI 層実装エージェントです。
次の screen.md から React コンポーネントを実装してください。

## screen.md（画面設計）

[対象の screen.md ファイルの内容を貼り付け、例: docs/shell/ui/business-trip-detail-screen.md]

## Core の関連型

[エージェントが先に生成した Core の型定義ファイルから、対象画面が扱う型のみ貼り付け]

## UI 規約

[../../reference/spec-set/shell/ui/README.md の内容を貼り付け]

## 実装方針（Policy）

- フレームワーク: React 19
- ビルド: Vite
- スタイル: Tailwind CSS
- 状態管理: TanStack Query（API 呼び出し）+ react-hook-form（フォーム）
- レスポンシブ: CSS メディアクエリで PC/スマホ切り替え（screen.md のレイアウトバリアントに従う）
- ルーティング: React Router

## 画面項目テーブルの解釈

screen.md の画面項目テーブルの各列を次のとおり解釈してください：

| 列 | 解釈 |
|---|---|
| No | レイアウトPNGと対応する番号。コンポーネント内でコメントとして残す |
| 項目名 | コンポーネントの semantic な名前 |
| 種別 | label/text/textarea/select_pulldown/radio/checkbox/button/link 等 |
| 派生元 | Core の data 属性。「`<data名>.<属性>`」形式 |
| 編集仕様 | フォーマット指定（yyyy/MM/dd など）、入力制約（1〜500文字 など） |
| 必須 | フォーム要素の required 属性 |
| 初期値 | 新規作成時のデフォルト値 |
| 表示条件 | `role >= MANAGER` などの動的制御。条件式として実装 |

## 制約

- 画面項目を「派生元」なしで作らない（Core にない項目を画面で発明しない）
- 派生計算（`sum(...)`）は明示的にコンポーネント内に純粋関数として書く
- 画面イベントは Core の behavior 1つを呼び出す形にする
  （複数 behavior の連結は Core 側に workflow として戻す）

## 裁量（Discretion）

- コンポーネントの分割粒度
- ローディング表示の見た目
- バリデーションエラーの見せ方
- アニメーション

## 成果物

1. **`shell/ui/screens/<ScreenName>.tsx`** — 画面コンポーネント
2. **`shell/ui/screens/<ScreenName>.spec.tsx`** — Storybook ストーリー（または Vitest コンポーネントテスト）
3. **`shell/ui/api-client.ts`** — API 呼び出しの薄いラッパ

## 検証

- `tsc --noEmit` で型エラーなし
- Storybook で各バリアント（PC/スマホ、状態×ロール）が表示できる
- E2E テスト（Playwright）で screen.md の「受け入れ基準」テーブルを網羅
````

---

## 全パート共通の検証ループ

各パートを生成したら、次のループを回します：

1. 型検査（TypeScript なら `tsc --noEmit`）で型エラーチェック
2. 仕様テストで Core が壊れていないか確認（Core が変わらないので、ここで赤くなったら Shell が Core を間違って使っている）
3. パート別のテスト
   - 永続: Mapper の往復テスト + Repository 統合テスト
   - API: 契約テスト
   - UI: Storybook + E2E
4. 失敗があれば、エラーメッセージとファイル全文をエージェントに返して修正させる
5. 仕様の問題なら Core / 仕様モデルに戻る（Shell で吸収しない）

## Policy & Discretion の境界

| 領域 | Strict Spec（曖昧さゼロ） | Policy & Discretion |
|---|---|---|
| Core の型 | ★ | |
| Core の behavior | ★ | |
| 永続テーブル定義 | ★ | |
| API パスとメソッド | ★ | |
| API のリクエスト/レスポンス JSON 構造 | ★ | |
| 画面項目（派生元、編集仕様） | ★ | |
| 永続実装の ORM 選択 | | ★ |
| マイグレーションの分割 | | ★ |
| エラーレスポンスの細部 | | ★ |
| UI のレイアウト詳細 | | ★ |
| ローディング・アニメーション | | ★ |

★が左にあるものは仕様モデル / 規約で曖昧さなく決める。右にあるものはエージェントの裁量で選び、選択理由を ADR に残す。

## 参照

- [../../reference/spec-set/ai-collaboration/shell-generation.md](../../reference/spec-set/ai-collaboration/shell-generation.md)
- [core-generation-prompt.md](core-generation-prompt.md): Core 生成へ
