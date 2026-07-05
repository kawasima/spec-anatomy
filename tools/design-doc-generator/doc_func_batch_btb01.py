"""システム機能設計書(バッチ) — BTB01 経理連携ファイル作成。

最終承認済（appl_status='50'）の出張申請を抽出し、申請者が立て替えた精算額を
経理システム連携ファイル（IBT01）へ出力する日次バッチ取引。従来SIの設計をそのまま写す。
特に次の点は「直す」対象ではなく「そのまま書く」対象:

- 抽出条件を appl_status のコード値直書き（'50'）で表す。なぜ最終承認済のみが対象なのか
  （Why）は書かない。連携済の管理も専用カラムを持たず、appl_status を '60'(経理連携済) に
  更新することで表現する（状態をコード値の直書きで持ち回る）。
- 精算額の算出条件（自社負担なら実費、先方負担なら0円）を、共通コンポーネント CC0002 と
  重複して 2.6. 処理詳細 にも自然言語で書き下す。なぜ先方負担が0円なのか（Why）は書かない。

空テンプレート（Nablarch開発標準）のヘッダは INDIRECT 参照ではなく各シート直書きなので、
変更履歴だけでなくコンテンツシートにもヘッダ値を個別に書き込む点に注意。
"""
from __future__ import annotations

from copy import copy

from common import PROJECT, open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(バッチ)_BTB01_経理連携ファイル作成.xlsx"
OUTPUT = "システム機能設計書(バッチ)_BTB01_経理連携ファイル作成.xlsx"
PRODUCT = "システム機能設計書(バッチ)\n\nBTB01/経理連携ファイル作成"

OVERVIEW_SHEET = "1.1. バッチ取引概要"
FLOW_SHEET = "1.3. バッチ処理フロー"
PROC_SHEET = "2. バッチ処理ID(バッチ処理名)"
PROC_TITLE = "2. BTB0101(経理連携ファイル作成)"

PROCESS_ID = "BTB0101"
PROCESS_NAME = "経理連携ファイル作成"


# ------------------------------------------------------------------
# 汎用ヘルパ
# ------------------------------------------------------------------
def _anchor(ws, coord):
    from common import _anchor_coord
    return _anchor_coord(ws, coord)


def put_none(ws, coord):
    ws[_anchor(ws, coord)] = None


def clear_cells(ws, row, cols):
    for col in cols:
        put_none(ws, f"{col}{row}")


def clone_row_style(ws, src: int, dst: int, max_col: int = 44):
    """styled行 src の各セル書式・行高・単一行結合を dst 行へ複製する。"""
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


def write_rows(ws, start, step, colmap, records, styled_end=None, clone_src=None):
    """表に行を流し込む。styled_end を超えた行は clone_src の書式を複製する。"""
    for i, rec in enumerate(records):
        r = start + i * step
        if styled_end is not None and clone_src is not None and r > styled_end:
            clone_row_style(ws, clone_src, r)
        for col, key in colmap.items():
            if key in rec and rec[key] is not None:
                put(ws, f"{col}{r}", rec[key])


def write_detail(ws, start, rows):
    """処理詳細（自由記述領域）に (col->val の dict) を上から書く。

    各セルを次のキー列（無ければ内容右端 AH=34）まで横結合し、wrap_text と行高を設定する
    common.write_detail_region に委譲する（狭い1セルでの日本語の縦折り返しを防ぐ）。
    2.7.1.（行90）に達しないよう limit=89 を渡す。"""
    write_detail_region(ws, rows, start, limit=89, right_col=34)


# ------------------------------------------------------------------
# ヘッダ（各シート直書き）
# ------------------------------------------------------------------
def fill_sheet_header(ws):
    put(ws, "E1", PROJECT["pj"])
    put(ws, "E2", PROJECT["system"])
    put(ws, "E3", PROJECT["subsystem"])
    put(ws, "S1", PRODUCT)
    put(ws, "AC1", PROJECT["author"])
    put(ws, "AG1", PROJECT["created"])
    put(ws, "AC2", PROJECT["author"])
    put(ws, "AG2", PROJECT["changed"])


