---
name: 出張申請テーブル
description: Core の data に対応する永続モデルの例（Data Mapper パターン）
status: approved
last-reviewed: 2026-04-25
---

# 出張申請テーブル

[仕様モデル](../../spec-model/business-trip.md) の `data` を、永続モデルとしてどう表現するかの例です。

## 永続モデルとドメインモデルの分離

Data Mapper パターンに従い、永続モデル（テーブル定義）とドメインモデル（Core）を別の型として持ちます。Core の状態ごとに data を分けた構造を、テーブルでは status カラムで表現し、Mapper で双方向に変換します。

## テーブル定義

```sql
CREATE TABLE departments (
  code                 VARCHAR(20) PRIMARY KEY,
  name                 VARCHAR(255) NOT NULL,
  manager_employee_id  VARCHAR(20),                 -- 部門長。NULL可（承認者フォールバックの終端）
  FOREIGN KEY (manager_employee_id) REFERENCES employees(id)
);

-- 社員テーブルは別集約だが、所属部門カラムをここに示す（Core の `data 社員` の 所属部門 に対応）
-- ALTER TABLE employees ADD COLUMN department_code VARCHAR(20) REFERENCES departments(code);
-- employees(manager_id) は上長参照（承認者決定の一次ソース）。所属部門は上長不在時のフォールバックに使う。

CREATE TABLE business_trips (
  id              VARCHAR(20) PRIMARY KEY,
  applicant_id    VARCHAR(20) NOT NULL,
  destination     VARCHAR(255) NOT NULL,
  purpose         TEXT NOT NULL,
  start_date      DATE NOT NULL,
  end_date        DATE NOT NULL,
  cost_bearing    VARCHAR(20) NOT NULL,        -- 'self' or 'counterparty'
  status          VARCHAR(30) NOT NULL,         -- 状態を文字列で
  submitted_at    TIMESTAMP,
  approver_id     VARCHAR(20),                  -- 承認時のみ
  approved_at     TIMESTAMP,                    -- 承認時のみ
  rejection_reason TEXT,                        -- 却下時のみ
  finalized_at    TIMESTAMP,                    -- 最終承認時のみ
  cancelled_at    TIMESTAMP,                    -- 取消時のみ
  CONSTRAINT chk_dates CHECK (start_date <= end_date),
  CONSTRAINT chk_cost_bearing CHECK (cost_bearing IN ('self', 'counterparty')),
  CONSTRAINT chk_status CHECK (
    status IN (
      'draft', 'submitted',
      'pre_approval_required', 'pre_approval_not_required',
      'pre_approved', 'pre_rejected',
      'actual_registered', 'finalized',
      'cancelled'
    )
  ),
  FOREIGN KEY (applicant_id) REFERENCES employees(id),
  FOREIGN KEY (approver_id) REFERENCES employees(id)
);

CREATE TABLE business_trip_travelers (
  trip_id       VARCHAR(20) NOT NULL,
  line_no       INTEGER NOT NULL,
  employee_id   VARCHAR(20) NOT NULL,
  PRIMARY KEY (trip_id, line_no),
  FOREIGN KEY (trip_id) REFERENCES business_trips(id),
  FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE business_trip_planned_costs (
  trip_id       VARCHAR(20) NOT NULL,
  line_no       INTEGER NOT NULL,
  expense_date  DATE NOT NULL,
  category      VARCHAR(20) NOT NULL,  -- 'transportation', 'accommodation', 'entertainment'
  planned_amount INTEGER NOT NULL,
  PRIMARY KEY (trip_id, line_no),
  FOREIGN KEY (trip_id) REFERENCES business_trips(id)
);

CREATE TABLE business_trip_actual_costs (
  trip_id       VARCHAR(20) NOT NULL,
  line_no       INTEGER NOT NULL,
  expense_date  DATE NOT NULL,
  category      VARCHAR(20) NOT NULL,
  actual_amount INTEGER NOT NULL,
  PRIMARY KEY (trip_id, line_no),
  FOREIGN KEY (trip_id) REFERENCES business_trips(id)
);
```

## Mapper の責務

### Core → 永続モデル（toRecord）

```text
behavior toRecord = 出張申請 -> BusinessTripRecord

# 状態に応じてカラムを埋める
出張申請ドラフト         → status='draft'、submitted_at=NULL、approver_id=NULL...
申請済み出張申請         → status='submitted'、submitted_at=値、approver_id=NULL...
事前承認必要な出張申請   → status='pre_approval_required'、approver_id=NULL
事前承認OK               → status='pre_approved'、approver_id=値、approved_at=値
事前承認NG               → status='pre_rejected'、approver_id=値、approved_at=値、rejection_reason=値
出張実績                 → status='actual_registered'、approver_id（事前承認OK時のみ）
最終承認                 → status='finalized'、approver_id=最終承認者、finalized_at=値
取消済出張申請           → status='cancelled'、cancelled_at=値（取消前の他カラムはそのまま保持）
```

