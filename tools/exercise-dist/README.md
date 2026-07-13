# exercise-dist

「生成AI時代のドキュメンテーション」ハンズオンの受講者配布用サブセットを組むツールです。[examples/business-trip/](../../examples/business-trip/) から答え（`spec-model/` `shell/` `ai-collaboration/`）を除いた演習入力だけを集めて zip 化します。

## 使い方

```sh
cd tools/exercise-dist
python build.py
```

出力（いずれも `.gitignore` 済みの `build/` 配下）:

- `build/business-trip-exercise/` — 配布物の中身（ステージング）
- `build/business-trip-exercise.zip` — 配布用アーカイブ

## 配布物に含めるもの / 含めないもの

含める:

- `traditional-design/*.xlsx`（`_templates/` は除く）と `NOTICE.md`
- `design-html/*.html`
- `exercise/requirements.template.md` と受講者向け `README.md`（zip のルートに置く）

含めない（答え）:

- `spec-model/` `shell/` `ai-collaboration/`
- before/after の対応を書いた `traditional-design/README.md` と `design-html/README.md`

`build.py` は zip 化の前に、ステージング直下のエントリが許可した集合だけであること、答えや空テンプレート（`_templates/`）が混ざっていないことを検査し、混入があれば失敗します。

## 配り方

`build/business-trip-exercise.zip` を勉強会ページや共有ドライブに置いて配るか、中身を別の公開リポジトリに push して `git clone` / Download ZIP させます。どちらも `NOTICE.md`（CC BY-SA 4.0 の出典表示）が同梱されます。
