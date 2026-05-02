---
name: token-billing プロンプト評価
description: 各 AI Collaboration プロンプトを token-billing 元素材に適用した結果と本サンプルとの差分
status: completed
last-reviewed: 2026-05-02
---

# token-billing プロンプト評価

[docs/ai-collaboration/](../../../docs/ai-collaboration/) のプロンプト群を token-billing の元素材だけを入力として実行し、生成された Spec Set と Core/Shell 実装を本サンプル（[../spec-model/](../spec-model/) [../shell/](../shell/) [../spec-tests/](../spec-tests/)）と比較した結果です。

実装言語は **Java 25 + Spring Boot 4** で、Zenn 本『古典ドメインモデルパターンの解脱』で示された **Raoh 0.5.0** によるデコーダ合成パターンに倣っています。元の token-billing リポジトリが Java/Spring Boot 雛形だったことに合わせています。

## 実施手順

各プロンプトは別々のサブエージェントに、以下の制約付きで実行させました:

- 入力素材は明示したファイルだけ（`source-material.md`、前段の生成物、`reference/spec-set/` の規約、Raoh の book 本文と `examples/spring/` のリファレンス実装）
- 本サンプルの正解（`examples/token-billing/spec-model/`、`shell/`、`spec-tests/`、`README.md`）は読まないこと
- `docs/spec-model/business-trip*.md` と `docs/shell/` も書き口を真似てしまうため参照禁止

3つのプロンプトは直列に実行しました（refactoring → core-generation → shell-generation）。前段の出力が次段の入力です。生成物は [generated/](generated/) 配下に保存してあります。

## 評価対象のプロンプト

| プロンプト | 入力素材 | 生成物 |
| --- | --- | --- |
| [refactoring-prompt.md](../../../docs/ai-collaboration/refactoring-prompt.md) | `source-material.md` | `generated/refactoring/spec-model.md` |
| [core-generation-prompt.md](../../../docs/ai-collaboration/core-generation-prompt.md) | 生成された spec-model.md + Raoh examples | `generated/core-generation/` 配下 22 Java ファイル |
| [shell-generation-prompt.md](../../../docs/ai-collaboration/shell-generation-prompt.md) | source-material + spec-model + Core + Raoh examples | `generated/shell-generation/` 配下 18 ファイル（Java 11、SQL 1、ADR 3、Gradle/properties/main 各1） |

## Raoh の流儀をどう適用したか

このサンプルでは、core-generation と shell-generation の両プロンプトに Raoh 本のリファレンス実装（`/Users/kawasima/workspace/raoh/examples/spring/membership/` 配下）を読ませて、その書き口にそのまま倣わせました。本サンプル（TypeScript ベースの自作テンプレート）とは前提が異なるため、評価は「本サンプルとの素直な比較」ではなく「Raoh の流儀がどこまで正しく実装に反映されたか」が主軸になります。

Raoh の流儀の中核:

1. **Always-Valid Layer**: 境界を越えた瞬間からドメイン型のみが流れる
2. **Parse, Don't Validate**: `JsonDecoder<JsonNode, T>` でJSON → ドメイン型を一気に変換。`Form` クラスや `CreateXxxCommand` を作らない
3. **状態は sealed interface + record で分ける**
4. **ドメインモデルは「ただの record」**: `@Entity` `@NotNull` `@Column` を持たせない
5. **JdbcClient + 行デコーダ**: ORM や JPA は使わない。`Map<String, Object>` の SELECT 結果を `MapDecoders` でドメイン型へ
6. **エンコーダ**: ドメイン型 → `Map<String, Object>` を `Encoder` で記述。レスポンス DTO クラスを作らない

## 結果サマリ

### refactoring-prompt（要件文書 → 仕様モデル）

総合評価: **本サンプルと同等以上**。元素材だけを与えて、本サンプルの設計判断のほぼ全てを再現し、加えて本サンプルが採用しなかった上位概念（当月の枠消費状況の3状態化）まで提案してきた。

#### refactoring-prompt の評価軸ごとの確認

