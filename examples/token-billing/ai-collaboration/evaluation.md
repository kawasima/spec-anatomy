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

## specの位置づけ

ここまでは実装スタイルの差を見てきた。もうひとつ別の軸がある。仕様変更があったときに spec とコードのどちらを直して、どちらを再生成するか、という軸だ。AI 時代の Spec-driven 系の方法論はここで分かれる。

3つの立場を整理しておく。

| 立場 | spec の役割 | コードの役割 | 仕様変更の経路 |
| --- | --- | --- | --- |
| Spec-as-source | 真実。コードは派生物 | spec から決定論的に再生成される | spec を変更 → コードを再生成 |
| Spec-anchored | アンカー（契約）。常に最新を保つ | 真実の片側。spec と双方向同期 | spec を変更 → コードを更新（または逆方向で sync） |
| Spec-first | 起点。最初だけ書く | 真実。spec はやがて陳腐化する | コードを変更（spec は更新しない） |

SMDD（spec-anatomy）はこの軸で見ると Core と Shell で立場が違う。Core は Spec-as-source で、仕様DSLが真実、Java/TypeScript の Core 実装は仕様モデルから派生する。仕様モデルが refactor されたら Core を再生成する（[core-generation-prompt.md](../../../docs/ai-collaboration/core-generation-prompt.md) の「仕様モデルを refactoring したので Core を再生成したい」がこの想定）。Shell は Spec-anchored で、API 契約・テーブル定義の spec が anchor、実装の細部は ADR で記録する。Policy & Discretion で「方針は明示するが選択は委ねる」スタイル。

