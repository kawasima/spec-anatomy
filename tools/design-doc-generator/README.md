# design-doc-generator

出張申請システム（[examples/business-trip](../../examples/business-trip/)）の「従来SI設計書一式」を、Nablarch開発標準の本物の空テンプレートに内容を流し込んで生成するツールです。出力は [examples/business-trip/traditional-design/](../../examples/business-trip/traditional-design/) の Excel 一式（before）で、同じ business-trip の spec-model / shell（after）と対になります。

## 使い方

```sh
cd tools/design-doc-generator
python build.py      # doc_*.py を全て実行し、.xlsx を出力
```

個別のブックだけ作り直すときは `python doc_code.py` のように単体で実行します。openpyxl 3.1 系が必要です。

## 仕組み

- テンプレートは Nablarch開発標準の空書式（`010_フォーマット`）。書式には手を触れず、セル値だけを書き込みます。
- `traditional-design/_templates/` は **`.gitignore` 済み**（他者の CC BY-SA 空フォーマットをリポジトリに同梱しない）。テンプレートが無いと `open_template` が [templates_manifest.py](templates_manifest.py) の対応表を使って Nablarch開発標準から取得します。初回の `build.py` はネットワークが必要です。
- 各ブックの記入位置は、Nablarch開発標準の記入見本（`020_サンプル`）で確認した固定セル・固定列を使っています。
- 各シートの1〜3行目ヘッダ（PJ名・システム名・成果物名・作成/変更）は多くのテンプレートで `=INDIRECT("変更履歴!…")` の数式なので、値は変更履歴シートに集約して書きます（`common.fill_history`）。`fill_header` はこれへ委譲する後方互換のエイリアスです。

## ファイル構成

- `common.py` — テンプレート読み込み、変更履歴ヘッダ記入、結合セル対応の値書き込み（`put`）、表の流し込み（`fill_table`）、出力（`save`）、プロジェクト識別（`PROJECT`）
- `build.py` — 全 `doc_*.py` の一括実行
- `doc_*.py` — 設計書1ブックにつき1モジュール。内容を構造化して持ち、`common` のヘルパで流し込む

## 注意

- openpyxl は保存時に Excel の図形（オートシェイプ・レイアウト図）を保持しません。図が主体のブック（画面レイアウト・遷移図・処理フロー・ジョブフロー・帳票レイアウト）は、テキスト・表の部分だけを埋め、図形キャンバスは空のままにしています。
- 生成物（`traditional-design/*.xlsx`）は Nablarch開発標準（CC BY-SA 4.0）の派生物です。出典表示は [traditional-design/NOTICE.md](../../examples/business-trip/traditional-design/NOTICE.md) を参照してください。空テンプレート（`_templates/`）はリポジトリに同梱せず build 時に取得します。この生成スクリプト自体はテンプレートを含まないため、その適用範囲外です。