| 軸 | 結果 | 詳細 |
| --- | --- | --- |
| 型分割の検出 | ◎ 完全一致 | 「請求 = 枠内請求 OR 超過込み請求」をステップ6 で発見し、整数フラグでの分岐を排除 |
| 抽象概念の命名 | ◎ 一致＋追加 | 「適用料金プラン」（射影型でスタンプ結合排除）「当月の枠消費状況（3状態）」を導入。本サンプルにはない後者の方が踏み込んでいる |
| Why の明示 | ◎ 充実 | AC1/AC2 の業務根拠、「枠を先に消費する」の顧客への約束意義、適用超過レートのスナップショット理由を Why として明示 |
| 不変条件の網羅 | ◎ 完全一致 | `総トークン = プロンプト + 完了` `枠内: 枠消費 = 総` `超過込み: 枠消費 + 超過 = 総, 超過 ≥ 1, 請求金額 > 0` を property として列挙 |
| 暗黙の前提の炙り出し | ○ 部分一致 | 月境界（推測: UTC暦月）、通貨単位（推測: USD）、丸め（推測: round_half_up）を「推測:」と明示 |
| エラーケースの網羅 | ◎ 一致＋追加 | AC1/AC2 に加え「サブスクリプション無効エラー」を独自発見（要件文書には書かれていない） |

#### 本サンプルにない発見: 当月の枠消費状況の3状態化

```text
data 当月の枠消費状況 = 枠未消費 OR 枠一部消費 OR 枠使い切り
```

`max(0, 月間込み枠 - 当月使用済み)` という整数比較で済ませがちな判定を業務状態として型に持ち上げた。本サンプルでは `当月消費` という単一型に留めていたが、生成物の方が SMDD の精神（状態を OR で分ける）により忠実。**本サンプルの spec-model.md を refactoring すべき発見**。

### core-generation-prompt（仕様モデル + Raoh 流儀 → Java/Spring 実装）

総合評価: **Raoh の流儀をそのまま適用した良質な Core 実装**。22 Java ファイルが生成され、`javac --release 21` がクリーンに通ることを生成エージェントが確認している。

#### core-generation-prompt の評価軸ごとの確認

| 軸 | 結果 | 詳細 |
| --- | --- | --- |
| sealed interface + record | ◎ | `Bill = sealed interface { record InQuota, record WithOverage }`、`MonthlyQuotaUsage = sealed interface { record Untouched, record Partial, record Exhausted }` で実装 |
| 状態ごとに必須フィールドが異なる | ◎ | `InQuota` には `overageTokens` `appliedOverageRatePer1K` `totalCharge` を持たせない。共通アクセサのみ interface に定義 |
| ドメインモデルが「ただの record」 | ◎ | `@Entity` `@NotNull` `@Column` 一切なし。Bean Validation も Lombok も使っていない |
| 値オブジェクトの型化 | ◎ | `record CustomerId(String value)` `record TokenAmount(long value)` `record Money(BigDecimal amount, Currency currency)` のように個別型 |
| スタンプ結合の排除 | ◎ | `BillCalculationBehavior.calculate(ValidatedUsageReport, MonthlyQuotaUsage, AppliedPricingPlan, Instant)` の4引数。`Subscription` 全体や `PricingPlan` 全体を渡さず、計算に必要な射影型 `AppliedPricingPlan` だけを受け取る |
| Always-Valid Layer | ◎ | 入力は `ValidatedUsageReport` で「未検証 → 検証済み」のモード遷移を型で表現。Behavior は失敗ケースを返さない（純関数、全域） |
| ports と adapters の分離 | ◎ | `core/port/` 配下に Repository と Clock の interface のみ。`@Repository` などの Spring アノテーションは付けない（Shell 側の責務） |
| 型レベルの不変条件保証 | ◎ | `OverageTokens` を別 record にして「value >= 1」を型で強制。`WithOverage` の compact constructor で `totalCharge > 0` を強制 |

#### Core 側の設計上の補足

- Core 内には Raoh 依存を持ち込まず、純粋 Java のみで完結。Raoh の `Result` を返すのは Shell 側のバリデーション層
- 計算ロジックの Why（1000 で割る理由・枠を先に消費する理由・型分割の理由）が javadoc で明示
- 仕様モデルの DSL コードを `<pre>` で javadoc に埋め込み、コードと仕様モデルの対応を可視化

### shell-generation-prompt（仕様モデル + Core + Raoh 流儀 → Spring Boot 実装）