`data 取消済出張申請 = 申請済み出張申請 AND 取消日時` は、取消前の申請内容（status 遷移元のカラム）をそのまま残し、cancelled_at を埋めて status='cancelled' にします。取消がどの状態から起きたかは監査上残したいので、遷移元のカラムを消しません。

### 永続モデル → Core（toEntity）

```text
behavior toEntity = BusinessTripRecord -> 出張申請 OR Mapping エラー

# status の値に応じて、対応する data 型を構築
status='draft'                  → 出張申請ドラフト
status='submitted'              → 申請済み出張申請
status='pre_approval_required'  → 事前承認必要な出張申請
status='pre_approval_not_required' → 事前承認不要な出張申請
status='pre_approved'           → 事前承認OK
status='pre_rejected'           → 事前承認NG
status='actual_registered'      → 出張実績
status='finalized'              → 最終承認
status='cancelled'              → 取消済出張申請

# 必須カラムが NULL なら Mapping エラー
# 例: status='pre_approved' なのに approver_id=NULL → Mapping エラー
# 例: status='cancelled' なのに cancelled_at=NULL → Mapping エラー
```

## 関連の永続化

関連のモデリングの観点では、出張申請と予定費用・実績費用の関係は次のように扱います。

| 関連                   | 種類                | 永続化パターン                |
| ---------------------- | ------------------- | ----------------------------- |
| 出張申請 ⇔ 予定費用    | 親子（依存関係あり）| 単方向 + Eager Load + 差分検出 |
| 出張申請 ⇔ 実績費用    | 親子（依存関係あり）| 単方向 + Eager Load + 差分検出 |
| 出張申請 ⇔ 出張者      | 親子（依存関係あり）| 単方向 + Eager Load + 差分検出 |
| 出張申請 → 申請者      | リソース参照        | ID参照                        |
| 出張申請 → 承認者      | リソース参照        | ID参照                        |
| 社員 → 所属部門        | リソース参照        | ID参照（department_code）     |
| 部門 → 部門長          | リソース参照        | ID参照（manager_employee_id） |

予定費用・実績費用・出張者は出張申請のライフサイクルと運命を共にするため、出張申請が集約ルートです。`Repository.findById` は出張申請と費用・出張者を一度に Eager Load し、`save` は差分検出で予定費用・実績費用・出張者（`List<出張者>`）を更新します。

申請者・承認者は別の集約（社員）に属するため、ID参照で持ちます。社員の所属部門・部門の部門長も別集約への ID参照です。

## 承認者解決の永続的観点

`behavior 承認者を決定する = 申請者 -> 承認者` は、申請者の上長を一次ソースとし、上長が不在なら所属部門の部門長にフォールバックします（Why: 承認は指揮命令系統の上位者が行う。上長未設定者も部門長が代行できるようにして承認の空白を作らない）。永続側では次の2本の参照で解決します。

```text
behavior EmployeeRepository.findManager = 社員番号 -> 承認者 OR NoManager
# employees.manager_id を辿って上長を返す。未設定なら NoManager

behavior DepartmentRepository.findManagerByEmployee = 社員番号 -> 承認者 OR NoDepartmentManager
# employees.department_code → departments.manager_employee_id を辿って部門長を返す
# 部門長が未設定（NULL）なら NoDepartmentManager
```

上長・部門長の双方が解決できない場合は、承認者を決定できないため業務エラー（[API](../api/business-trip-api.md) の `NO_APPROVER_FOUND`）になります。判定順序（上長 → 部門長）は Core の `behavior 承認者を決定する` の Why に従い、永続側は参照の解決だけを担います。

## Repository インターフェース

```text
behavior BusinessTripRepository.findById = 出張申請ID -> 出張申請 OR NotFound
behavior BusinessTripRepository.save = 出張申請 -> 保存完了
behavior BusinessTripRepository.delete = 出張申請ID -> 削除完了
# delete は `behavior 下書きを破棄する`（出張申請ドラフト -> Unit）専用。ドラフトは物理削除する。
# 取消（`behavior 出張申請を取り消す`）は削除ではなく status='cancelled' への save で表す（監査上残す）。
```

業務ロジックは Repository を通じて Core の data を扱います。SQL や ORM の詳細は Repository の実装に閉じます。ドラフトの破棄だけは物理削除（delete）、取消は状態遷移（save）と区別します。

## 関連 Shell

- API: [../api/business-trip-api.md](../api/business-trip-api.md)
- UI: [../ui/business-trip-detail-screen.md](../ui/business-trip-detail-screen.md)

## 関連 ADR

このサンプルでは Data Mapper パターンを採用していますが、Active Record / Repository / CQRS のいずれを採るかは ADR で記録します（[../../../reference/spec-set/adrs/README.md](../../../reference/spec-set/adrs/README.md) 参照）。
