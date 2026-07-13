"""「生成AI時代のドキュメンテーション」ハンズオンの受講者配布用サブセットを組む。

examples/business-trip/ から答え（spec-model / shell / ai-collaboration）を除いた
演習入力だけを build/business-trip-exercise/ にステージングし、zip 化する。

    python build.py

出力（いずれも .gitignore 済みの build/ 配下）:
  build/business-trip-exercise/        配布物の中身（ステージング）
  build/business-trip-exercise.zip     配布用アーカイブ
"""
from __future__ import annotations

import glob
import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "examples", "business-trip")
OUT_DIR = os.path.join(ROOT, "build")
BUNDLE_NAME = "business-trip-exercise"
BUNDLE = os.path.join(OUT_DIR, BUNDLE_NAME)
ZIP = os.path.join(OUT_DIR, BUNDLE_NAME + ".zip")

# 配布物の直下に現れてよいエントリ。ここに無いものが混ざったら失敗させる。
ALLOWED_TOP = {"traditional-design", "design-html", "requirements.template.md", "README.md"}
# 答え。配布物のどこにも現れてはいけない。
FORBIDDEN = ("spec-model", "shell", "ai-collaboration")


def main() -> int:
    if os.path.exists(BUNDLE):
        shutil.rmtree(BUNDLE)
    os.makedirs(BUNDLE)

    added: list[str] = []

    # 1. 従来SI設計書一式: *.xlsx（_templates/ は除く）と NOTICE.md
    #    before/after の対応を書いた README.md は答えを示唆するので含めない。
    td_src = os.path.join(SRC, "traditional-design")
    td_dst = os.path.join(BUNDLE, "traditional-design")
    os.makedirs(td_dst)
    for x in sorted(glob.glob(os.path.join(td_src, "*.xlsx"))):
        shutil.copy2(x, td_dst)
        added.append(os.path.join("traditional-design", os.path.basename(x)))
    shutil.copy2(os.path.join(td_src, "NOTICE.md"), td_dst)
    added.append(os.path.join("traditional-design", "NOTICE.md"))

    # 2. 画面デザインHTML: *.html（README.md は before/after 対応表なので含めない）
    dh_dst = os.path.join(BUNDLE, "design-html")
    os.makedirs(dh_dst)
    for h in sorted(glob.glob(os.path.join(SRC, "design-html", "*.html"))):
        shutil.copy2(h, dh_dst)
        added.append(os.path.join("design-html", os.path.basename(h)))

    # 3. 演習の雛形と受講者向けREADME → 配布物のルートへ
    ex_src = os.path.join(SRC, "exercise")
    for name in ("requirements.template.md", "README.md"):
        shutil.copy2(os.path.join(ex_src, name), os.path.join(BUNDLE, name))
        added.append(name)

    _guard()

    # 4. zip 化（アーカイブ内のルートを business-trip-exercise/ にする）
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in os.walk(BUNDLE):
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                arc = os.path.join(BUNDLE_NAME, os.path.relpath(full, BUNDLE))
                zf.write(full, arc)

    print(f"staged {len(added)} files -> {os.path.relpath(BUNDLE, ROOT)}/")
    for rel in added:
        print(f"  {rel}")
    print(f"zip -> {os.path.relpath(ZIP, ROOT)}")
    return 0


def _guard() -> None:
    """答えの混入と想定外エントリを検査する。混入があれば止める。"""
    top = set(os.listdir(BUNDLE))
    extra = top - ALLOWED_TOP
    if extra:
        raise SystemExit(f"想定外の直下エントリが混ざっています: {sorted(extra)}")

    for dirpath, dirnames, filenames in os.walk(BUNDLE):
        for name in dirnames + filenames:
            low = name.lower()
            if any(f in low for f in FORBIDDEN):
                rel = os.path.relpath(os.path.join(dirpath, name), BUNDLE)
                raise SystemExit(f"答えが混入しています: {rel}")
            if name == "_templates":
                raise SystemExit("CC BY-SA の空テンプレート（_templates/）が混入しています")


if __name__ == "__main__":
    raise SystemExit(main())
