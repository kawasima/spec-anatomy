# 画面デザインHTML（共有）

出張申請システムの画面デザインHTMLです。実際に利用者が見る画面のモックで、**before（[traditional-design/](../traditional-design/) の画面設計書のレイアウト）と after（[shell/ui/](../shell/ui/) の Spec Set 画面）の両方から参照される共有アセット**です。画面そのものは設計の記法（方眼紙か Spec Set か）に依らず同じなので、1か所に置いて両方から使います。

1画面1ファイルのレスポンシブHTML（PC・モバイル両対応）。CSSは各ファイルにインラインで自己完結しており、ブラウザで直接開けます。

## 画面一覧と対応

| ファイル | 画面 | traditional 画面ID | Spec Set 画面 |
| --- | --- | --- | --- |
| [01-list.html](01-list.html) | 出張申請一覧 | WBT0501 | SCREEN-BT-01 |
| [02-application-create.html](02-application-create.html) | 出張申請 作成・編集 | WBT0101 | SCREEN-BT-03 |
| [03-application-confirm.html](03-application-confirm.html) | 出張申請 登録確認 | WBT0102 | （登録の確認ステップ） |
| [04-application-complete.html](04-application-complete.html) | 出張申請 登録完了 | WBT0103 | （登録の完了ステップ） |
| [05-pre-approval.html](05-pre-approval.html) | 出張申請 事前承認 | WBT0201 | SCREEN-BT-02 |
| [06-actual-create.html](06-actual-create.html) | 出張実績 登録 | WBT0301 | SCREEN-BT-04 |
| [07-actual-confirm.html](07-actual-confirm.html) | 出張実績 登録確認 | WBT0302 | （実績登録の確認ステップ） |
| [08-actual-complete.html](08-actual-complete.html) | 出張実績 登録完了 | WBT0303 | （実績登録の完了ステップ） |
| [09-final-approval.html](09-final-approval.html) | 出張申請 最終承認 | WBT0401 | SCREEN-BT-05 |

traditional は「入力→確認→完了」を別々の画面（取引）として扱い、Spec Set は確認・完了を登録操作のステップとして畳みます。同じ画面モックを、粒度の違う2つの設計記法が別々の見方で参照します。

## 使い方

- **そのまま確認**: 各HTMLをブラウザで開く（ビルド不要）。
- **画面項目表を起こす**: [tools/oppsett/](../../../tools/oppsett/) にデザインHTMLを読み込ませ、要素をマークアップして screen.md（画面項目表）を生成する。各領域の `data-group`、各項目の `data-item` 属性はこのマークアップの下地です。
- **ビューアで見る**: リポジトリの viewer で screen.md を開くと、対応するレイアウトHTMLが iframe でインライン表示されます。

## 約束事

- 各領域に `data-group="◯◯領域"`、各項目（ラベル・入力・ボタン・列見出し・状態バッジ）に `data-item="項目名"` を付ける（oppsett のマークアップ対象）。
- CSSはインラインで自己完結（外部参照なし）。作風は全画面で統一（グレー基調の業務フォーム、状態は申請状態10種のバッジ）。
- レスポンシブ（`max-width:640px` で1カラム化・テーブル横スクロール）。
- 拡張スコープ（下書き保存・破棄・差し戻し再申請・取消）のボタンや、事前承認却下・取消済などの状態も含みます。
