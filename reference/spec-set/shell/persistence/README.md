# 永続モデルへの変換規約

Core の `data` を、データベースのテーブル定義・ORM マッピング・関連の永続化パターンに変換する規約です。

## 永続モデルとは

永続モデルはテーブルの1行に対応する型です。データベーススキーマから導かれるレコード不変条件（NOT NULL、PRIMARY KEY、FOREIGN KEY、CHECK 制約）を保護します。

ドメインモデルが守るのはビジネス不変条件（「承認済みなら承認者が存在する」）、永続モデルが守るのはレコード不変条件（「主キーは NOT NULL」「外部キーは参照先が存在する」）。同じカラムでも、ドメインと永続では意味が違います。

## ドメインモデルと永続モデルの分離

永続モデル == ドメインモデル（Active Record パターン）と扱うと、業務ルールがデータベーススキーマに従属し、テーブル変更が業務ロジックに波及します。

このSpec Setでは、次の3つの実装パターンから業務の性質に合わせて選びます。

### Data Mapper パターン（推奨：複雑なドメイン）

永続モデルとドメインモデルを完全に分離し、専用の Mapper が相互変換を担います。

```text
# 永続モデル（Persistence Model）
data BusinessTripRecord = {
  id, applicant_id, destination, estimated_cost, status,
  approver_id (NULL可), approved_at (NULL可)
}

# ドメインモデル（Core）
data 出張申請 = 申請準備中 OR 事前承認待ち OR 事前承認済み

# Mapper
behavior toEntity = BusinessTripRecord -> 出張申請
behavior toRecord = 出張申請 -> BusinessTripRecord
```

ドメインモデルが永続化層を知らずに書けるため、業務ロジックのテストが I/O なしで完結します。

### Repository 経由のマッピング

永続モデルを外部に出さず、Repository の内部で完結させます。`OrderRepository#findById` は引数と戻り値がドメインモデルで、呼び出し側からは「どんなテーブル構造か」「どうマッピングしているか」が見えません。

```text
behavior OrderRepository.findById = OrderId -> 出張申請 OR NotFound
behavior OrderRepository.save = 出張申請 -> 保存完了
```

### CQRS 的な分離

書き込み側はドメインモデルを通して永続化し、読み取り側（一覧画面、集計など）は永続モデルを直接クエリしてプレゼンテーション用のデータ型に詰めます。書き込みには業務ルールが要りますが、表示のたびにドメインモデルを経由させると重い JOIN クエリの恩恵を受けられないからです。

### Active Record パターン（小規模 / CRUD 中心）

業務ロジックが CRUD 中心で、複雑なルールがほとんどなく、整合性をデータベース制約で十分に守れる場合は、Active Record（Rails の ActiveRecord、Java の JPA Entity 直結）が合理的です。

ただし業務ルールが複雑になってきたら、上の3パターンのいずれかに移行します。Active Record で複雑なドメインを扱うと、業務ルールが ORM の挙動に依存します。

## レコード不変条件の表現

データベーススキーマの制約は永続モデルの型として表現します。

| SQL の制約          | 永続モデルでの表現                       |
| ------------------- | ---------------------------------------- |
| NOT NULL            | nullを許可しない型                       |
| PRIMARY KEY         | 一意性を保証する型                       |
| FOREIGN KEY         | 参照先が存在することを前提とする         |
| CHECK               | 値の制約を型として表現                   |

```text
# テーブル定義
CREATE TABLE business_trips (
  id INTEGER PRIMARY KEY,
  applicant_id INTEGER NOT NULL,
  estimated_cost INTEGER NOT NULL CHECK (estimated_cost >= 0),
  status VARCHAR(20) NOT NULL,
  approver_id INTEGER,
  approved_at TIMESTAMP,
  FOREIGN KEY (applicant_id) REFERENCES employees(id)
);

# 永続モデル（型として）
data BusinessTripRecord = {
  id: number,                          # NOT NULL
  applicant_id: number,                # NOT NULL, FK
  estimated_cost: 0以上の整数,          # CHECK
  status: 'pending' | 'approved' | 'completed',
  approver_id: number | null,          # NULL許容
  approved_at: Date | null,            # NULL許容
}
```

