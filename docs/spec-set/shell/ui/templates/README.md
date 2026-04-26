# UI テンプレート

Shell の UI（画面・帳票・メール）の項目を埋めるためのテンプレート群です。各テンプレートは Traditional SI 設計書の項目構造（Nablarch開発標準§3.4.4 画面取引・§6 画面・§7 帳票・§8 メール）を下敷きにし、現代の業務システム実装で必要な項目（デバイス別レイアウト、i18n、レスポンシブ対応）を加えています。

## テンプレート一覧

### 画面

- [screen.md](screen.md) — 画面1件のテンプレート（画面項目グループ、画面項目、画面イベント、レイアウトバリアント）
- [screen-catalog.md](screen-catalog.md) — 画面一覧（カタログ）のテンプレート
- [screen-transitions.md](screen-transitions.md) — 画面遷移のテンプレート

### 帳票

- [report.md](report.md) — 帳票1件のテンプレート（用紙仕様、項目グループ、帳票項目）
- [report-catalog.md](report-catalog.md) — 帳票一覧のテンプレート

### メール

- [mail.md](mail.md) — メール1件のテンプレート（件名、差出人、送信先、本文、埋め込み文字列定義）
- [mail-catalog.md](mail-catalog.md) — メール一覧のテンプレート

## 使い方

1. 該当するテンプレートを `shell/ui/<種別>/<id>.md` の場所にコピーします
2. Front matter の `id`、`name`、`status`、`last-reviewed` を埋めます
3. 各項目テーブルの「派生元」列を必ず埋めます（Core の `data` のどの属性から派生するか）
4. Core にない項目を発明しないこと。発明したくなったら、それは Core に追加すべき業務概念です

## 派生元の書き方

「派生元」列には、Core の `data` のどの属性から派生するかを明示します。

```text
| 項目名     | 派生元                              | 編集仕様              |
| ---------- | ----------------------------------- | --------------------- |
| 注文番号   | 承認済み注文.注文番号               | ORD-{yyyy}-{nnnn}形式 |
| 顧客名     | 承認済み注文.顧客.氏名              | 全角50文字超は省略    |
| 配送料     | sum(承認済み注文.明細.配送料)       | #,##0 円              |
```

- 単純な属性参照: `<data 名>.<属性名>` の形式
- 集計: `sum(...)`、`count(...)` のように関数として明示
- 外部リソース呼び出し: `<サービス名>.<メソッド名>(<引数>)` の形式

派生元のない項目が出てきたら、それは Core の `data` に追加すべき業務概念です。Shell に閉じた項目発明は、画面駆動・配線プログラミングの再生産になります。

## Traditional SI 設計書との対応

このテンプレート群は、Nablarch 開発標準の次の設計書を素材にしています。

| Spec Set のテンプレート     | Traditional SI 設計書                       |
| --------------------------- | ------------------------------------------- |
| screen.md                   | §3.4.4 画面取引設計書（画面詳細）          |
| screen-catalog.md           | §6 画面一覧                                 |
| screen-transitions.md       | §6 画面遷移図                               |
| report.md                   | §7 帳票設計書                               |
| report-catalog.md           | §7 帳票一覧                                 |
| mail.md                     | §8 メール設計書                             |
| mail-catalog.md             | §8 メール一覧                               |

ただし次は Spec Set には含めません。コードと冗長な項目を文書から除外する方針に従っています。

- 画面項目名_物理（Form/Entity フィールド名と完全一致）
- 画面引継ぎ項目（session/request scope のキー名）
- 画面イベント詳細のバリデーション処理一覧（コードのバリデータ実装と冗長）
- 帳票_カメラ用シート（印刷不要原本）

## 参照

- [../README.md](../README.md): UI への変換規約
- [../../../examples/business-trip/shell/ui/business-trip-detail-screen.md](../../../examples/business-trip/shell/ui/business-trip-detail-screen.md): 画面テンプレートを使ったサンプル