総合評価: **Raoh の Spring example をそのまま適用した良質な Shell 実装**。controller の薄さ・JdbcClient での行デコーダ・sealed interface を反映した DB 制約まで一貫している。

#### shell-generation-prompt の評価軸ごとの確認

| 軸 | 結果 | 詳細 |
| --- | --- | --- |
| Controller の薄さ | ◎ | `UsageController.reportUsage` は decode → service.process → encode の3段スイッチのみ。業務ロジックなし |
| デコーダ合成 | ◎ | `JsonUsageDecoders.USAGE_REPORT_REQUEST` で JSON → `UsageReportCommand`。`combine().map()` の Raoh 流。Form クラスなし |
| エンコーダ | ◎ | `BillEncoder` で sealed interface を switch 分岐。`InQuota` のレスポンスには `overageTokens` `appliedOverageRatePer1K` `totalCharge` のキーが**そもそも出力されない**（null や 0 ではなく、フィールド自体が存在しない） |
| JdbcClient + 行デコーダ | ◎ | `MapBillDecoders.combine(...).map(...)` で `Map<String, Object>` 行をドメイン型に。JPA・ORM 不使用 |
| sealed interface の DB 反映 | ◎ | `bills.kind VARCHAR(16)` 列 + 4 本の CHECK 制約（`chk_bill_kind` `chk_total_tokens` `chk_token_split` `chk_in_quota_shape` `chk_with_overage_shape`）で sealed interface の不変条件を DB レベルに引き上げ |
| 適用超過レートのスナップショット | ◎ | `bills.applied_overage_rate_per_1k` カラムを追加し、料金プラン側の現在値ではなく計算時点の値を保存。ADR-002 として理由を記録 |
| エラーマッピング | ◎ | ValidationError → 400 / CustomerNotFound → 404 / SubscriptionInactive → 409 / 内部 → 500。`UsageBillingService.Result` を sealed interface にして 4 ケースを網羅 |
| ADR の自発的生成 | ◎ | 3本（ORM 不使用、レートスナップショット、テーブル設計）を Context/Decision/Consequences で記録 |

#### Shell 側の設計上の補足

- 顧客存在チェックは Service 層で別途呼ぶ設計（デコーダパイプラインに `flatMap` で組み込む選択肢もあったが、境界デコーダの I/O 依存を避けるため明示的に分離）
- `UsageBillingService.Result` を sealed interface にして「計算済み / 顧客なし / サブスクリプションなし / データ整合性問題」の4ケースを Result 型として表現
- `kind` フィールドが API レスポンスでも DB 列でも discriminator として一貫している。クライアント・サーバー・DB が同じ判別を共有

## 総合所感

### Raoh の流儀がそのまま実装に乗った

Zenn 本『古典ドメインモデルパターンの解脱』が示す Always-Valid Layer / Parse, Don't Validate / sealed interface での状態分割 / 「ただの record」というドメインモデルが、3つのプロンプトすべてで一貫して実装に現れました。core-generation と shell-generation のプロンプト本体はもともと TypeScript 前提でしたが、参考素材として Raoh のリファレンス実装（`examples/spring/membership/`）を読ませることで、Java/Spring/Raoh 流儀への翻訳が成立しました。

### sealed interface の分割が3層で一貫

仕様モデルで発見された `Bill = 枠内請求 OR 超過込み請求` の二分割が:

- **Core (Java)**: `sealed interface Bill permits Bill.InQuota, Bill.WithOverage`
- **Shell DB**: `bills.kind` 列 + CHECK 制約で「kind='IN_QUOTA' なら課金列すべて NULL、kind='WITH_OVERAGE' なら課金列すべて NOT NULL かつ正」を強制
- **Shell API**: `BillEncoder` の switch で各 record に対応した別エンコーダ。`InQuota` レスポンスには課金関連フィールドが**出力されない**（null や 0 ではなく、フィールド自体が存在しない）

の3層で一貫して反映されました。整数 0 や null による sentinel パターンが構造的に排除されています。

### 「ただの record」のドメインモデル

`Bill` `Subscription` `Customer` `PricingPlan` どれも `@Entity` `@NotNull` `@Column` を一切持たない素の record。永続化の知識は `Pg*Repository` に、バリデーションの知識は `JsonUsageDecoders` に、計算の知識は `BillCalculationBehavior` に、それぞれ分離されました。