# ------------------------------------------------------------------
# 定義データ
# ------------------------------------------------------------------
TRANSACTION = {
    "id": "BTB01",
    "name": "経理連携ファイル作成",
    "overview": (
        "最終承認済の出張申請を対象に、申請者が立て替えた精算額を経理システム連携ファイル"
        "（IBT01）へ出力する日次バッチ取引。毎営業日夜間にジョブスケジューラより起動し、"
        "申請状態が最終承認済の出張申請を抽出して連携ファイルを作成する。"
    ),
    "trigger": (
        "日次（毎営業日夜間）。ジョブスケジューラより起動する。"
        "前提となる最終承認処理（BTS04）が当日分まで完了していること。"
    ),
    "premise": (
        "経理システム連携ファイルの出力先ディレクトリが利用可能であること。"
        "抽出対象は申請状態（appl_status）が'50'（最終承認済）の出張申請とする。"
    ),
}

PROC_LIST = [
    {"no": 1, "id": PROCESS_ID, "name": PROCESS_NAME, "resident": "-",
     "process": "-", "thread": "-",
     "overview": "申請状態が'50'(最終承認済)の出張申請を抽出し、立替精算額を集計して"
                 "経理システム連携ファイルを出力する。"},
]

PROC_OVERVIEW = {
    "unit": "抽出した出張申請1件。",
    "order": "BT_APPLICATION.application_idの昇順。",
    "recovery": "先頭から再実行する。連携済(appl_status='60')の申請は再抽出されないため、"
                "二重連携は発生しない。",
}

PARAMS = [
    {"no": 1, "name": "業務日付", "req": "-", "value": "業務日付(yyyymmdd)",
     "desc": "経理連携対象を抽出する基準となる業務日付。省略時はシステム日付を使用する。",
     "phys": "businessDate"},
]

RESULTS = [
    {"no": 1, "code": 0, "fault": "-", "result": "正常に処理が終了した場合。"},
    {"no": 2, "code": 198, "fault": "-",
     "result": "警告終了：連携対象の出張申請が0件の場合。連携ファイルは出力しない。"},
    {"no": 3, "code": 1, "fault": "-",
     "result": "異常終了：処理中にシステムエラーが発生した場合。"},
]

IO = [
    {"no": 1, "name": "BT_APPLICATION", "kind": "テーブル", "io": "I",
     "c": "-", "r": "○", "u": "-", "d": "-", "lock": "-",
     "note": "抽出対象の出張申請を取得する。"},
    {"no": 2, "name": "BT_ACTUAL_COST", "kind": "テーブル", "io": "I",
     "c": "-", "r": "○", "u": "-", "d": "-", "lock": "-",
     "note": "精算額の集計元となる出張実績費用を取得する。"},
    {"no": 3, "name": "経理システム連携ファイル", "kind": "I/Fファイル", "io": "O",
     "c": "-", "r": "-", "u": "-", "d": "-", "lock": "-",
     "note": "立替精算額を経理システムへ連携する。"},
    {"no": 4, "name": "BT_APPLICATION", "kind": "テーブル", "io": "O",
     "c": "-", "r": "-", "u": "○", "d": "-", "lock": "-",
     "note": "連携済の申請の申請状態を更新する。"},
]

INPUT_ITEMS = [
    {"no": 1, "src": "BT_APPLICATION", "item": "application_id", "req": "○",
     "domain": "申請ID", "note": "-"},
    {"no": 2, "src": "BT_APPLICATION", "item": "applicant_id", "req": "○",
     "domain": "社員番号", "note": "-"},
    {"no": 3, "src": "BT_APPLICATION", "item": "cost_bearing", "req": "○",
     "domain": "費用負担区分", "note": "-"},
]

