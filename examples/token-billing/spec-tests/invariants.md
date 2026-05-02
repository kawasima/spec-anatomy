---
name: トークン課金 不変条件テスト
description: data の不変条件を性質として検証する
status: approved
last-reviewed: 2026-05-02
---

# トークン課金 不変条件テスト

[仕様モデル](../spec-model/token-billing.md) の `data` 定義に書かれた不変条件を、性質ベースで検証します。

## 値オブジェクトの不変条件

```text
[I-01] トークン数 ≥ 0
  ∀ tokens. tokens は トークン数 ⇒ tokens ≥ 0
  検証: -1, -100 を入力したら data 構築が失敗する

[I-02] 金額 ≥ 0、USD 2桁精度
  ∀ amount. amount は 金額 ⇒ amount ≥ 0 AND amount × 100 が整数
  検証: -0.01, 0.001 のような値で構築が失敗する

[I-03] 月の月番号 ∈ [1, 12]
  ∀ m. m は 月 ⇒ 1 ≤ m.月番号 ≤ 12
  検証: 月番号 0, 13 で構築が失敗する
```

## 集約の不変条件

### 料金プラン

```text
[I-04] 月間含み枠 ≥ 0
[I-05] 超過レート ≥ 0
```

`monthly_quota = 0` のプラン（T-08 のケース）は型として有効です。「無料枠ゼロ・全部超過レート課金」のプランを表現できます。

### サブスクリプション

```text
[I-06] 終了日 = NULL OR 開始日 ≤ 終了日
  終了日が NULL なら無期限。
  検証: 開始日 = 2026-03-01, 終了日 = 2026-02-01 で構築が失敗する
```

### 申告トークン

```text
[I-07] プロンプトトークン数 ≥ 0 AND 補完トークン数 ≥ 0
  両方とも 0 は有効（API としては意味がないが、型としては許す）
  検証: -1 のいずれかで構築が失敗する
```

### 枠内請求

```text
[I-08] 枠内消費トークン数 = 申告.プロンプト + 申告.補完
  枠内請求では超過がないため、申告した合計がそのまま枠内消費になる
  これは型定義から導かれるので、構築時に等式が崩れていれば構築失敗
```

### 超過込み請求

```text
[I-09] 超過トークン数 ≥ 1
  超過込み請求の意味は「超過がある」こと。0 になるのは枠内請求の領分
  検証: 超過 = 0 で構築すると失敗する

[I-10] 枠内消費 + 超過 = 申告.プロンプト + 申告.補完
  申告した合計トークンは、枠内消費と超過の和に等しい

[I-11] 請求額 = round_half_up((超過 / 1000) × 適用超過レート, 2)
  計算式に従い、計算結果と一致する
  検証: 任意の超過・レートに対して計算結果が一致する
```

## 永続層との整合（[../shell/persistence/token-billing-table.md](../shell/persistence/token-billing-table.md) と連動）

DB の CHECK 制約は Core の不変条件をミラーします。

| Core の不変条件          | 対応する DB 制約                              |
| ------------------------ | ---------------------------------------------- |
| I-04, I-05               | `chk_quota_nonneg`, `chk_rate_nonneg`         |
| I-06                     | `chk_effective_range`                         |
| I-07                     | `chk_tokens_nonneg`                           |
| I-08, I-09, I-10         | `chk_total_tokens`, `chk_token_split`         |
| 枠内請求 vs 超過込み請求 | `chk_overage_consistency`                     |

DB と Core の両方が同じ不変条件を持つことで、片方を経由してデータが入っても整合が崩れません。Mapper の `toEntity` は `chk_overage_consistency` をすり抜けたデータがあれば Mapping エラーで弾きます。

## property-based test として書ける性質

```text
∀ (当月消費, 料金プラン, 申告).
  let 結果 = 請求を計算する(当月消費, 料金プラン, 申告) in
    [I-08 / I-10] 結果.枠内消費 + 結果.超過 = 申告.プロンプト + 申告.補完
    [I-04 連動]   結果.枠内消費 ≤ 料金プラン.月間含み枠
    [型分割]      (結果が枠内請求 ⇔ 結果.超過 = 0)
    [I-11]        結果が超過込み請求 ⇒
                  結果.請求額 = round_half_up((結果.超過 / 1000) × 結果.適用超過レート, 2)
```

## 関連

- 仕様モデル: [../spec-model/token-billing.md](../spec-model/token-billing.md)
- 全域性: [totality.md](totality.md)
- 不変条件の規約: [../../../reference/spec-set/spec-tests/invariants/](../../../reference/spec-set/spec-tests/invariants/)
