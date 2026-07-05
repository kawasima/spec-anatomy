"""採番一覧 — 出張申請システムの採番設計。

申請ID(BT_APPLICATION.application_id)を「BT＋業務日付＋連番6桁」でシーケンス採番する。
抜け番を許容するため、採番テーブルではなくシーケンスを用いる。判定ロジックと同様、
「なぜこの桁数・この初期化タイミングなのか」という根拠はここには書かれない。
"""
from __future__ import annotations

import datetime as _dt

from common import PROJECT, open_template, fill_header, fill_table, put, save

TEMPLATE = "採番一覧.xlsx"
OUTPUT = "採番一覧.xlsx"
PRODUCT = "採番一覧"

# 採番一覧の明細シートは '1'。列見出しは7行目、データは9行目から。
DATA_SHEET = "1"
START_ROW = 9
COLMAP = {
    "C": "no",
    "D": "target_id",
    "F": "name",
    "K": "format",
    "Q": "method",
    "W": "gap",
    "X": "sequence",
    "AD": "cyclic",
    "AG": "init",
    "AJ": "min",
    "AM": "max",
    "AP": "step",
    "AQ": "init_timing",
    "AS": "note",
}

RECORDS = [
    {
        "no": 1,
        "target_id": "BT01",
        "name": "申請ID",
        "format": "BT＋業務日付(YYYYMMDD)＋6桁ゼロ埋め連番",
        "method": "generateApplicationId",
        "gap": "可",
        "sequence": "APPLICATION_ID_SEQ",
        "cyclic": "無し",
        "init": 1,
        "min": 1,
        "max": 999999,
        "step": 1,
        "init_timing": "日次",
        "note": "出張申請登録時に採番する。抜け番を許容する。共通コンポーネントCC0004(申請ID採番)から呼び出す。",
    },
]


def fill_book_header(wb):
    """INDIRECTで変更履歴を参照する各シートのヘッダを埋める。

    変更履歴シートを真とし、そこへPJ名等と変更履歴の初回・修正行を書く。
    加えて明細・目次シートには実値を直接書き込み、再計算前でも表示されるようにする。
    """
    ch = wb["変更履歴"]
    put(ch, "E1", PROJECT["pj"])
    put(ch, "E2", PROJECT["system"])
    put(ch, "E3", PROJECT["subsystem"])
    put(ch, "S1", PRODUCT)
    # 変更履歴 明細（作成/変更 の日付・担当者はここから導出される）
    y, m, d = (int(x) for x in PROJECT["created"].split("-"))
    put(ch, "A8", 1)
    put(ch, "B8", "1.0版")
    put(ch, "D8", _dt.datetime(y, m, d))
    put(ch, "G8", "新規")
    put(ch, "J8", "-")
    put(ch, "Q8", "(新規作成)")
    put(ch, "AF8", PROJECT["author"])
    y2, m2, d2 = (int(x) for x in PROJECT["changed"].split("-"))
    put(ch, "A9", 2)
    put(ch, "B9", "1.1版")
    put(ch, "D9", _dt.datetime(y2, m2, d2))
    put(ch, "G9", "修正")
    put(ch, "J9", "-")
    put(ch, "Q9", "(記載内容の修正)")
    put(ch, "AF9", PROJECT["author"])
    # 明細・目次シートはINDIRECT式なので、実値で上書きして表示を確定させる
    for sn in (DATA_SHEET, "目次"):
        fill_header(wb[sn], product_name=PRODUCT)


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_book_header(wb)
    fill_table(wb[DATA_SHEET], START_ROW, COLMAP, RECORDS)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