DETAIL = [
    {"D": "(1) 経理連携対象の抽出"},
    {"E": "「2.5.1. BT_APPLICATION」に基づき、申請状態(appl_status)が'50'(最終承認済)の"
          "出張申請を抽出する。"},
    {"E": "抽出結果が0件の場合、警告終了する。"},
    {"E": "終了コード", "H": "障害コード", "K": "メッセージID", "O": "埋め込み文字列"},
    {"E": 198, "H": "-", "K": "-", "O": "-"},
    {},
    {"D": "(2) 精算額の集計・算出"},
    {"E": "抽出した出張申請ごとに、出張実績費用(BT_ACTUAL_COST)の実費(actual_amount)を"
          "申請単位で集計する。"},
    {"E": "集計した実費をもとに、費用負担区分(cost_bearing)に応じて精算額を算出する。"},
    {"F": "・費用負担区分が'01'(自社負担)の場合、集計した実費の合計額を精算額とする。"},
    {"F": "・費用負担区分が'02'(先方負担)の場合、精算額は0円とする。"},
    {},
    {"D": "(3) 連携レコードの生成"},
    {"E": "出張申請ごとに、経理システム連携ファイルのレコードを生成する。"},
    {"E": "レコードは固定長形式とし、運用に応じてCSV形式でも出力可能とする。"},
    {"E": "レコードの編集仕様は「2.7.3. 経理連携ファイル出力：経理システム連携ファイル」を参照。"},
    {},
    {"D": "(4) 連携ファイルの出力"},
    {"E": "生成した全レコードを経理システム連携ファイル(IBT01)に出力する。"},
    {},
    {"D": "(5) 連携済の管理"},
    {"E": "出力が完了した出張申請について、申請状態(appl_status)を'60'(経理連携済)に更新する。"},
    {"E": "更新仕様は「2.7.2. 連携済更新：BT_APPLICATION」を参照。"},
]

UPDATE_ITEMS = [
    {"no": 1, "item": "appl_status", "srctbl": "-", "srcitem": "-",
     "edit": "'60'(経理連携済)", "note": "-"},
]

FILE_ITEMS = [
    {"no": 1, "id": "applicationId", "name": "申請ID", "src": "BT_APPLICATION",
     "srcitem": "application_id", "edit": "-", "note": "-"},
    {"no": 2, "id": "employeeCode", "name": "社員番号", "src": "BT_APPLICATION",
     "srcitem": "applicant_id", "edit": "-", "note": "-"},
    {"no": 3, "id": "costBearingType", "name": "費用負担区分", "src": "BT_APPLICATION",
     "srcitem": "cost_bearing", "edit": "-", "note": "-"},
    {"no": 4, "id": "settlementAmount", "name": "精算額", "src": "-", "srcitem": "-",
     "edit": "「2.6. 処理詳細 (2)」で算出した精算額を設定する。", "note": "-"},
    {"no": 5, "id": "linkageDate", "name": "連携日付", "src": "-", "srcitem": "-",
     "edit": "システム日付(yyyymmdd)を設定する。", "note": "-"},
]


# ------------------------------------------------------------------
# 記入
# ------------------------------------------------------------------
def fill_overview(ws):
    put(ws, "H8", TRANSACTION["id"])
    put(ws, "H9", TRANSACTION["name"])
    put(ws, "H10", TRANSACTION["overview"])
    put(ws, "H30", TRANSACTION["trigger"])
    put(ws, "H34", TRANSACTION["premise"])
    # 1.2. バッチ処理一覧（データ行: 48, 51, 54, 57）
    write_rows(ws, 48, 3,
               {"D": "no", "E": "id", "I": "name", "Q": "resident",
                "S": "process", "U": "thread", "W": "overview"},
               PROC_LIST)
    for r in (51, 54, 57):  # テンプレの No.2〜4 プレースホルダを消す
        put_none(ws, f"D{r}")


