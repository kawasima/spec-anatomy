# ADR-002: 適用超過レートを請求記録にスナップショットする

## ステータス

採用（2026-05-02）

## 背景

元素材の `bills` テーブルには `total_charge` 列はあるが、計算に使われた超過レートそのものは保存されない。料金プラン（`pricing_plans.overage_rate_per_1k`）を後から参照すれば再計算できる、という前提だった。

spec-model 側はこれを引き継がず、`超過込み請求` の不変条件として `適用超過レート` フィールドを持つように改めている（refactoring の上位概念A）。

## 決定

`bills.applied_overage_rate_per_1k DECIMAL(10, 4)` 列を追加し、超過込み請求のときだけ NOT NULL（`InQuota` のときは NULL）にする。Core の `Bill.WithOverage` レコードもこの値を保持する。

## 理由

- 料金プランの超過レートは将来変更されうる（顧客との契約改定、価格改定など）。元のスキーマだとレート変更の瞬間に過去の請求の意味が変わってしまう：「2026年4月の請求の `total_charge=$0.60` は、当時のレート $0.02 で計算されたのか、現在のレート $0.025 で計算されたのか」が記録から復元できない。
- 会計上、すでに発行された請求金額は不変であるべき。スナップショットはこの不変性を構造的に保証する手段。
- spec-model の最終形にこの判断が明示されている（`適用超過レート = 計算時点でのスナップショット`）。

## 影響

- `bills` テーブルに1列追加。`InQuota` のときは NULL を入れる。
- Core の `Bill.WithOverage` レコードに `appliedOverageRatePer1K: Money` フィールドを置く（既に Core 側にある）。
- 監査・帳票クエリは `bills.applied_overage_rate_per_1k` を直接読めばよい。`pricing_plans` を JOIN する必要がない。
- 制約上、`InQuota` 行ではこの列が必ず NULL であることを CHECK 制約 `chk_in_quota_shape` で保証する。`InQuota` に偶然レートを書き込んでしまう実装ミスは DB が拒否する。