### プロンプトの限界として観察された点

このサンプルでも限界らしい限界は観察されませんでした。Raoh のリファレンス実装を素材として与えれば、生成エージェントは流儀を忠実に拾えました。

ただし、これは **「Raoh の examples/spring/ という参照実装が存在する」前提** での結果です。参照実装がない領域（例えば `raoh-jooq` や `raoh-gsh` を使うパターン、あるいは Raoh を使わない Bean Validation ベースの実装をあえて避ける指示など）では、別の難しさが出る可能性があります。

### 本サンプルへの逆フィード候補

生成物（Java/Spring/Raoh 版）と本サンプル（TypeScript ベースの spec ドキュメント）の比較から、本サンプルの spec ドキュメントに反映する候補:

1. **「当月の枠消費状況」の3状態化を spec-model に取り込むか**: 生成物の `枠未消費 OR 枠一部消費 OR 枠使い切り` は SMDD の精神により忠実
2. **`bills.applied_pricing_plan_id` を persistence spec に追加するか**: 仕様モデルの `適用料金プランID` を永続層に反映
3. **`TIMESTAMP → TIMESTAMPTZ` への変更を persistence spec に取り込むか**: UTC 月境界クエリの安全性として妥当
4. **ADR の3本を本サンプルに置くか**: 本サンプルでは「このサンプルでは省略」としていた ADR が、生成物では Context/Decision/Consequences の3節で記録された
5. **API レスポンスでフィールド自体を出さない（null や 0 を出さない）方針**: 本サンプルでは `kind: "InQuota"` のレスポンスでも `overageTokens: 0` を載せていたが、生成物はフィールド自体を出さない。Always-Valid の精神により忠実

これらは Phase C（本サンプルへの逆反映）として別途扱うのが筋です。

## ネタ元 SPDD 実装との比較

token-billing リポジトリの `spdd-practice-demo` ブランチには、SPDD（Structured Prompt-Driven Development）と銘打った別の AI 駆動開発ワークフロー（analysis doc → structured prompt → generated code）の成果物が置かれています。同じ要件文書から出発した実装が並んでいるので、ここでは**生成された Java コードどうしを直接比較**します。

参照したコミット: `origin/spdd-practice-demo` の Story 1（マルチプラン課金、Standard/Premium 対応版）。

### コードベース全体の規模

| 観点 | SPDD（spdd-practice-demo） | spec-anatomy + Raoh 流 |
| --- | --- | --- |
| Java ファイル数 | 39 | 22（Core）+ 11（Shell）= 33 |
| クラス層構造 | Controller / DTO / Service / Strategy / Domain / Repository / InfrastructureAdapter / PO / Mapper / Exception | api / service / persistence / core(model+behavior+port) |
| ドメイン以外の DTO クラス | `UsageRequest` `BillResponse` `BillingContext` ＋ 4 PO + 4 Mapper + 4 例外 | デコーダとエンコーダ（関数）のみ。中間 DTO クラスなし |
| Lombok 使用 | あり（`@Getter` `@Builder` `@Setter` 多数） | なし |
| Bean Validation | あり（`@NotNull` `@Min`） | なし（Raoh デコーダで境界検証） |
| JPA + Spring Data | あり（`@Entity` PO + `@Repository` Adapter + `Mapper`） | なし（JdbcClient + 行デコーダ） |

クラスの数だけ見ると同程度ですが、**SPDD は同じ業務概念を平均 3〜4 クラス（DTO・ドメイン・PO・Mapper・例外）で表現**するのに対し、Raoh 流は **1 クラス（record）と関数（デコーダ・エンコーダ）の組合せ**で表現します。

### `Bill` の表現の対比