def fill_process(ws):
    ws.title = PROC_TITLE
    put(ws, "B5", PROC_TITLE)

    # 2.1. 処理概要
    put(ws, "I8", PROC_OVERVIEW["unit"])
    put(ws, "I9", PROC_OVERVIEW["order"])
    put(ws, "I10", PROC_OVERVIEW["recovery"])

    # 2.2. 起動パラメータ（データ行16、17・18を掃除）
    write_rows(ws, 16, 1,
               {"D": "no", "E": "name", "K": "req", "L": "value",
                "Q": "desc", "AK": "phys"},
               PARAMS)
    for r in (17, 18):
        put_none(ws, f"D{r}")

    # 2.3. 処理結果一覧（データ行24,25,26）
    write_rows(ws, 24, 1,
               {"D": "no", "E": "code", "H": "fault", "K": "result"},
               RESULTS)

    # 2.4. 入出力一覧（データ行33,34,35。4件目は35から複製）
    write_rows(ws, 33, 1,
               {"D": "no", "E": "name", "K": "kind", "O": "io",
                "P": "c", "Q": "r", "R": "u", "S": "d", "T": "lock", "V": "note"},
               IO, styled_end=35, clone_src=35)

    # 2.5.1. BT_APPLICATION（取得項目 44,45,46）
    put(ws, "D39", "2.5.1. BT_APPLICATION")
    write_rows(ws, 44, 1,
               {"E": "no", "F": "src", "L": "item", "Q": "req",
                "R": "domain", "W": "note"},
               INPUT_ITEMS)
    # 取得条件（appl_status のコード値直書き）
    put(ws, "F49", "申請状態(appl_status)")
    put(ws, "K49", "=")
    put(ws, "L49", "'50'(最終承認済)")
    # 2.5.2. 入力ファイルなし
    put(ws, "D51", "2.5.2. 該当なし（入力ファイル・電文・メールなし）")
    put(ws, "E53", "該当なし。")
    put_none(ws, "E56")
    put_none(ws, "M56")

    # 2.6. 処理詳細（自由記述、行60から）
    write_detail(ws, 60, DETAIL)

    # 2.7.1. 登録なし
    put(ws, "D90", "2.7.1. 該当なし（テーブルへの新規登録なし）")
    for coord in ("E92", "F92", "K92", "V92", "AD92", "K93", "Q93",
                  "E94", "E95", "E96"):
        put_none(ws, coord)
    put(ws, "E94", "本バッチではテーブルへの新規登録は行わない。")

    # 2.7.2. 連携済更新：BT_APPLICATION
    put(ws, "D99", "2.7.2. 連携済更新：BT_APPLICATION")
    put(ws, "K101",
        "application_id ＝「2.6. 処理詳細 (1)」で抽出した出張申請の application_id")
    write_rows(ws, 104, 1,
               {"E": "no", "F": "item", "K": "srctbl", "Q": "srcitem",
                "V": "edit", "AD": "note"},
               UPDATE_ITEMS)
    for r in (105, 106):
        put_none(ws, f"E{r}")

    # 2.7.3. 経理連携ファイル出力：経理システム連携ファイル
    put(ws, "D109", "2.7.3. 経理連携ファイル出力：経理システム連携ファイル")
    put(ws, "F113", "【外部インタフェース設計書_経理システム連携ファイル】を参照。")
    put(ws, "I115", "IBT01")
    put(ws, "Q115", "経理システム連携ファイル")
    write_rows(ws, 122, 1,
               {"F": "no", "G": "id", "K": "name", "O": "src",
                "T": "srcitem", "X": "edit", "AE": "note"},
               FILE_ITEMS, styled_end=124, clone_src=124)


def fill_toc(wb):
    toc = wb["目次"]
    put(toc, "B12", f"2. {PROCESS_ID}({PROCESS_NAME})")


def fill_cover(wb):
    cover = wb["表紙"]
    put(cover, "J32", PROJECT["author"])
    put(cover, "J34", "システム開発部")


def build() -> str:
    wb = open_template(TEMPLATE)

    # 変更履歴（明細行・PJ識別）
    fill_history(wb, product_name=PRODUCT)

    # 各シートのヘッダは INDIRECT 参照でなく直書きなので個別に埋める
    for name in wb.sheetnames:
        if name in ("表紙", "データ"):
            continue
        fill_sheet_header(wb[name])

    fill_cover(wb)
    fill_overview(wb[OVERVIEW_SHEET])
    fill_process(wb[PROC_SHEET])
    fill_toc(wb)

    # 印刷範囲を内容全体に張り直す。バッチ機能設計書の印刷右端は AI(35)。
    # 処理フローシートはテンプレ時点で print_area が空なのでここで補う。
    for name in (OVERVIEW_SHEET, FLOW_SHEET, PROC_TITLE):
        set_print_area(wb[name], right_col=35)

    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
