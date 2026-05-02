# ADR-001: JdbcClient + 手動マッピングを採用、JPAは使わない

## ステータス

採用（2026-05-02）

## 背景

token-billing の Shell 層には、永続化のために主に2つの選択肢がある。

1. Spring Data JPA + Hibernate
2. Spring の `JdbcClient` + Raoh の Map デコーダによる手動マッピング

元の token-billing 雛形（`/Users/kawasima/workspace/token-billing/build.gradle`）は前者で、`spring-boot-starter-data-jpa` が依存に含まれていた。

## 決定

JPA を使わない。`JdbcClient` を使い、`Map<String, Object>` の行を Raoh の `combine + field` で Core の record（`Bill`, `Customer`, …）へデコードする。

## 理由

- Core の `Bill` は `sealed interface` で `InQuota | WithOverage` の二分割。これに `@Entity` を付けると、JPA は単一クラスにフィールドを統合した「貧血ドメインモデル」を要求する。`@Inheritance(SINGLE_TABLE)` の discriminator まで持ち込めば近いことはできるが、Core の record は不変前提なので JPA の dirty-check 機構と相性が悪い。
- Core の record は `org.tw.token_billing.core` パッケージにあり、Spring/JPA への依存を持たない。JPA を使うと、永続化のために Core を改変するか、Shell 側に対応する `BillEntity` などを置いてマッピングする手間が必要になる。Raoh のデコーダはマッピングの責務を Shell に閉じ込めるため、Core を不変のまま保てる。
- spec-model 由来の不変条件（`総トークン数 = 枠消費 + 超過`、`InQuota では 超過 = 0 かつ rate/charge IS NULL`）は SQL の CHECK 制約で表現する。JPA を経由すると CHECK の存在を Java 側に二重に書くことになりがちで、Source of Truth が分散する。
- 1テーブルあたりの SELECT/INSERT 1〜2種類しか必要ない。JPA の Repository 抽象が払う追加複雑性に見合うほどクエリは多くない。

## 影響

- `bills.kind` を switch する箇所が `PgBillHistoryRepository#save` の1か所に集中する（INSERT 文の分岐）。READ 側は `MapBillDecoders.BILL_ROW` の1か所に集中する。
- スキーマ変更時は SQL → デコーダ → エンコーダの順で人手で同期する。JPA のような「フィールド追加で自動」は得られない。spec-model の変更頻度に対して問題ない見込み。
- Hibernate 由来の N+1 や lazy load に起因する調査が発生しない。
