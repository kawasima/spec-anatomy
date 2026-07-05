"""システム機能一覧 — 出張申請システムの機能（取引）体系。

before（従来SI）では、業務の単位が「機能＝取引」というフラットな一覧に潰れている。
各取引の処理方式（画面／バッチ）だけが分類軸で、なぜその取引が必要か（Why）や、
状態遷移のどこに位置するかは、この一覧からは読み取れない。after では出張申請の
ライフサイクル上の操作として型に整理されるが、ここでは6つの取引が並ぶだけである。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "システム機能一覧.xlsx"
OUTPUT = "システム機能一覧.xlsx"

# 各取引を1機能として記入する（1機能1取引）。取引ID＝画面ID/バッチID。
FUNCTIONS = [
    {
        "func_id": "BTS01",
        "func_name": "出張申請登録",
        "func_desc": "出張の申請を登録する。入力→確認→完了の3画面遷移で行い、"
        "確認時に事前承認要否を判定する。編集モードでは'00'下書きの保存・破棄、"
        "および'31'事前承認却下の差し戻し修正・再申請を行う。",
        "tx_id": "WBT0101",
        "tx_name": "出張申請登録",
        "tx_desc": "-",
        "method": "画面",
    },
    {
        "func_id": "BTS02",
        "func_name": "事前承認",
        "func_desc": "上長が出張申請の内容・金額を確認し、事前承認または却下を行う。",
        "tx_id": "WBT0201",
        "tx_name": "事前承認",
        "tx_desc": "-",
        "method": "画面",
    },
    {
        "func_id": "BTS03",
        "func_name": "出張実績登録",
        "func_desc": "出張後に実績費用を登録する。入力→確認→完了の3画面遷移で行う。",
        "tx_id": "WBT0301",
        "tx_name": "出張実績登録",
        "tx_desc": "-",
        "method": "画面",
    },
    {
        "func_id": "BTS04",
        "func_name": "最終承認",
        "func_desc": "上長が出張実績の内容・金額を確認し、最終承認または却下を行う。",
        "tx_id": "WBT0401",
        "tx_name": "最終承認",
        "tx_desc": "-",
        "method": "画面",
    },
    {
        "func_id": "BTS05",
        "func_name": "出張申請一覧",
        "func_desc": "出張申請を検索し、一覧表示する。一覧から各画面へ遷移するほか、"
        "最終承認前（'10'〜'40'）の申請の取消を行う。",
        "tx_id": "WBT0501",
        "tx_name": "出張申請一覧",
        "tx_desc": "-",
        "method": "画面",
    },
    {
        "func_id": "BTB01",
        "func_name": "経理連携ファイル作成",
        "func_desc": "最終承認済の立替精算額を集計し、経理システム連携ファイルを"
        "作成する。日次バッチで起動する。",
        "tx_id": "BBT0601",
        "tx_name": "経理連携ファイル作成",
        "tx_desc": "-",
        "method": "バッチ",
    },
]

# sheet '1' の列マップ。ヘッダは 7〜8 行の縦結合、データ開始行=9（記入見本で確認）。
COLMAP = {
    "B": "no",
    "C": "func_id",
    "E": "func_name",
    "J": "func_desc",
    "Q": "tx_id",
    "S": "tx_name",
    "Y": "tx_desc",
    "AG": "method",
    "AJ": "remark",
}
START_ROW = 9


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, f in enumerate(FUNCTIONS):
        rec = dict(f)
        rec["no"] = i + 1
        records.append(rec)
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    # ヘッダは 変更履歴 シートに書き、他シートは INDIRECT 参照で解決される。
    fill_header(wb["変更履歴"], product_name="システム機能一覧")
    fill_table(wb["1"], START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
