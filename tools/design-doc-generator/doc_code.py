"""コード設計書 — 出張申請システムのコードマスタ。

after（spec-model）では「費目」「費用負担区分」は data の OR、状態は型として8つに
分割され、役職は「役職なし申請」という業務概念になる。ここ（before）ではすべてが
コード値のフラットな列挙に潰れており、判定の根拠（Why）はどこにも書かれていない。
とくに申請状態の8コードは、after で型のOR分割になるものを1カラムのコード値で表している。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "コード設計書.xlsx"
OUTPUT = "コード設計書.xlsx"

# コードグループ定義。各グループの先頭行にだけ code_id/code_name/desc を置く。
GROUPS = [
    {
        "code_id": "C0010001",
        "code_name": "費目",
        "desc": "出張で発生する費用の費目を表す。",
        "values": [
            ("01", "交通費", "交通費"),
            ("02", "宿泊費", "宿泊費"),
            ("03", "交際費", "交際費"),
        ],
    },
    {
        "code_id": "C0020001",
        "code_name": "費用負担区分",
        "desc": "出張費用の負担元を表す。",
        "values": [
            ("01", "自社負担", "自社"),
            ("02", "先方負担", "先方"),
        ],
    },
    {
        "code_id": "C0030001",
        "code_name": "申請状態",
        # 「申請状態」1カラムで申請のライフサイクル全体を表す。after では型のOR分割になる。
        "desc": "出張申請の状態を表す。画面遷移・登録処理で本コードを更新する。",
        "values": [
            ("00", "下書き", "下書"),
            ("10", "申請済", "申請済"),
            ("20", "事前承認待ち", "承認待"),
            ("21", "事前承認不要", "承認不要"),
            ("30", "事前承認済", "承認済"),
            ("31", "事前承認却下", "却下"),
            ("40", "実績登録済", "実績済"),
            ("50", "最終承認済", "完了"),
            ("60", "経理連携済", "連携済"),
            ("90", "取消済", "取消"),
        ],
    },
    {
        "code_id": "C0040001",
        "code_name": "役職",
        # 事前承認判定は「役職コード = '99'」で役職なしを判断する（処理詳細に埋没）。
        "desc": "社員の役職を表す。",
        "values": [
            ("10", "一般社員", "一般"),
            ("20", "主任", "主任"),
            ("30", "課長", "課長"),
            ("40", "部長", "部長"),
            ("99", "役職なし", "なし"),
        ],
    },
]

# ja シートの列マップ（記入見本で確認）
COLMAP = {
    "C": "no",
    "D": "code_id",
    "F": "code_name",
    "J": "desc",
    "P": "value",
    "Q": "sort",
    "R": "name",
    "U": "abbr",
}
START_ROW = 12


def build_records() -> list[dict]:
    records: list[dict] = []
    no = 1
    for g in GROUPS:
        for j, (value, name, abbr) in enumerate(g["values"]):
            rec = {"no": no, "value": value, "sort": j + 1, "name": name, "abbr": abbr}
            if j == 0:
                rec["code_id"] = g["code_id"]
                rec["code_name"] = g["code_name"]
                rec["desc"] = g["desc"]
            records.append(rec)
            no += 1
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb["ja"]
    fill_header(ws, product_name="コード設計書")
    fill_table(ws, START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