SPDD は自己宣言上、Spec-anchored を主張している。[`.cursor/commands/spdd-sync.md`](https://github.com/gszhangwei/token-billing/blob/spdd-practice-demo/.cursor/commands/spdd-sync.md) の冒頭に「ensuring the prompt remains the accurate source of truth for the system design」とあり、[`.cursor/commands/spdd-generate.md`](https://github.com/gszhangwei/token-billing/blob/spdd-practice-demo/.cursor/commands/spdd-generate.md) の Review & Iteration Loop には「When reality diverges, fix the prompt first — then update the code」「The structured prompt serves as the contract between design and implementation」とある。コードを直接編集してから `/spdd-sync` で spec に戻す経路は補助として用意されているが、推奨はあくまで「spec を直してから code を再生成」だ。

### 想定運用と実態のずれ

SPDD の想定運用は、ひとつの prompt ファイルをひとつの機能領域の完全仕様として扱い、同じ機能領域に増分が入るときは [`/spdd-prompt-update`](https://github.com/gszhangwei/token-billing/blob/spdd-practice-demo/.cursor/commands/spdd-prompt-update.md) で既存 prompt ファイルを上書き更新する、というものだ。新しい機能領域のときだけ新規 prompt ファイルを作る。そうすれば `spdd/prompt/` 配下は機能領域別の現在仕様カタログになる。

ところが `spdd-practice-demo` ブランチの実態は違う。Story 1（基本課金）で `[Feat]-api-token-usage-billing.md` を作ったあと、Story 2（マルチプラン課金）では `/spdd-prompt-update` を使わずに新規ファイル `[Feat]-multi-plan-billing-model-aware-pricing.md` を作っている。Story 1 の prompt には Story 2 で追加された `modelId`・`promptCharge`・`completionCharge` が反映されないまま残り、コード上の `Bill` クラスだけが Story 2 完了時点のフルセットになっている。prompt とコードが乖離している。

自己宣言は Spec-anchored だが、運用が破綻すると SPDD は実質的に Spec-first に退化する。SPDD の設計の問題ではなく運用の問題だが、運用を強制する仕組みは現状ない。

## ストーリーの総和はシステム仕様になるか

SPDD には「`spdd/prompt/` 配下の全ファイルの集合がシステム全体の仕様になる」という前提が暗黙にある。`/spdd-prompt-update` で上書き更新が続けられれば、各ファイルが機能領域の最新仕様であり、その集合がシステム仕様だ、というロジックだ。

この前提は新しいものではなく、過去30年のソフトウェア工学で何度も検討されてきた。歴史を見ると、条件付きでしか成り立たない近似であり、それを超えるとどこかで崩れる、というのが繰り返し確認されてきた。

### XPの位置づけ

Kent Beck の *Extreme Programming Explained*（1999）で User Story が登場したとき、これは「会話の約束手形（promissory note for conversation）」として位置づけられた。Ron Jeffries の 3C（Card / Conversation / Confirmation）がそれを定式化している。カードは仕様そのものではなく、会話のきっかけにすぎない。

XP において仕様の本体はストーリーではなく、Acceptance Test（Customer Test）、System Metaphor、Simple Design の3つに分散していた。System Metaphor がストーリー横断のシステム全体像を担う想定だった。

ところが System Metaphor は実際にはほとんど機能しなかった。Beck 自身が *Extreme Programming Explained 2nd Edition*（2004）で「XP のプラクティスのうちこれだけは明確に失敗した」と認めている。多くのチームでメタファが「クライアント・サーバ」程度の抽象に留まり、システム全体の構造を伝える媒体にならなかった。これで「ストーリーの総和の上位に何を置くか」の問題が宙ぶらりんになった。

### Cohnの定式化

*User Stories Applied*（2004）で Mike Cohn ははっきり書いている。

> User stories are not the requirements. They are placeholders for requirements.

そしてストーリーが大きくなったら epic として分解し、エピックが集まったら theme として束ねよ、という theme → epic → story の3層構造を提案している。「ストーリーの総和」だけでは全体仕様にならないことを、Cohn 自身が階層を入れる形で認めている。

### SbEとLiving Documentation

Gojko Adzic の *Specification by Example*（2011）と Cyrille Martraire の *Living Documentation*（2019）はこの問題に正面から答えた。両者の主張は一致している。ストーリー単体は仕様の運搬手段として不完全で、受け入れ基準（Examples）を集約したものこそが仕様であり、それをコードと同じリポジトリに置きテストで保証することで Living Documentation になる。ただしドメインモデル・アーキテクチャ・横断制約は Examples からは自動的には生まれず、別途モデリングが要る、というのが共通の結論だ。

Cucumber の `.feature` ファイルは「1機能 = 1ファイルで上書き更新」という運用が想定されており、SPDD の `/spdd-prompt-update` の発想と近い。BDD コミュニティが20年かけて辿り着いたのは、`.feature` ファイルの集合は振る舞いの仕様にはなっても、ドメインモデル・アーキテクチャ・横断制約の仕様にはならない、という認識である。

### DDDからの答え

Eric Evans の *Domain-Driven Design*（2003）は別の角度から同じ問題を扱った。ユビキタス言語と境界づけられたコンテキストはストーリーの足し算からは出てこない。ドメインモデルは業務全体に対する仮説であり、ストーリー1つに紐づくものではない。順序は逆で、ドメインモデルが先にあり、その上にストーリーが乗る。

DDD コミュニティが Scrum と相性が悪いと長く言われてきた理由はここにある。Scrum はストーリーの優先順位付けが主、DDD はドメインモデルの構造化が主で、出発点が違う。両立させるには Event Storming のように、ストーリーを越えてシステム全体を描き出す手段を別途入れる必要があった。

### 何が抜け落ちるのか

ストーリーの総和を仕様と呼ぶときに抜け落ちるものは、垂直方向と横断方向の2つに整理できる。

垂直方向に抜けるのは「なぜそう設計したのか」だ。ストーリーは「ユーザーから見える振る舞い」を記述する切り口で、その下にあるドメインモデルやアーキテクチャ判断を記述する切り口ではない。なぜ Bill を sealed interface に分けるのか、なぜ Repository を分けるのか、なぜ適用超過レートをスナップショットするのか、といった判断はストーリー単体に書きにくいし、ストーリーの和を取っても出てこない。

横断方向に抜けるのは「複数のストーリーが同時に触る不変条件」だ。請求記録は計算日時を超えて書き換えられない、料金プランの変更は過去の請求記録に遡及しない、サブスクリプションは同顧客同時刻に1つしか有効でない、といった性質は個別のストーリーが書かれた時点では明示されにくい。後から「全ストーリーをまたいで成立すべき性質」として浮上することが多い。

### SMDDとSPDDの違い

SMDD はこの2つを領域別ファイル分割で扱う。spec-model（ドメインの不変条件・全域性）が Core として最上位にあり、ストーリーはその上の「業務操作の組合せ」として乗る。Core/Shell の二段階で垂直階層を表す。横断的な性質は spec-tests（不変条件・状態遷移・全域性）として別カテゴリに置き、複数 behavior にまたがる性質を property として記述する。ファイルは領域別（spec-model / shell/api / shell/persistence / spec-tests）に分割され、ストーリー単位ではない。

SPDD は同じ問題を REASONS Canvas の E（Entities）と S（Safeguards）に詰め込む形で扱う。1ファイル内で垂直（E）と横断（S）を表現しようとする。機能領域が小さいうちは機能するが、領域が増えると複数ファイルの E と S が互いに整合しているかは `/spdd-prompt-update` の手作業に依存する。機能領域単位の Spec-anchored が運用で守られる限り、SPDD は Specification by Example の延長として成立する。守られなければ Spec-first に退化する。

### 結論

「ユーザーストーリーの総和 = システム全体の仕様」は、過去30年のソフトウェア工学が誰も完全には信じてこなかった近似だ。XP は System Metaphor で補おうとして失敗し、Cohn は階層構造を入れ、SbE は Examples の集約とドメインモデルの分離で答え、DDD は最初からドメインモデルを優先するスタンスを取った。SPDD はストーリー単位の prompt ファイルが上書き更新で育てば全体仕様になる、という前提に立つが、これは BDD コミュニティが既に通った道であり、`/spdd-prompt-update` の運用が破綻したときの帰結を demo ブランチが示している。

token-billing くらいの小さなドメインで Story 1 だけを実装する範囲なら SPDD で十分だ。Story 2、Story 3 と増えたときに、ストーリーを越えた全体構造をどこに書くのかが残課題になる。SMDD はそれを spec-set のディレクトリ構造として最初から組み込み、SPDD は `/spdd-prompt-update` の手作業に委ねている。

## 関連

- 元素材: [source-material.md](source-material.md)
- 生成物: [generated/](generated/)
- 本サンプル全体: [../README.md](../README.md)
- 本サンプル spec-model: [../spec-model/token-billing.md](../spec-model/token-billing.md)
- 本サンプル persistence: [../shell/persistence/token-billing-table.md](../shell/persistence/token-billing-table.md)
- 本サンプル API: [../shell/api/token-billing-api.md](../shell/api/token-billing-api.md)
- 参照: 河野『[古典ドメインモデルパターンの解脱](https://zenn.dev/kawasima/books/ddd-detachment)』
- 参照: [Raoh GitHub](https://github.com/kawasima/raoh) （ローカル: [/Users/kawasima/workspace/raoh/](/Users/kawasima/workspace/raoh/)）
