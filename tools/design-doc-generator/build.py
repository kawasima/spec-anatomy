"""出張申請システムの従来SI設計書一式を一括生成する。

各 doc_*.py を順に実行し、examples/business-trip/traditional-design/ に .xlsx を出力する。
テンプレートは同ディレクトリの _templates/（Nablarch開発標準の空書式, CC BY-SA 4.0）を読む。

    python build.py
"""
from __future__ import annotations

import glob
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    sys.path.insert(0, HERE)
    mods = sorted(
        os.path.basename(p)[:-3]
        for p in glob.glob(os.path.join(HERE, "doc_*.py"))
    )
    ok, fail = 0, 0
    for name in mods:
        mod = importlib.import_module(name)
        try:
            out = mod.build()
            print(f"OK   {name} -> {os.path.basename(out)}")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {name}: {e}")
            fail += 1
    print(f"--- {ok} ok, {fail} fail ---")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
