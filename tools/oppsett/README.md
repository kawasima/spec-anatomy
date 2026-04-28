# oppsett — 画面設計書レイアウト支援ツール

デザインHTML（Figmaエクスポートまたは手書きのHTML）を入力として、番号付き赤枠オーバーレイをマークアップし、Spec Set の screen.md を生成するインタラクティブツールです。

## このツールの位置付け

spec-anatomy の Spec Set は、Shell の画面設計を [docs/spec-set/shell/ui/templates/screen.md](../../docs/spec-set/shell/ui/templates/screen.md) のフォーマットで書きます。このフォーマットは「項目テーブル＋画面イベント＋業務的事前条件・事後条件」を中心とした構造化された Markdown ですが、レイアウト図と項目表を手で対応づけるのは認識ズレが起きやすく、SIer 現場のボトルネックでした。

oppsett はこの工程を支援します。

- ブラウザでデザインHTMLを表示
- ユーザーが要素を選択すると赤枠でオーバーレイが付き、番号が振られる
- 番号ごとに項目名・種別・派生元・編集仕様をフォームで入力
- 完了すると、番号付きオーバーレイ付き HTML と screen.md の項目テーブルを出力

## SMDD の Core/Shell との関係

oppsett は **Shell（画面設計）の作業支援ツール**です。Core（仕様モデル）の `data` 定義から派生元を補完するのが理想ですが、現バージョンでは派生元はユーザーが手で入力します。将来的には [docs/examples/business-trip/spec-model/business-trip.md](../../docs/examples/business-trip/spec-model/business-trip.md) のような仕様モデルファイルを読み込んで補完候補を出す機能を加える予定です。

## 使い方

### 起動

リポジトリをローカルで開き、`tools/oppsett/index.html` をブラウザで直接開きます。ビルドツールやサーバ不要です。

```sh
open tools/oppsett/index.html
# または
python3 -m http.server -d tools/oppsett 8000  # localhost:8000 で起動
```

### 操作の流れ

1. **デザインHTMLを読み込む**: ツールバーから読み込むか、ドロップゾーンにドラッグ&ドロップ
2. **画面項目グループを作る**: サイドパネルで「ヘッダ領域」「操作領域」などのグループを定義
3. **項目をマークアップ**: デザインHTML上の要素にホバーして仮選択、Enter または クリックで確定すると赤枠と番号が付く
   - ↑↓←→ キーで親子・兄弟要素に移動できる
   - Esc で選択解除
4. **項目詳細を入力**: 番号ごとに項目名・種別・派生元・編集仕様などをフォーム入力
5. **出力**:
   - **screen.md 書出**: Spec Set 準拠の screen.md を出力
   - **オーバーレイHTML出力**: 番号付き赤枠オーバーレイ付きの HTML を出力（インタラクティブ確認用）
   - **レイアウトPNG出力**: 番号付きオーバーレイ付きの PNG を出力（screen.md に画像として埋め込み用）
   - **プロジェクト保存**: 作業状態を JSON で保存（再開時に読み込める）

### 既存の screen.md を編集する

ツールバーの「screen.md 読込」から既存の screen.md を読み込めます。項目テーブルがパースされ、デザインHTMLと突き合わせて再編集できます。

## 出力フォーマット

### screen.md

[docs/spec-set/shell/ui/templates/screen.md](../../docs/spec-set/shell/ui/templates/screen.md) のテンプレートに準拠した Markdown を出力します。項目テーブルは次の列を持ちます。

| No | 項目名 | 種別 | 派生元 | 編集仕様 | 必須 | 初期値 | 表示条件 |
|----|--------|------|--------|----------|------|--------|----------|

### オーバーレイHTML

入力デザインHTMLに `<style>` で赤枠スタイルを追加し、各項目位置に `<div>` で枠と番号バッジを描画したHTMLを出力します。インタラクティブな確認用。screen.md の `## レイアウトバリアント` から相対パスで参照する想定です。

### レイアウトPNG

iframe 内にオーバーレイを注入した状態を [html2canvas](https://html2canvas.hertzen.com/) でキャプチャしてPNGを出力します。GitHub などの Markdown レンダラで画像として直接表示できます。screen.md の各バリアント節に次の形式で埋め込みます。

```markdown
### PC版

![SCREEN-BT-02 PC版レイアウト](layout/SCREEN-BT-02-pc.overlay.png)

[インタラクティブHTML](layout/SCREEN-BT-02-pc.overlay.html) — 番号は下の項目テーブルの No 列と対応
```

PNGはバイナリなので Git でも追跡対象にして問題ありませんが、画面ごとに数百KB程度になります。

## 動作確認

[docs/examples/business-trip/shell/ui/layout/SCREEN-BT-02-pc.html](../../docs/examples/business-trip/shell/ui/layout/SCREEN-BT-02-pc.html) を読み込んで、対応する [SCREEN-BT-02 の screen.md](../../docs/examples/business-trip/shell/ui/business-trip-detail-screen.md) と一致するか確認できます。デザインHTML から screen.md を生成し、既存の screen.md と項目テーブルが一致すれば往復可能性が確認できます。

## 開発

ピュア JavaScript の ESModule 構成で、ビルドツールを使いません。

```text
tools/oppsett/
├── index.html              ─ エントリポイント
├── vendor/
│   └── html2canvas.min.js  ─ PNG キャプチャ用（MIT ライセンス）
└── src/
    ├── main.js             ─ アプリ起動・イベント配線
    ├── state.js            ─ アプリ状態管理（Pub/Sub）
    ├── canvas.js           ─ デザインHTMLの表示と要素選択
    ├── overlay.js          ─ 赤枠オーバーレイ描画
    ├── inspector.js        ─ ホバー仮選択・キーボード移動
    ├── dom-walker.js       ─ DOM の親子兄弟ナビゲーション
    ├── sidepanel.js        ─ サイドパネル（グループ・項目・詳細フォーム）
    ├── exporter.js         ─ オーバーレイHTML出力
    ├── screen-md-writer.js ─ screen.md 書き出し
    ├── screen-md-parser.js ─ screen.md 読み込み
    ├── storage.js          ─ プロジェクトJSONの保存・復元
    └── styles.css
```

## 制約と既知の制限

- 仕様モデル（Core）からの派生元の自動補完は未実装
- 1画面1ドキュメントの想定。複数デバイス（PC/スマホ/タブレット）の同時編集は未対応
- 画面遷移（screen-transitions.md）の生成は対象外
- HTML の構造が大きく変わると、保存済み項目の rect 情報がずれる可能性がある

## 関連ドキュメント

- [docs/spec-set/shell/ui/templates/screen.md](../../docs/spec-set/shell/ui/templates/screen.md): 出力フォーマットの規約
- [docs/spec-set/shell/ui/README.md](../../docs/spec-set/shell/ui/README.md): UI への変換規約
- [docs/examples/business-trip/shell/ui/](../../docs/examples/business-trip/shell/ui/): screen.md のサンプル
