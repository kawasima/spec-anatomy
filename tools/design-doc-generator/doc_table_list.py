"""テーブル一覧 — 出張申請システムの物理テーブルの一覧。

Nablarch開発標準のテーブル一覧に、出張申請サブシステムが主管するテーブルを
論理名・物理名で記載する。従来SIの設計なので、状態や承認者はコードカラム・
NULL許容カラムとして BT_APPLICATION に持たせている（詳細はテーブル定義書）。
"""
from __future__ import annotations

import datetime

from common import open_template, put, fill_table, save
from common import PROJECT

TEMPLATE = "テーブル一覧.xlsx"
OUTPUT = "テーブル一覧.xlsx"

TABLE_SHEET = "1"
START_ROW = 9

# 「1. テーブル一覧」シートの列マップ（記入見本・空テンプレで確認）。
# 主管サブシステムはID=D / サブシステム名=E（E:I結合）、論理=J（J:R結合）、
# 物理=S（S:AA結合）、備考=AB（AB:AH結合）。
COLMAP = {
    "C": "no",
    "D": "subsystem_id",
    "E": "subsystem_name",
    "J": "logical",
    "S": "physical",
    "AB": "remark",
}

TABLES = [
    ("出張申請", "BT_APPLICATION",
     "出張申請のヘッダ。申請状態・承認者・提出/承認日時をコード/NULL許容カラムで保持する。"),
    ("出張予定費用", "BT_PLANNED_COST",
     "出張申請の予定費用明細。申請IDと明細番号を主キーとする。"),
    ("出張実績費用", "BT_ACTUAL_COST",
     "出張後の実績費用明細。申請IDと明細番号を主キーとする。"),
    ("社員", "BT_EMPLOYEE",
     "社員マスタ。役職・所属部門と上長（社員自己参照）を保持する。"),
    ("部門", "BT_DEPARTMENT",
     "部門マスタ。部門コードと部門名を保持する。"),
    ("出張者", "BT_TRAVELER",
     "出張申請の出張者明細。申請IDと明細番号を主キーとし、出張者の社員IDを保持する。"),
]


def fill_history(wb, product_name: str):
    """変更履歴シートにプロジェクト識別と変更履歴を記入する。

    各コンテンツシートの1〜3行目ヘッダは変更履歴シートの値をINDIRECTで参照する
    数式のため、値の書き込み先は変更履歴シートとする。
    """
    ws = wb["変更履歴"]
    put(ws, "E1", PROJECT["pj"])
    put(ws, "E2", PROJECT["system"])
    put(ws, "E3", PROJECT["subsystem"])
    put(ws, "S1", product_name)
    put(ws, "A8", 1)
    put(ws, "B8", "1.0版")
    put(ws, "D8", datetime.date.fromisoformat(PROJECT["created"]))
    put(ws, "G8", "新規")
    put(ws, "J8", "-")
    put(ws, "Q8", "(新規作成)")
    put(ws, "AF8", PROJECT["author"])
    put(ws, "A9", 2)
    put(ws, "B9", "1.1版")
    put(ws, "D9", datetime.date.fromisoformat(PROJECT["changed"]))
    put(ws, "G9", "変更")
    put(ws, "J9", "1. テーブル一覧")
    put(ws, "Q9", "・出張申請システムのテーブルを追加")
    put(ws, "AF9", PROJECT["author"])


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, (logical, physical, remark) in enumerate(TABLES):
        records.append({
            "no": i + 1,
            "subsystem_id": PROJECT["subsystem_id"],
            "subsystem_name": PROJECT["subsystem"],
            "logical": logical,
            "physical": physical,
            "remark": remark,
        })
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, "テーブル一覧")
    ws = wb[TABLE_SHEET]
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