ドメインモデルの「承認済みなら承認者が存在する」は、永続モデルでは「approver_id NULL可、業務上は status='approved' のとき必須」として、Mapper で変換します。

## 関連の永続化パターン

関連のモデリングの4つの論点（パリティ・ID/実体・取得タイミング・更新方式）の組み合わせから、業務の性質に合わせて1つを選びます。

### 純粋ドメインモデル（推奨：仕様モデル駆動と整合）

```text
パリティ: 単方向
参照種別: 実体参照（同じ集約内）
取得タイミング: Eager Load
更新方式: 差分検出
```

ドメインモデルが永続化層の存在を知らずに書けます。Eager Load で関連を全部ロードし切るため不変条件が型で保護され、差分検出で書き戻すためドメインモデル側に SQL が現れません。仕様モデル駆動と相性がよい組み合わせです。

代償は、リポジトリ側に差分検出ロジックを書く必要があることと、Eager Load による初期ロードが重くなり得ることです。関連の件数が大きすぎる場合は、関連取得だけ Nullable に落として Read/Write を分けます。

### ORM 前提（双方向 + Lazy Load + Unit of Work）

JPA/Hibernate、Rails ActiveRecord などの ORM を前提にする場合の組み合わせです。フレームワークの機能をフルに使えますが、ドメインモデルが永続化層と密結合します。

### 交差エンティティ（ID参照 + Eager Load + DEL/INS）

リソース×リソース（依存関係なし）の関連で、関連自体に属性がある場合（例: `Membership`、`Enrollment`）。

```text
data Student = {id, name}
data Course = {id, name}
data Enrollment = {id, studentId, courseId, enrolledAt}
```

`Enrollment` が独立した集約ルートとして扱われるため、関連自体に業務ルール（履修承認フロー、入会申請）がある場合に向いています。

## イミュータブルデータモデルと永続化

イミュータブルデータモデルを採るときは、永続化も次のように変わります。

### イベントは INSERT-ONLY

イベントテーブルには UPDATE/DELETE をしません。新しいイベントは新しいレコードとして追加します。

```text
CREATE TABLE order_events (
  event_id BIGINT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  payload JSONB NOT NULL,
  occurred_at TIMESTAMP NOT NULL
);
-- INSERT-ONLY、UPDATE/DELETE しない
```

### リソースの現在像はイベントから導出

リソーステーブルは「現在像」を持ちますが、その現在像はイベント系列から `behavior` で導出できる形で保存します。リソーステーブルへの直接 UPDATE は避け、イベントの追加で間接的に更新します（イベントソーシング）。

書き込み側はイベントテーブル INSERT、読み取り側はリソーステーブル SELECT、という分離が CQRS 的なパターンと相性がよい構成になります。

### スナップショット

イベント系列が長くなると、毎回 fold するコストが効いてきます。途中の状態をスナップショットとして保存し、「fold(全体) = fold(fold(前半), 後半)」の性質を利用して再開します。

## ADR で記録する判断

永続化方式の選定（Data Mapper / Repository / Active Record / CQRS / イミュータブル）は ADR として記録します。判断の根拠（業務の複雑さ、性能要件、チームのフレームワーク習熟度）を残しておくと、後から見直すときに便利です。

詳細は [../../adrs/README.md](../../adrs/README.md)。

## テンプレート

- [templates/table.md](templates/table.md) — テーブル1件のテンプレート
- [templates/table-catalog.md](templates/table-catalog.md) — テーブル一覧
- [templates/code.md](templates/code.md) — コード値（enum）のテンプレート
- [templates/identifiers.md](templates/identifiers.md) — ID 体系・採番規則

## 参照

- Martin Fowler *Patterns of Enterprise Application Architecture*（Active Record / Data Mapper / Repository）
- Scrapbox「関連のモデリング」
