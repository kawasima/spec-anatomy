# 出典とライセンス

このディレクトリ（`traditional-design/`）に含まれる Excel 設計書は、**Nablarch開発標準**の
「設計ドキュメント（設計書フォーマット＆サンプル）」の空フォーマットを素材にしています。

- 素材元: Nablarch開発標準 / 030_設計ドキュメント
  <https://github.com/nablarch-development-standards/nablarch-development-standards/tree/main/030_%E8%A8%AD%E8%A8%88%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88>
- ライセンス: クリエイティブ・コモンズ 表示 - 継承 4.0 国際（CC BY-SA 4.0）
  <https://creativecommons.org/licenses/by-sa/4.0/>

## 内訳

- `_templates/*.xlsx` — Nablarch開発標準が提供する空の設計書フォーマット（`010_フォーマット`）。
  **リポジトリには同梱せず**（`.gitignore` 済み）、生成ツールが build 時に取得する。書式は無改変。
- `*.xlsx`（このディレクトリ直下） — 上記フォーマットに、本リポジトリの出張申請システム
  （`examples/business-trip/`）の内容を流し込んだもの。フォーマットの派生物にあたる。
  流し込んだ業務内容（出張申請の画面・テーブル・コード・業務ルール等）は架空であり、
  Nablarch開発標準のサンプル業務とは無関係。

## ライセンスの適用

CC BY-SA 4.0 の継承（ShareAlike）条件により、このディレクトリ配下の Excel 設計書
（フォーマットの派生物）は **CC BY-SA 4.0** のもとで提供されます。出典表示は上記のとおり。

この適用範囲はこのディレクトリに閉じています。リポジトリの他の部分（生成スクリプト
`tools/design-doc-generator/`、spec-model、shell、各種 Markdown 文書）には及びません。
