# メッセージング契約への変換規約

Core のドメインイベントを、メッセージブローカーのトピック／キューに対応させる規約です。

## ドメインイベントとメッセージング

Core で定義したドメインイベント（イミュータブルデータモデルのイベント・エンティティ）は、Shell のメッセージング契約として外部システムに通知できる形に変換します。

```text
# Core
data 注文承認イベント = イベントID AND 対象注文ID AND 承認者 AND 承認日時

behavior 注文を承認する = 未承認注文 AND 承認者 -> 承認済み注文 AND 注文承認イベント
```

```text
# Shell（メッセージング）
topic: order.approved
ペイロードスキーマ: 注文承認イベント（Core から派生）
配信保証: At-least-once
順序保証: パーティションキー = 対象注文ID
```

## 基本仕様

メッセージング契約には次の項目を記述します。

| 項目             | 内容                                                |
| ---------------- | --------------------------------------------------- |
| 種別             | パブサブ / キュー / イベントストリーム              |
| トピック／キュー | `order.approved`、`stock.reservation.requested` 等  |
| 発行者           | このメッセージを発行するシステム／コンポーネント    |
| 購読者           | このメッセージを購読するシステム／コンポーネント    |
| 配信保証         | At-most-once / At-least-once / Exactly-once         |
| 順序保証         | 全体順序 / パーティション順序 / 順序保証なし        |
| パーティションキー | 順序保証ありの場合のキー属性                      |
| 保持期間         | ブローカーでのメッセージ保持期間                    |
| 暗号化           | あり（方式） / なし                                 |
| 認証認可         | 認証方式と必要権限                                  |
| ブローカー       | Kafka / RabbitMQ / SQS / Pub/Sub / 等               |

## ペイロードスキーマ

ペイロードは Core のドメインイベント（`data`）から派生します。スキーマレジストリ（Confluent Schema Registry など）を使う場合は、Avro / Protobuf / JSON Schema として保存します。

```json
{
  "messageId": "<UUID>",
  "eventType": "order.approved",
  "occurredAt": "<ISO 8601>",
  "data": {
    "orderId": "ORD-2026-0001",
    "approver": "EMP-123",
    "approvedAt": "2026-04-25T10:00:00Z"
  }
}
```

ヘッダ（`messageId`、`eventType`、`occurredAt`）は Cloud Events や AWS EventBridge の規約に従うのが一般的です。`messageId` は重複検知のキーになります。

## 冪等性

メッセージング契約では、発行側の重複送信と受信側の冪等処理を明示します。

- **発行側の重複送信可能性**: あり（At-least-once の場合） / なし（Exactly-once の場合）
- **受信側の冪等性確保方法**: `messageId` で重複検知、補償ロジックなど

イベント・エンティティは「同じ messageId のイベントを2回受信しても1回しか反映されない」という冪等性が業務上重要です。

## エラー処理

| エラー条件             | 処理                          |
| ---------------------- | ----------------------------- |
| ペイロード不正         | DLQ（デッドレターキュー）へ移送 |
| 業務不変条件違反       | DLQ へ移送 + 運用通知         |
| 一時的失敗             | リトライ <回数>回、間隔 <ms>  |

## ドメインイベントとの対応

メッセージングが「発行する」イベントは、Core のドメインイベントと1対1で対応します。一方、メッセージングが「購読する」イベントは、別システムが発行する外部イベントです。両者の境界では、形式の変換（外部の JSON ペイロード → Core の `data`）が必要になることがあります。

```text
# Core
behavior 出荷指示を受け取る = 出荷指示メッセージ -> 出荷タスク

# Shell（メッセージング）
topic: shipment.instructions（外部システムが発行）
ペイロード形式: 外部システムの定義
変換: 外部ペイロード → 出荷指示メッセージ（Core の data）
```

外部からの入力なので、境界でのバリデーション（外部ペイロード → Core の `data` への変換）が必要です。

## 契約テスト

メッセージングも API と同様に契約テストの対象です。

- ペイロードのスキーマと Core の `data` 構造が一致しているか
- 配信保証と業務上の要件（重複の許容、順序の必要性）が整合しているか
- DLQ への移送条件が定義通りに動くか

## テンプレート

### メッセージング契約

- [templates/messaging.md](templates/messaging.md) — メッセージング契約1件
- [templates/messaging-catalog.md](templates/messaging-catalog.md) — メッセージング契約一覧

### 外部I/F

- [templates/external.md](templates/external.md) — 外部I/F 1件（HTTP共通仕様、レコード構成、固定長/JSON/XML電文項目）
- [templates/external-catalog.md](templates/external-catalog.md) — 外部I/F一覧

詳細は [templates/README.md](templates/README.md) を参照。

## 参照

- Cloud Events Specification
- Alexis King "Parse, don't validate"（境界での変換と内部の不変条件）
