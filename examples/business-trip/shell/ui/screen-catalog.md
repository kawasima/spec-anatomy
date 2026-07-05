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
| 1 | [SCREEN-BT-01](SCREEN-BT-01-business-trip-list.md) | 出張申請一覧 | 申請者・承認者が申請の状態を確認する入口。申請者は取消も行う | `behavior 出張申請を取り消す`（一覧取得＋取消） |
| 2 | [SCREEN-BT-02](business-trip-detail-screen.md) | 出張申請詳細（事前承認） | 承認者が事前承認必要な申請を確認し承認・却下する | `behavior 上長が事前承認する` |
| 3 | [SCREEN-BT-03](SCREEN-BT-03-business-trip-create.md) | 出張申請作成・編集 | 申請者が出張予定を入力し下書き保存・破棄・申請提出・差し戻し再申請する | `behavior 出張申請する` / `behavior 下書きを保存する` / `behavior 下書きを破棄する` / `behavior 差し戻された申請を再申請する` |
| 4 | [SCREEN-BT-04](SCREEN-BT-04-business-trip-actuals.md) | 出張実績登録 | 帰社後に申請者が実費用を入力して実績を登録する | `behavior 出張実績を登録する` |
| 5 | [SCREEN-BT-05](SCREEN-BT-05-business-trip-final-approve.md) | 出張申請最終承認 | 承認者が出張実績を確認し最終承認する | `behavior 最終承認する` |

`behavior 事前承認が必要か判断する` と `behavior 承認者を決定する` は申請提出・再申請時にサーバ側で自動実行されるため、対応する画面はない。承認者決定は上長を一次ソースとし、上長不在なら所属部門の部門長にフォールバックする（[API の承認者決定の扱い](../api/business-trip-api.md#承認者決定の扱い) 参照）。

## 申請状態と画面の対応

出張申請の状態ごとに、申請者・承認者それぞれがどの画面で操作するかを示す。

取消（`behavior 出張申請を取り消す`）は申請済み〜出張実績（'10'〜'40'）の状態で申請者が [SCREEN-BT-01](SCREEN-BT-01-business-trip-list.md) の取消アクションから実行できる。下の表では各状態行の申請者操作に含めず、共通操作として扱う。

| 申請状態                | 申請者の操作画面                                            | 承認者の操作画面                                                     |
| ----------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------- |
| 出張申請ドラフト        | [SCREEN-BT-03](SCREEN-BT-03-business-trip-create.md)（下書き編集・破棄）| −                                                        |
| 申請済み出張申請        | （参照のみ／取消可）                                        | −                                                                    |
| 事前承認必要な出張申請  | （参照のみ／取消可）                                        | [SCREEN-BT-02](business-trip-detail-screen.md)（承認・却下）        |
| 事前承認不要な出張申請  | （参照のみ／取消可）                                        | −                                                                    |
| 事前承認OK              | [SCREEN-BT-04](SCREEN-BT-04-business-trip-actuals.md)（実績登録）／取消可 | −                                                       |
| 事前承認NG（差し戻し）  | [SCREEN-BT-03](SCREEN-BT-03-business-trip-create.md)（差し戻し再申請）／取消可 | −                                                 |
| 出張実績あり            | （参照のみ／取消可）                                        | [SCREEN-BT-05](SCREEN-BT-05-business-trip-final-approve.md)（最終承認）|
| 最終承認済み            | （参照のみ・取消不可）                                      | （参照のみ）                                                         |
| 取消済出張申請          | （参照のみ・終端）                                          | （参照のみ・終端）                                                   |

## 命名規約

- 画面ID: `SCREEN-BT-{連番2桁}`（BT = Business Trip）
- ファイル名: `SCREEN-BT-{No}-{kebab-case-name}.md`

## 関連ドキュメント

- [screen-transitions.md](screen-transitions.md): 画面遷移図
- [../api/business-trip-api.md](../api/business-trip-api.md): API 契約
- [仕様モデル](../../spec-model/business-trip.md): 仕様モデル（Core）
