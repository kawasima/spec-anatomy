"""外部インタフェース一覧 — 出張申請システムが外部システムと授受するI/Fの一覧。

本システムの外部I/Fは経理システムへの連携ファイル1本のみ。最終承認済の申請の立替精算額を
日次バッチ（BTB01 経理連携ファイル作成）でファイル出力し、経理システムへ渡す。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "外部インタフェース一覧.xlsx"
OUTPUT = "外部インタフェース一覧.xlsx"

# シート「1」の列マップ（記入見本で確認）。
# No.=B, ファイルID/電文ID=C, 外部I/F名=F, 入出力種別=M, 相手先=O, 媒体=T, 授受方式=V,
# 暗号化有無=Z, 文字コード=AB, 処理サイクル(サイクル=AE/詳細=AH),
# データ量(ﾚｺｰﾄﾞ長=AN/件数=AP), ファイル保存期間=AT, 備考=AX
COLMAP = {
    "B": "no",
    "C": "file_id",
    "F": "if_name",
    "M": "io",
    "O": "partner",
    "T": "media",
    "V": "method",
    "Z": "encrypt",
    "AB": "charcode",
    "AE": "cycle",
    "AH": "cycle_detail",
    "AN": "rec_len",
    "AP": "count",
    "AT": "keep_days",
    "AX": "remark",
}
# 空テンプレートは見出しが7行目・小見出しが8行目のため、データは9行目から。
START_ROW = 9

INTERFACES = [
    {
        "no": 1,
        "file_id": "IBT01",
        "if_name": "経理システム連携ファイル",
        "io": "出力",
        "partner": "経理システム",
        "media": "ファイル",
        "method": "-",
        "encrypt": "無し",
        "charcode": "UTF-8",
        "cycle": "日次",
        "cycle_detail": "日次バッチ（毎営業日）",
        "rec_len": "-",
        "count": "-",
        "keep_days": "-",
        "remark": "最終承認済の申請の立替精算額を経理システムへ連携する。",
    },
]


def build() -> str:
    wb = open_template(TEMPLATE)
    ws = wb["1"]
    fill_header(ws, product_name="外部インタフェース一覧")
    fill_table(ws, START_ROW, COLMAP, INTERFACES)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
