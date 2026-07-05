"""共通コンポーネント一覧 — 出張申請システムのサブシステム内共通コンポーネント。

事前承認要否判定・精算額計算といった業務判定ロジックが共通コンポーネントとして
切り出されている。判定の根拠（Why）は処理概要の自然言語に埋没しており、after では
CC0002 精算額計算のように概念ごと消えるものもある。ここ（before）では処理単位で
フラットに列挙する。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "共通コンポーネント一覧.xlsx"
OUTPUT = "共通コンポーネント一覧.xlsx"

# 「2. サブシステム内共通」シートに全コンポーネントを記入する。
SHEET = "2. サブシステム内共通"

COMPONENTS = [
    {
        "comp_id": "CC0001",
        "comp_name": "事前承認要否判定",
        "class_name": "PreApprovalDecision",
        "proc_name": "事前承認要否判定",
        "method_name": "needsPreApproval",
        "summary": "出張申請の予定費用合計・申請者の役職・費用負担区分から、上長の事前承認が必要かどうかを判定する。",
    },
    {
        "comp_id": "CC0002",
        "comp_name": "精算額計算",
        "class_name": "SettlementCalculator",
        "proc_name": "精算額計算",
        "method_name": "calculateSettlementAmount",
        "summary": "費用負担区分が自社負担の場合は実費、先方負担の場合は0円を精算額として返す。",
    },
    {
        "comp_id": "CC0003",
        "comp_name": "経理連携データ作成",
        "class_name": "AccountingLinkFileCreator",
        "proc_name": "経理連携データ作成",
        "method_name": "createAccountingData",
        "summary": "最終承認済の出張申請の立替額を、経理システム連携用のファイルに出力する。",
    },
    {
        "comp_id": "CC0004",
        "comp_name": "申請ID採番",
        "class_name": "ApplicationIdGenerator",
        "proc_name": "申請ID採番",
        "method_name": "generateApplicationId",
        "summary": "BT＋YYYYMMDD＋連番6桁の形式で、出張申請の申請IDを採番する。",
    },
]

# シート「2. サブシステム内共通」の列マップ（記入見本で確認）
COLMAP = {
    "C": "no",
    "D": "comp_id",
    "H": "comp_name",
    "L": "class_name",
    "P": "proc_name",
    "U": "method_name",
    "AB": "summary",
}
START_ROW = 8


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, c in enumerate(COMPONENTS):
        rec = dict(c)
        rec["no"] = i + 1
        records.append(rec)
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb[SHEET]
    fill_header(ws, product_name="共通コンポーネント一覧")
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
