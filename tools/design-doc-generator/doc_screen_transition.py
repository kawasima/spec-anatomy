"""画面遷移図 — 出張申請サブシステム（BT）の画面取引ごとの遷移図。

本ブックは図（画面ノードと遷移矢印）を主体とする成果物であり、遷移そのものは
図形（オートシェイプ）で描画する。openpyxl は図形を保持できないため、遷移図の
図形キャンバスには一切手を触れない（図形が失われる点は既知の制約であり、遷移の
実体は examples/business-trip の Markdown 図で参照する）。

ただし各シートの見出しに続けて、遷移の対応関係を示すテキストの「遷移一覧」表を
記入する。下書き編集・差し戻し再申請・取消といった追加遷移は、この表部分に
反映する（'31'事前承認却下→BTS01編集→'10'申請済、'00'下書き→BTS01編集、
最終承認前の各状態→取消→'90'取消済 など）。

before（従来SI）では画面遷移が機能（取引）単位の図に分割され、状態遷移
（下書き→申請済→事前承認待ち→…）との対応は図の外に置かれる。ここでは
画面取引 BTS01〜BTS05 を1取引1シートで並べるにとどめる。
"""
from __future__ import annotations

from common import open_template, fill_history, put, save

TEMPLATE = "画面遷移図_BT_出張申請.xlsx"
OUTPUT = "画面遷移図_BT_出張申請.xlsx"
PRODUCT = "画面遷移図"

# 複製元の（空の）機能シート。見本では 1機能=1シートで、見出しは "N. 機能名(機能ID)"。
BASE_SHEET = "1.  機能名 (機能ID)"

# 遷移一覧（表部分）の記入位置。図形キャンバス（行6以降の描画領域）とは別に、
# 見出し直下から遷移の対応関係を3列（遷移元状態／操作／遷移先）で羅列する。
TRANS_TITLE_ROW = 7      # 「遷移一覧」見出し行
TRANS_HEADER_ROW = 8     # 列見出し行
TRANS_START_ROW = 9      # 明細開始行
TRANS_FROM_COL = "B"     # 遷移元（申請状態コード）
TRANS_EVT_COL = "K"      # 操作（イベント）
TRANS_TO_COL = "R"       # 遷移先（画面／申請状態）

# 画面取引（機能）。画面遷移図は画面取引ごとに1シート。
# transitions: (遷移元状態, 操作, 遷移先) の羅列。下書き編集・差し戻し再申請・取消を反映する。
FUNCTIONS = [
    {
        "func_id": "BTS01",
        "func_name": "出張申請登録",
        "transitions": [
            ("'00' 下書き（一覧から行選択）", "編集モード表示", "WBT0101 出張申請登録（編集）"),
            ("WBT0101 編集", "下書き保存", "'00' 下書き"),
            ("WBT0101 編集", "破棄", "（削除。以降の遷移なし）"),
            ("WBT0101 編集", "申請する", "'10' 申請済"),
            ("'31' 事前承認却下（一覧から行選択）", "差し戻し修正・編集モード表示",
             "WBT0101 出張申請登録（編集）"),
            ("WBT0101 編集（差し戻し）", "再申請", "'10' 申請済"),
        ],
    },
    {"func_id": "BTS02", "func_name": "事前承認"},
    {"func_id": "BTS03", "func_name": "出張実績登録"},
    {"func_id": "BTS04", "func_name": "最終承認"},
    {
        "func_id": "BTS05",
        "func_name": "出張申請一覧",
        "transitions": [
            ("'00' 下書き", "行クリック", "WBT0101 出張申請登録（編集）"),
            ("'31' 事前承認却下", "行クリック", "WBT0101 出張申請登録（編集・差し戻し修正）"),
            ("'20' 事前承認待ち", "行クリック", "WBT0201 事前承認"),
            ("'21'/'30'", "行クリック", "WBT0301 出張実績登録"),
            ("'40' 実績登録済", "行クリック", "WBT0401 最終承認"),
            ("'10'〜'40'（最終承認前）", "取消", "'90' 取消済"),
        ],
    },
]


def sheet_title(idx: int, f: dict) -> str:
    """見本の見出し規約 "N. 機能名(機能ID)" に合わせる（名称と括弧の間に空白なし）。"""
    return f"{idx}. {f['func_name']}({f['func_id']})"


def fill_transitions(ws, transitions: list[tuple]):
    """遷移一覧（表部分）を記入する。図形キャンバスには触れない。"""
    put(ws, f"{TRANS_FROM_COL}{TRANS_TITLE_ROW}",
        "遷移一覧（遷移矢印は図形で描画。ここでは遷移の対応関係を表で示す）")
    put(ws, f"{TRANS_FROM_COL}{TRANS_HEADER_ROW}", "遷移元（申請状態）")
    put(ws, f"{TRANS_EVT_COL}{TRANS_HEADER_ROW}", "操作")
    put(ws, f"{TRANS_TO_COL}{TRANS_HEADER_ROW}", "遷移先（画面／申請状態）")
    for i, (frm, evt, to) in enumerate(transitions):
        r = TRANS_START_ROW + i
        put(ws, f"{TRANS_FROM_COL}{r}", frm)
        put(ws, f"{TRANS_EVT_COL}{r}", evt)
        put(ws, f"{TRANS_TO_COL}{r}", to)


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
        # 機能ID・機能名の表領域（見出し）。遷移図の図形には触れない。
        put(ws, "B5", title)
        # 遷移一覧（表部分）。追加遷移を持つ取引のみ記入する。
        if f.get("transitions"):
            fill_transitions(ws, f["transitions"])

    fill_toc(wb, titles)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