SPDD の `Bill`（[domain/Bill.java](file:///Users/kawasima/workspace/token-billing/src/main/java/org/tw/token_billing/domain/Bill.java)、`spdd-practice-demo` ブランチ）:

```java
@Getter @Builder @AllArgsConstructor
public class Bill {
    private final Integer includedTokensUsed;
    private final Integer overageTokens;       // ← 0 か正かで「枠内/超過」を兼ねる
    private final BigDecimal promptCharge;     // ← Premium のときだけ意味がある（Standard では null）
    private final BigDecimal completionCharge; // ← 同上
    private final BigDecimal totalCharge;
    // ... 計算ロジックは `createStandard()` と `createPremium()` 静的ファクトリに直接書かれている
}
```

Raoh 流の `Bill`（[generated/core-generation/.../Bill.java](generated/core-generation/src/main/java/org/tw/token_billing/core/model/Bill.java)）:

```java
public sealed interface Bill permits Bill.InQuota, Bill.WithOverage {
    record InQuota(... 課金関連フィールドなし ...)        implements Bill { ... }
    record WithOverage(..., OverageTokens overageTokens,
                       Money appliedOverageRatePer1K,
                       Money totalCharge, ...)             implements Bill { ... }
}
```

決定的な差:

- **状態の表現**: SPDD は **整数 0 をセンチネル**にして枠内/超過を兼用（`overageTokens = 0` なら枠内、`> 0` なら超過）。Raoh 流は **sealed interface の異なる record に分割** し、`InQuota` には超過関連フィールドが**そもそも存在しない**
- **Standard/Premium の分岐**: SPDD は `BillingStrategy` という GoF Strategy パターンで Standard/Premium を分岐。Raoh 流の生成物は Story 1（マルチプラン）対応していないが、対応するなら `Bill` の sealed interface に `WithOverage` と並ぶ第3バリアント `PremiumSplit(promptCharge, completionCharge)` を追加するだけで、Strategy ファクトリは不要
- **不変条件**: SPDD は `Bill.builder()` でいかなる組合せの Bill も作れる（`overageTokens = -1` も `totalCharge = null` も型上は通る）。Raoh 流は `OverageTokens` の `value >= 1`、`WithOverage` の compact constructor で `totalCharge > 0` を強制し、不正な Bill を構築不能にする

### 詰め替えの数

SPDD の Bill 1件のフロー:

```text
JSON --> UsageRequest --(Service)--> BillingContext --> Bill --(BillMapper)--> BillPO --(JPA)--> 行
                                                          |
                                                      （Bill のまま戻る）
                                                          |
                                                  (Service)
                                                          v
                                                  --(BillResponse.fromBill)--> BillResponse --> JSON
```

詰め替え 5 回（UsageRequest → BillingContext → Bill → BillPO → JPA、および Bill → BillResponse）。

Raoh 流のフロー:

```text
JSON --(JsonUsageDecoders.USAGE_REPORT_REQUEST.decode)--> UsageReportCommand
       --(BillCalculationBehavior.calculate)--> Bill
       --(JdbcClient + switch on Bill)--> 行
       --(BillEncoder.BILL.encode)--> Map<String,Object> --> JSON
```

詰め替え 3 回（JSON→UsageReportCommand、Bill→DB 行、Bill→Map）。中間オブジェクトが消え、PO・Mapper・専用 DTO がない。

### バリデーションの位置

SPDD: `@NotNull` `@Min` を `UsageRequest` に貼り、Spring が `@Valid` で検証。**型変換とバリデーションが分離**しているため、`UsageRequest` がバリデーション通過後も String/Integer 生のままでドメイン層に流れ込み、`BillingService.calculateBill(UsageRequest)` の入口でも再度ガード節（`validateCustomerExists` `resolveActivePricingPlan`）を書くことになる（Shotgun Parsing）。

Raoh 流: デコーダが「JSON → 検証済みドメイン型」を一気に行う（Parse, Don't Validate）。`UsageReportCommand` は型としてすでに検証済みであり、Service 層は再検証しない。`ValidatedCustomerId` のように「検証済み」が型に刻まれるため、未検証の `String customerId` が下流に流れることが構造的に起こらない。

### エラーハンドリング

SPDD: `CustomerNotFoundException` `NoActiveSubscriptionException` `ModelPricingNotFoundException` を `throws` で投げ、`GlobalExceptionHandler` でキャッチして HTTP ステータスにマップ。**例外でフロー制御**するクラシックな Spring パターン。

Raoh 流: 例外を投げない。`UsageBillingService.Result` を `sealed interface { Calculated | CustomerNotFound | SubscriptionInactive | DataIntegrityIssue }` にして、Controller の `switch` で網羅的に HTTP 応答にマップ。失敗ケースが**型に刻まれて**おり、コンパイラが網羅性をチェックする。例外クラスが 4 本消える。

### DB スキーマの整合性

SPDD: `BillPO` の `overageTokens` は `nullable = false` だが、**「枠内のときは null」「超過のときは正」のような不変条件を CHECK 制約で表現していない**。`promptCharge` `completionCharge` は `nullable = true` で「Premium のときだけ値がある」というルールが SQL レベルでは表現されない。アプリケーションコードのバグで矛盾した行が書き込まれる可能性がある。

Raoh 流: `bills.kind` 列 + 4 本の CHECK 制約で「kind='IN_QUOTA' なら overage_tokens=0 かつ rate=NULL かつ charge=NULL」「kind='WITH_OVERAGE' なら overage_tokens>=1 かつ rate IS NOT NULL かつ charge>0」を SQL レベルで強制。アプリケーション層の Java の sealed interface 不変条件と DB の CHECK 制約が**ミラー**になっており、二重防壁。

### SPDD との比較から得られる総合所感

ネタ元 SPDD 実装は Zenn 本『古典ドメインモデルパターンの解脱』が**まさに批判している構造そのもの**になりました（古典ドメインモデルパターン + Full Mapping + Bean Validation + 例外フロー制御）。これは SPDD ワークフローの問題というより、**「analysis doc → structured prompt → code 生成」という流れに、ドメインモデリングの設計指針（Always-Valid Layer / Parse, Don't Validate / sealed interface 状態分割）を**注入していない**から起きる現象**だと考えられます。生成 AI に `@Entity` を付けるのが妥当か、`int overageTokens = 0` でセンチネルを使うのが妥当かといった判断は、特定の流儀（古典 DDD / 関数型寄り / Raoh）に立たないと決められません。

spec-anatomy 側はそこに **refactoring-prompt のステップ6（deeper insight refactoring）** で「整数 0 をセンチネルにせず型を分ける」「業務概念を boolean / null / 整数フラグに平坦化しない」という SMDD の精神を組み込み、core/shell-generation-prompt で Raoh のリファレンス実装を素材として読ませることで、最終生成物が古典ドメインモデルパターンに転落しないようにしました。**プロンプトの差より、プロンプトに埋め込まれた設計哲学の差**が結果を分けています。

| 観点 | SPDD（古典 + Full Mapping） | spec-anatomy + Raoh 流 |
| --- | --- | --- |
| ドメインモデルが持つ知識 | 永続化（@Entity）+ バリデーション（@NotNull）+ 計算ロジック | 構造のみ（record） |
| 状態の表現 | int 0 のセンチネル / nullable | sealed interface + record |
| 詰め替え回数 | 5 回 | 3 回 |
| バリデーション | Bean Validation（境界の外）+ Service 内ガード節 | デコーダで境界の入口で完了 |
| エラー伝播 | 例外（throws） | Result 型（sealed interface） |
| DB の不変条件保証 | NOT NULL のみ | CHECK 制約で sealed の整合性を保証 |
| Standard/Premium の分岐 | GoF Strategy パターン | sealed interface のバリアント追加（拡張時） |
| 業務概念の boolean / 0 / null での平坦化 | 多い | 構造的に排除 |
| 型レベルで防げる「ありえない値」 | 少ない（Builder で何でも作れる） | 多い（OverageTokens >= 1, totalCharge > 0 等を型保証） |

「同じ要件文書から、AI 駆動で実装まで自動生成する」という目的は SPDD も spec-anatomy も同じですが、**埋め込んだ設計哲学が違うと、生成される実装の品質はここまで分岐する**という示唆が得られた、と言えます。

## 関連

- 元素材: [source-material.md](source-material.md)
- 生成物: [generated/](generated/)
- 本サンプル全体: [../README.md](../README.md)
- 本サンプル spec-model: [../spec-model/token-billing.md](../spec-model/token-billing.md)
- 本サンプル persistence: [../shell/persistence/token-billing-table.md](../shell/persistence/token-billing-table.md)
- 本サンプル API: [../shell/api/token-billing-api.md](../shell/api/token-billing-api.md)
- 参照: 河野『[古典ドメインモデルパターンの解脱](https://zenn.dev/kawasima/books/ddd-detachment)』
- 参照: [Raoh GitHub](https://github.com/kawasima/raoh) （ローカル: [/Users/kawasima/workspace/raoh/](/Users/kawasima/workspace/raoh/)）
