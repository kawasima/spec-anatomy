"""帳票一覧 — 出張申請システムの帳票。

最終承認済の出張申請1件を経理提出用に出力する出張精算書のみ。出力元取引は
最終承認（BTS04）。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "帳票一覧.xlsx"
OUTPUT = "帳票一覧.xlsx"

REPORTS = [
    {
        "report_id": "RBT01",
        "report_name": "出張精算書",
        "summary": "最終承認済の出張申請1件を、経理提出用に出力する。立替額と精算額を記載する。",
        "form": "PDF",
        "paper_size": "A4",
        "orientation": "縦",
        "pages": 1,
        "proc_type": "オンライン",
        "timing": "随時",
        "src_txn_id": "BTS04",
        "src_txn_name": "最終承認",
    },
]

# シート '1' の列マップ（記入見本で確認）。ヘッダ行7・サブヘッダ行8・データ開始行9。
COLMAP = {
    "C": "no",
    "D": "report_id",
    "G": "report_name",
    "M": "summary",
    "X": "form",
    "AA": "paper_size",
    "AC": "orientation",
    "AE": "pages",
    "AH": "proc_type",
    "AL": "timing",
    "AO": "src_txn_id",
    "AR": "src_txn_name",
}
START_ROW = 9


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, r in enumerate(REPORTS):
        rec = dict(r)
        rec["no"] = i + 1
        records.append(rec)
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb["1"]
    fill_header(ws, product_name="帳票一覧")
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
