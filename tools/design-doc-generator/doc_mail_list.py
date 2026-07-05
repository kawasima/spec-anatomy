"""メール一覧 — 出張申請システムのメール。

事前承認依頼・却下通知・最終承認依頼の3通。いずれも申請者と上長の間で送受信する。
送信元取引は、事前承認依頼が出張申請登録（BTS01）、却下通知が事前承認（BTS02）、
最終承認依頼が出張実績登録（BTS03）。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "メール一覧.xlsx"
OUTPUT = "メール一覧.xlsx"

MAILS = [
    {
        "mail_id": "MBT01",
        "mail_name": "事前承認依頼メール",
        "summary": "事前承認が必要になった出張申請について、申請者から上長へ承認を依頼する。",
        "to": "上長",
        "from": "申請者",
        "err_to": "システム運用担当",
        "encrypt": "否",
        "format": "TEXT",
        "attach": "無",
        "template_id": "TBT01",
        "proc_type": "オンライン",
        "timing": "随時",
        "src_txn_id": "BTS01",
        "src_txn_name": "出張申請登録",
    },
    {
        "mail_id": "MBT02",
        "mail_name": "事前承認却下通知メール",
        "summary": "上長が出張申請の事前承認を却下したことを、申請者へ通知する。",
        "to": "申請者",
        "from": "上長",
        "err_to": "システム運用担当",
        "encrypt": "否",
        "format": "TEXT",
        "attach": "無",
        "template_id": "TBT02",
        "proc_type": "オンライン",
        "timing": "随時",
        "src_txn_id": "BTS02",
        "src_txn_name": "事前承認",
    },
    {
        "mail_id": "MBT03",
        "mail_name": "最終承認依頼メール",
        "summary": "出張実績登録が完了した出張申請について、申請者から上長へ最終承認を依頼する。",
        "to": "上長",
        "from": "申請者",
        "err_to": "システム運用担当",
        "encrypt": "否",
        "format": "TEXT",
        "attach": "無",
        "template_id": "TBT03",
        "proc_type": "オンライン",
        "timing": "随時",
        "src_txn_id": "BTS03",
        "src_txn_name": "出張実績登録",
    },
]

# シート '1' の列マップ（記入見本で確認）。ヘッダ行7・サブヘッダ行8・データ開始行9。
COLMAP = {
    "C": "no",
    "D": "mail_id",
    "G": "mail_name",
    "M": "summary",
    "V": "to",
    "Y": "from",
    "AB": "err_to",
    "AE": "encrypt",
    "AG": "format",
    "AI": "attach",
    "AK": "template_id",
    "AN": "proc_type",
    "AQ": "timing",
    "AT": "src_txn_id",
    "AW": "src_txn_name",
}
START_ROW = 9


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, m in enumerate(MAILS):
        rec = dict(m)
        rec["no"] = i + 1
        records.append(rec)
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb["1"]
    fill_header(ws, product_name="メール一覧")
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
