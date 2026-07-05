"""画面一覧 — 出張申請システムの画面を機能（画面取引）単位で列挙する。

登録・実績登録は入力→確認→完了の3画面取引。画面IDはDBカラム駆動の設計に対応し、
各画面は対応する取引に属する。after（spec-model）では画面遷移は状態型で表されるが、
ここ（before）では画面をフラットに列挙するのみで、遷移の根拠は記述しない。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "画面一覧.xlsx"
OUTPUT = "画面一覧.xlsx"

# 機能（画面取引）ごとの画面グループ。機能ID/機能名は各グループ先頭行にのみ置く。
GROUPS = [
    {
        "func_id": "BTS01",
        "func_name": "出張申請登録",
        "screens": [
            ("WBT0101", "出張申請登録画面", "出張目的・出張期間・費用負担区分・予定費用を入力する。"),
            ("WBT0102", "出張申請登録確認画面", "入力された出張申請内容を表示し、登録内容を確認する。"),
            ("WBT0103", "出張申請登録完了画面", "出張申請の登録完了メッセージを表示する。"),
        ],
    },
    {
        "func_id": "BTS02",
        "func_name": "事前承認",
        "screens": [
            ("WBT0201", "出張申請事前承認画面", "事前承認対象の出張申請内容を表示し、承認または却下を行う。"),
        ],
    },
    {
        "func_id": "BTS03",
        "func_name": "出張実績登録",
        "screens": [
            ("WBT0301", "出張実績登録画面", "出張実績費用を入力する。"),
            ("WBT0302", "出張実績登録確認画面", "入力された出張実績内容を表示し、登録内容を確認する。"),
            ("WBT0303", "出張実績登録完了画面", "出張実績の登録完了メッセージを表示する。"),
        ],
    },
    {
        "func_id": "BTS04",
        "func_name": "最終承認",
        "screens": [
            ("WBT0401", "出張申請最終承認画面", "実績登録済の出張申請内容・金額を表示し、最終承認を行う。"),
        ],
    },
    {
        "func_id": "BTS05",
        "func_name": "出張申請一覧",
        "screens": [
            ("WBT0501", "出張申請一覧画面", "検索条件に該当する出張申請の一覧を表示する。"),
        ],
    },
]

# シート '1' の列マップ（記入見本で確認）
COLMAP = {
    "C": "no",
    "D": "func_id",
    "G": "func_name",
    "L": "screen_id",
    "O": "screen_name",
    "T": "desc",
}
START_ROW = 8


def build_records() -> list[dict]:
    records: list[dict] = []
    no = 1
    for g in GROUPS:
        for j, (sid, sname, desc) in enumerate(g["screens"]):
            rec = {"no": no, "screen_id": sid, "screen_name": sname, "desc": desc}
            if j == 0:
                # 機能ID・機能名は結合セルの先頭行にのみ記入する。
                rec["func_id"] = g["func_id"]
                rec["func_name"] = g["func_name"]
            records.append(rec)
            no += 1
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb["1"]
    fill_header(ws, product_name="画面一覧")
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
