"""システム処理フロー — 出張申請サブシステム（BT）の機能（取引）ごとの処理フロー図。

本ブックは各機能の処理の流れ（画面・共通部品・DBアクセスの連鎖）を図形で描画する
成果物である。openpyxl は図形を保持できないため、ここではテキストの表領域
（各機能の機能ID・機能名＝各シートの見出しと目次）のみを記入し、処理フロー図の
図形キャンバスには手を触れない。処理フローの実体は examples/business-trip の
Markdown 図で参照する。

対象は画面取引 BTS01〜BTS05 とバッチ取引 BTB01 の6機能。1機能1シートで並べる。
"""
from __future__ import annotations

from common import open_template, fill_history, put, save

TEMPLATE = "システム処理フロー_BT_出張申請.xlsx"
OUTPUT = "システム処理フロー_BT_出張申請.xlsx"
PRODUCT = "システム処理フロー"

# 複製元の（空の）機能シート。テンプレでは名称 '1'。見本の見出しは "N. 機能名(機能ID)"。
BASE_SHEET = "1"

FUNCTIONS = [
    {"func_id": "BTS01", "func_name": "出張申請登録"},
    {"func_id": "BTS02", "func_name": "事前承認"},
    {"func_id": "BTS03", "func_name": "出張実績登録"},
    {"func_id": "BTS04", "func_name": "最終承認"},
    {"func_id": "BTS05", "func_name": "出張申請一覧"},
    {"func_id": "BTB01", "func_name": "経理連携ファイル作成"},
]


def sheet_title(idx: int, f: dict) -> str:
    return f"{idx}. {f['func_name']}({f['func_id']})"


def fill_toc(wb, titles: list[str]):
    """目次シートに各機能シートの見出しを記入する（見本では B7 から2行おき）。"""
    toc = wb["目次"]
    for i, title in enumerate(titles):
        put(toc, f"B{7 + i * 2}", title)


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    base = wb[BASE_SHEET]
    sheets = [base]
    for _ in range(len(FUNCTIONS) - 1):
        sheets.append(wb.copy_worksheet(base))

    titles: list[str] = []
    for i, (ws, f) in enumerate(zip(sheets, FUNCTIONS), start=1):
        title = sheet_title(i, f)
        titles.append(title)
        ws.title = title
        # 機能ID・機能名の表領域（見出し）。処理フロー図の図形には触れない。
        put(ws, "B5", title)

    fill_toc(wb, titles)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
