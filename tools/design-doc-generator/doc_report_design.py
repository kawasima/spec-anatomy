"""帳票設計書 — RBT01 出張精算書。

最終承認済（appl_status='50'）の出張申請1件を、経理提出用にA4縦で出力する帳票。
Nablarch開発標準の空テンプレート「帳票設計書」に、1.概要 / 3.項目定義（項目グループ設計・
項目設計）の表を流し込む。2.レイアウト（帳票イメージ図）のシートは、openpyxlが図形を保持
できないため空のまま残す（図の領域には触れない）。

従来SIの設計をそのまま写す。特に次の点は「直す」対象ではなく「そのまま書く」対象:
- 画面項目・帳票項目はテーブル駆動。取得元に物理テーブル.カラムを書く。
- 精算額は自社負担なら実費合計・先方負担なら0を出力する、という条件をWhyなしで淡々と書く
  （共通コンポーネントCC0002：精算額計算に対応）。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save

TEMPLATE = "帳票設計書_RBT01_出張精算書.xlsx"
OUTPUT = "帳票設計書_RBT01_出張精算書.xlsx"
PRODUCT = "帳票設計書\n出張精算書/RBT01"

OVERVIEW_SHEET = "1. 概要"
ITEM_SHEET = "3. 項目定義"


# ------------------------------------------------------------------
# 1. 概要
# ------------------------------------------------------------------
# ラベルC7〜C16に対する値セルは K列（K7:AH7 …）。
OVERVIEW = {
    "K7": "RBT01",
    "K8": "出張精算書",
    "K9": ("最終承認済（BT_APPLICATION.appl_status='50'）の出張申請1件を、経理提出用にA4縦で"
           "出力する帳票。申請者の出張予定費用・実績費用、および精算額を1ページに記載する。"),
    "K10": "PDF",
    "K11": "A4",
    "K12": "縦",
    "K13": "1（予定・実績費用明細の件数により改ページする）",
    "K14": "オンライン／バッチ",
    "K15": "最終承認時（BTS04 最終承認）、または経理連携バッチ（BTB01 経理連携ファイル作成）実行時",
    "K16": "BTS04/最終承認\nBTB01/経理連携ファイル作成",
}


# ------------------------------------------------------------------
# 3.1 項目グループ設計
# ------------------------------------------------------------------
GROUP_START = 10            # 最初のグループ明細行（唯一のスタイル付き行）
GROUP_CLONE_SRC = 10
GROUP_COL = {"D": "no", "E": "name", "I": "cond",
             "O": "page2", "R": "unit", "Y": "count", "AD": "order"}


def group(no, name, cond, page2, unit, count, order):
    return {"no": no, "name": name, "cond": cond,
            "page2": page2, "unit": unit, "count": count, "order": order}


GROUPS = [
    group(1, "申請・精算情報", "常時出力", "‐", "‐", "‐", "‐"),
    group(2, "予定費用明細", "常時出力", "有（改ページ時に見出しを再出力）",
          "BT_PLANNED_COSTの1レコード", "可変（申請の予定費用明細件数）", "1. line_no（昇順）"),
    group(3, "実績費用明細", "常時出力", "有（改ページ時に見出しを再出力）",
          "BT_ACTUAL_COSTの1レコード", "可変（申請の実績費用明細件数）", "1. line_no（昇順）"),
]


# ------------------------------------------------------------------
# 3.2 項目設計
# ------------------------------------------------------------------
SEP_START = 17             # 最初のグループ区切り行（D17:AY17 スタイル）
SEP_CLONE_SRC = 17
ITEM_CLONE_SRC = 18       # 明細（項目）行のスタイル複製元
ITEM_COL = {"D": "no", "E": "name", "J": "req", "K": "dtype", "M": "byte",
            "O": "halign", "Q": "valign", "S": "font", "U": "size",
            "W": "default", "Z": "edit", "AG": "srctbl", "AL": "srccol", "AP": "note"}


def it(no, name, dtype, byte, srctbl, srccol, req="○", halign="左",
       edit="-", default="-", note="-"):
    return {"no": no, "name": name, "req": req, "dtype": dtype, "byte": byte,
            "halign": halign, "valign": "中央", "font": "※", "size": 9.8,
            "default": default, "edit": edit, "srctbl": srctbl, "srccol": srccol,
            "note": note}


# 項目グループ1：申請・精算情報（固定欄。1申請=1レコードの単票項目）
GROUP1_ITEMS = [
    it(1, "帳票タイトル", "全角", 10, "固定値", "‐", req="-",
       halign="中央", edit="固定文字列「出張精算書」を出力", default='"出張精算書"'),
    it(2, "申請ID", "半角", 16, "BT_APPLICATION", "application_id",
       edit="BT＋YYYYMMDD＋連番6桁"),
    it(3, "申請者氏名", "全角", 100, "BT_EMPLOYEE", "employee_name",
       note="BT_APPLICATION.applicant_idに紐づく社員の氏名を取得する。"),
    it(4, "所属部門", "全角", 80, "BT_DEPARTMENT", "department_name",
       note="BT_APPLICATION.applicant_idに紐づく社員（BT_EMPLOYEE）のdepartment_codeをキーに、BT_DEPARTMENT.department_nameを取得する。"),
    it(5, "出張目的", "全角", 1000, "BT_APPLICATION", "purpose",
       edit="全文を折り返して出力する"),
    it(6, "出張開始日", "半角", 10, "BT_APPLICATION", "start_date",
       edit="yyyy/MM/dd"),
    it(7, "出張終了日", "半角", 10, "BT_APPLICATION", "end_date",
       edit="yyyy/MM/dd"),
    it(8, "費用負担区分", "全角", 8, "BT_APPLICATION", "cost_bearing",
       edit="コードC0020001（01:自社負担 / 02:先方負担）のコード値名称を出力"),
    it(9, "精算額", "半角", 11, "算出項目（CC0002 精算額計算）", "‐",
       halign="右", edit="\\9,999,999-",
       note=("cost_bearing='01'（自社負担）の場合はBT_ACTUAL_COST.actual_amountの合計を、"
             "cost_bearing='02'（先方負担）の場合は0を出力する。")),
    it(10, "最終承認者", "全角", 100, "BT_EMPLOYEE", "employee_name",
       note="BT_APPLICATION.approver_idに紐づく社員の氏名を取得する。"),
    it(11, "最終承認日", "半角", 16, "BT_APPLICATION", "finalized_at",
       edit="yyyy/MM/dd HH:mm"),
]

# 項目グループ2：予定費用明細（BT_PLANNED_COSTの明細一覧）
GROUP2_ITEMS = [
    it(1, "費目", "全角", 8, "BT_PLANNED_COST", "category",
       edit="コードC0010001（01:交通費 / 02:宿泊費 / 03:交際費）のコード値名称を出力"),
    it(2, "予定金額", "半角", 11, "BT_PLANNED_COST", "planned_amount",
       halign="右", edit="\\9,999,999-"),
]

# 項目グループ3：実績費用明細（BT_ACTUAL_COSTの明細一覧）
GROUP3_ITEMS = [
    it(1, "費目", "全角", 8, "BT_ACTUAL_COST", "category",
       edit="コードC0010001（01:交通費 / 02:宿泊費 / 03:交際費）のコード値名称を出力"),
    it(2, "実績金額", "半角", 11, "BT_ACTUAL_COST", "actual_amount",
       halign="右", edit="\\9,999,999-"),
]

# 区切り見出し文言と、配下の項目リスト
ITEM_SECTIONS = [
    ("項目グループ1：申請・精算情報", GROUP1_ITEMS),
    ("項目グループ2：予定費用明細", GROUP2_ITEMS),
    ("項目グループ3：実績費用明細", GROUP3_ITEMS),
]


# ------------------------------------------------------------------
# スタイル複製ヘルパ（doc_func_screen_bts01.py と同方針）
# ------------------------------------------------------------------
def clone_row_style(ws, src: int, dst: int, max_col: int = 55):
    """styled行 src の各セル書式・行高・単一行結合を dst 行へ複製する。"""
    if src == dst:
        return
    for col in range(1, max_col + 1):
        ws.cell(row=dst, column=col)._style = copy(ws.cell(row=src, column=col)._style)
    if src in ws.row_dimensions:
        ws.row_dimensions[dst].height = ws.row_dimensions[src].height
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row == dst and rng.max_row == dst:
            ws.unmerge_cells(str(rng))
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row == src and rng.max_row == src:
            ws.merge_cells(start_row=dst, start_column=rng.min_col,
                           end_row=dst, end_column=rng.max_col)


# ------------------------------------------------------------------
# 記入
# ------------------------------------------------------------------
def fill_overview(ws):
    for coord, value in OVERVIEW.items():
        put(ws, coord, value)


def fill_groups(ws):
    for i, g in enumerate(GROUPS):
        r = GROUP_START + i
        if r != GROUP_START:
            clone_row_style(ws, GROUP_CLONE_SRC, r)
        for col, key in GROUP_COL.items():
            put(ws, f"{col}{r}", g.get(key))


def fill_items(ws):
    r = SEP_START
    for sep_text, items in ITEM_SECTIONS:
        # グループ区切り行（D:AY 結合の見出し行）
        clone_row_style(ws, SEP_CLONE_SRC, r)
        put(ws, f"D{r}", sep_text)
        r += 1
        # 明細（項目）行
        for rec in items:
            clone_row_style(ws, ITEM_CLONE_SRC, r)
            for col, key in ITEM_COL.items():
                put(ws, f"{col}{r}", rec.get(key))
            r += 1


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)
    fill_overview(wb[OVERVIEW_SHEET])
    item_ws = wb[ITEM_SHEET]
    fill_groups(item_ws)
    fill_items(item_ws)
    # 2. レイアウト（帳票イメージ図）は図形保持不可のため触れない。
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
