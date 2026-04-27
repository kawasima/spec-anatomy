---
name: 出張申請システム 画面一覧
description: 出張申請システムの全画面一覧と関連 behavior の対応
status: approved
last-reviewed: 2026-04-27
---

# 出張申請システム 画面一覧

## 全画面一覧

| No | 画面ID | 画面名 | 画面説明 | 関連する behavior |
| -- | ------ | ------ | -------- | ----------------- |
| 1 | [SCREEN-BT-01](SCREEN-BT-01-business-trip-list.md) | 出張申請一覧 | 申請者・承認者が申請の状態を確認する入口 | （一覧取得のみ） |
| 2 | [SCREEN-BT-02](business-trip-detail-screen.md) | 出張申請詳細（事前承認） | 承認者が事前承認必要な申請を確認し承認・却下する | `behavior 上長が事前承認する` |
| 3 | [SCREEN-BT-03](SCREEN-BT-03-business-trip-create.md) | 出張申請作成・編集 | 申請者が出張予定を入力しドラフト保存・申請提出する | `behavior 出張申請する` |
| 4 | [SCREEN-BT-04](SCREEN-BT-04-business-trip-actuals.md) | 出張実績登録 | 帰社後に申請者が実費用を入力して実績を登録する | `behavior 出張実績を登録する` |
| 5 | [SCREEN-BT-05](SCREEN-BT-05-business-trip-final-approve.md) | 出張申請最終承認 | 承認者が出張実績を確認し最終承認する | `behavior 最終承認する` |

`behavior 事前承認が必要か判断する` は申請提出時にサーバ側で自動実行されるため、対応する画面はない。

## 申請状態と画面の対応

出張申請の状態ごとに、申請者・承認者それぞれがどの画面で操作するかを示す。

| 申請状態                | 申請者の操作画面                                            | 承認者の操作画面                                                     |
| ----------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------- |
| 出張申請ドラフト        | [SCREEN-BT-03](SCREEN-BT-03-business-trip-create.md)（編集）| −                                                                   |
| 申請済み出張申請        | （参照のみ）                                                | −                                                                    |
| 事前承認必要な出張申請  | （参照のみ）                                                | [SCREEN-BT-02](business-trip-detail-screen.md)（承認・却下）        |
| 事前承認不要な出張申請  | （参照のみ）                                                | −                                                                    |
| 事前承認OK              | [SCREEN-BT-04](SCREEN-BT-04-business-trip-actuals.md)（実績登録）| −                                                                |
| 事前承認NG              | （申請やり直しまたは終了）                                  | −                                                                    |
| 出張実績あり            | （参照のみ）                                                | [SCREEN-BT-05](SCREEN-BT-05-business-trip-final-approve.md)（最終承認）|
| 最終承認済み            | （参照のみ）                                                | （参照のみ）                                                         |

## 命名規約

- 画面ID: `SCREEN-BT-{連番2桁}`（BT = Business Trip）
- ファイル名: `SCREEN-BT-{No}-{kebab-case-name}.md`

## 関連ドキュメント

- [screen-transitions.md](screen-transitions.md): 画面遷移図
- [../api/business-trip-api.md](../api/business-trip-api.md): API 契約
- [../../spec-model/business-trip.md](../../spec-model/business-trip.md): 仕様モデル（Core）
