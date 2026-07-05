"""共通コンポーネント設計書 — 出張申請サブシステムの共通コンポーネント4件。

1ブックに4シート（1コンポーネント=1シート）で次を設計する。

- CC0001 事前承認要否判定：予定費用合計・役職コード・費用負担区分から申請状態コードを返す。
  判定は処理定義にif羅列で記す。なぜ10万円か・なぜ役職なしか・なぜ先方負担かのWhyは書かない。
  同じ判定ロジックが画面機能設計書(BTS01)の登録イベント詳細にも重複して存在する（single
  source of truthが無い状態を、そのまま残す）。
- CC0002 精算額計算：自社負担なら実績費用合計、先方負担なら0円。afterのspec-modelでは
  「事前承認要件」や状態別の型・経理連携に吸収され概念ごと消える幻のコンポーネント。ここ(before)
  では独立コンポーネントとして設計する。
- CC0003 経理連携データ作成：BT_APPLICATION/BT_ACTUAL_COSTをREADし、外部I/F IBT01形式で出力。
- CC0004 申請ID採番：採番ユーティリティで BT＋YYYYMMDD＋連番6桁 を採番。

空テンプレは1コンポーネント分の書式しか持たない。入出力パラメータ表(3行)・CRUD一覧(2行)・
エラー情報(1行)は行数が固定なので、超過分は行を挿入して書式を複製する。openpyxlのinsert_rowsは
結合セルも行高も移動しないため、結合を退避・再設定する自作の行挿入で対応する。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, _anchor_coord, set_print_area

TEMPLATE = "共通コンポーネント設計書.xlsx"
OUTPUT = "共通コンポーネント設計書.xlsx"
PRODUCT = "共通コンポーネント設計書"

# 変更履歴・目次以外の唯一のコンテンツシート（複製元）。テンプレの実名は前後に空白を含む。
BASE_SHEET = "1.  コンポーネント名 "

# ---- 空テンプレのセル配置（記入見本ではなく本テンプレで確認した座標）----
# コンポーネント定義ヘッダ
ID_CELL = "F5"        # コンポーネントID（ラベルB5 / 値F5:H5）
NAME_CELL = "M5"      # コンポーネント名（ラベルI5 / 値M5:U5）
PROC_CELL = "Z5"      # 処理名（ラベルV5 / 値Z5:AH5）
SUMMARY_CELL = "B7"   # 処理説明（1.処理概要 / 2.注意事項）B7:AH12
CLASS_CELL = "F13"    # クラス名（ラベルB13 / 値F13:P13）
METHOD_CELL = "U13"   # メソッド名（ラベルQ13 / 値U13:AH13）

# 入出力パラメータ表（列: 項目名B:I / I/O J:K / 型 L:N / 必須 O:P / 項目説明 Q:AH）
PARAM_START, PARAM_SLOTS = 16, 3
PARAM_COL = {"B": "name", "J": "io", "L": "type", "O": "req", "Q": "desc"}
# CRUD一覧（列: テーブル名B:I / C J / R K / U L / D M / 備考 N:AH）
CRUD_START, CRUD_SLOTS = 21, 2
CRUD_COL = {"B": "table", "J": "c", "K": "r", "L": "u", "M": "d", "N": "note"}
# エラー情報（列: 番号B:C / 名D:J / 種別K:O / メッセージID P:R / 埋め込み S:W / 概要 X:AH）
ERR_START, ERR_SLOTS = 25, 1
ERR_COL = {"B": "no", "D": "name", "K": "kind", "P": "msgid", "S": "embed", "X": "overview"}
# 処理定義（自由記述領域。左B:Xに本文、右Y/AB/AGは共通ｺﾝﾎﾟｰﾈﾝﾄID/処理名/エラー番号）
DETAIL_START, DETAIL_SLOTS = 28, 14

# 各セクションの「次のラベル行」＝挿入位置（超過分をここに割り込ませる）
PARAM_INSERT_AT = 19   # CRUD一覧ラベルの直前
CRUD_INSERT_AT = 23    # エラー情報ラベルの直前
ERR_INSERT_AT = 26     # 処理定義ラベル(27)の直前の余白行


# ------------------------------------------------------------------
# 行挿入ヘルパ（結合セル・行高を維持したまま行を割り込ませる）
# ------------------------------------------------------------------
def insert_rows_keep_merges(ws, at: int, n: int, max_col: int = 35):
    """at 行の直前に n 行を挿入する。at 以降の値・書式・行高・結合セルを n 行分だけ下へ送る。

    openpyxl の ws.insert_rows は結合セルも行高も移動しないため、自前で退避・再設定する。
    挿入した空行 [at, at+n-1] は値も書式も持たない状態で返す（呼び元で clone_row_style する）。
    """
    if n <= 0:
        return
    maxr = ws.max_row
    # 1) at 以降で始まる結合セルを退避して解除
    shifted = []
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row >= at:
            shifted.append((rng.min_row, rng.min_col, rng.max_row, rng.max_col))
            ws.unmerge_cells(str(rng))
    # 2) 下から順に値・書式・行高を n 行下へコピー
    for r in range(maxr, at - 1, -1):
        for c in range(1, max_col + 1):
            src = ws.cell(row=r, column=c)
            dst = ws.cell(row=r + n, column=c)
            dst.value = src.value
            if src.has_style:
                dst._style = copy(src._style)
        if r in ws.row_dimensions:
            ws.row_dimensions[r + n].height = ws.row_dimensions[r].height
    # 3) 挿入した空行を掃除
    for r in range(at, at + n):
        for c in range(1, max_col + 1):
            cell = ws.cell(row=r, column=c)
            cell.value = None
    # 4) 退避した結合セルを n 行下に再設定
    for (r1, c1, r2, c2) in shifted:
        ws.merge_cells(start_row=r1 + n, start_column=c1, end_row=r2 + n, end_column=c2)


def clone_row_style(ws, src: int, dst: int, max_col: int = 35):
    """styled 行 src の各セル書式・行高・単一行結合を dst 行へ複製する。"""
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


def clear_cells(ws, row: int, cols):
    for col in cols:
        ws[_anchor_coord(ws, f"{col}{row}")] = None


def fill_table(ws, start: int, slots: int, colmap: dict, records: list, clone_src: int):
    """start 行から records を書き込む。slots を超えた行は clone_src の書式を複製済み前提で埋め、
    余ったスタイル付き行は掃除する。"""
    for i, rec in enumerate(records):
        r = start + i
        for col, key in colmap.items():
            put(ws, f"{col}{r}", rec.get(key))
    for r in range(start + len(records), start + slots):
        clear_cells(ws, r, colmap.keys())


# ------------------------------------------------------------------
# コンポーネント定義データ
# ------------------------------------------------------------------
def p(name, io, typ, req, desc):
    return {"name": name, "io": io, "type": typ, "req": req, "desc": desc}


def crud(table, c="-", r="-", u="-", d="-", note="-"):
    return {"table": table, "c": c, "r": r, "u": u, "d": d, "note": note}


NO_CRUD = [crud("-", note="DBアクセスなし")]
NO_ERROR = [{"no": "-", "name": "該当なし", "kind": "-", "msgid": "-", "embed": "-", "overview": "-"}]


COMPONENTS = [
    {
        "sheet": "1. 事前承認要否判定",
        "id": "CC0001",
        "name": "事前承認要否判定",
        "proc": "事前承認要否判定",
        "class": "PreApprovalDecision",
        "method": "needsPreApproval",
        "summary": (
            "1.処理概要\n"
            "　出張申請の予定費用合計、申請者の役職コード、費用負担区分を入力として、上長の事前承認が"
            "必要か否かを判定し、申請状態コードを返却する。\n\n"
            "2.注意事項\n"
            "　本コンポーネントは出張申請登録（BTS01）から呼び出す。予定費用合計は呼び元で予定費用明細"
            "（BT_PLANNED_COST.planned_amount）を集計した値を渡すこと。"
        ),
        "params": [
            p("予定費用合計", "I", "Integer", "○", "出張予定費用明細のplanned_amountの合計（円）"),
            p("役職コード", "I", "String", "○", "申請者の役職コード（コードC0040001）"),
            p("費用負担区分", "I", "String", "○", "費用負担区分（コードC0020001）"),
            p("申請状態コード", "O", "String", "-",
              "事前承認要否の判定結果。'20'：事前承認待ち／'21'：事前承認不要"),
        ],
        "cruds": NO_CRUD,
        "errors": [
            {"no": 1, "name": "パラメータエラー", "kind": "IllegalArgumentException",
             "msgid": "-", "embed": "-",
             "overview": "予定費用合計・役職コード・費用負担区分のいずれかがnullの場合。"},
        ],
        "detail": [
            {"B": "1. 判定処理"},
            {"C": "　（1） 予定費用合計が 100000 以上の場合、申請状態コードに '20' を設定する。"},
            {"C": "　（2） 役職コードが '99' の場合、申請状態コードに '20' を設定する。"},
            {"C": "　（3） 費用負担区分が '02' の場合、申請状態コードに '20' を設定する。"},
            {"C": "　（4） 上記（1）〜（3）のいずれにも該当しない場合、申請状態コードに '21' を設定する。"},
            {"B": "2. 戻り値返却"},
            {"C": "　設定した申請状態コードを呼び元へ返却する。"},
        ],
    },
    {
        "sheet": "2. 精算額計算",
        "id": "CC0002",
        "name": "精算額計算",
        "proc": "精算額計算",
        "class": "SettlementCalculator",
        "method": "calculateSettlementAmount",
        "summary": (
            "1.処理概要\n"
            "　費用負担区分と実績費用合計を入力として、会社が立て替える精算額を計算して返却する。\n\n"
            "2.注意事項\n"
            "　本コンポーネントは出張申請最終承認（BTS04）および経理連携ファイル作成（BTB01）から呼び出す。"
            "実績費用合計は呼び元で実績費用明細（BT_ACTUAL_COST.actual_amount）を集計した値を渡すこと。"
        ),
        "params": [
            p("費用負担区分", "I", "String", "○", "費用負担区分（コードC0020001）"),
            p("実績費用合計", "I", "Integer", "○", "出張実績費用明細のactual_amountの合計（円）"),
            p("精算額", "O", "Integer", "-", "会社が立て替える精算額（円）"),
        ],
        "cruds": NO_CRUD,
        "errors": NO_ERROR,
        "detail": [
            {"B": "1. 精算額計算処理"},
            {"C": "　（1） 費用負担区分が '01'（自社負担）の場合、実績費用合計をそのまま精算額とする。"},
            {"C": "　（2） 費用負担区分が '02'（先方負担）の場合、精算額を 0 円とする。"},
            {"B": "2. 戻り値返却"},
            {"C": "　算出した精算額を呼び元へ返却する。"},
        ],
    },
    {
        "sheet": "3. 経理連携データ作成",
        "id": "CC0003",
        "name": "経理連携データ作成",
        "proc": "経理連携データ作成",
        "class": "AccountingLinkFileCreator",
        "method": "createAccountingData",
        "summary": (
            "1.処理概要\n"
            "　申請IDと精算額を入力として、経理システム連携用の外部インタフェースレコード（IBT01形式）を"
            "作成して返却する。\n\n"
            "2.注意事項\n"
            "　本コンポーネントはバッチ取引 BTB01（経理連携ファイル作成）から、最終承認済（appl_status='50'）"
            "の申請1件ごとに呼び出す。"
        ),
        "params": [
            p("申請ID", "I", "String", "○", "対象の出張申請の申請ID（BT_APPLICATION.application_id）"),
            p("精算額", "I", "Integer", "○", "【CC0002：精算額計算】で算出した精算額（円）"),
            p("経理I/Fレコード", "O", "String", "-", "経理システム連携ファイル（IBT01）の1レコード"),
        ],
        "cruds": [
            crud("BT_APPLICATION", r="○", note="申請者・出張目的・出張期間・最終承認日時を取得する"),
            crud("BT_ACTUAL_COST", r="○", note="出張実績費用明細を取得する"),
        ],
        "errors": [
            {"no": 1, "name": "対象データ不存在", "kind": "ApplicationException",
             "msgid": "MSGE0003", "embed": "{0}：申請ID",
             "overview": "指定した申請IDのBT_APPLICATIONが存在しない場合。"},
        ],
        "detail": [
            {"B": "1. データ取得処理"},
            {"C": "　申請IDをキーに BT_APPLICATION を検索し、申請者・出張目的・出張期間・最終承認日時を取得する。"},
            {"C": "　申請IDをキーに BT_ACTUAL_COST を検索し、出張実績費用明細を取得する。"},
            {"B": "2. レコード編集処理"},
            {"C": "　取得した項目と精算額を、外部インタフェース IBT01（経理システム連携ファイル）のレコード形式に編集する。"},
            {"D": "レコード形式：申請ID ＋ 社員番号 ＋ 精算額 ＋ 最終承認日時（固定長）"},
            {"B": "3. 戻り値返却"},
            {"C": "　編集した経理I/Fレコードを呼び元へ返却する。"},
        ],
    },
    {
        "sheet": "4. 申請ID採番",
        "id": "CC0004",
        "name": "申請ID採番",
        "proc": "申請ID採番",
        "class": "ApplicationIdGenerator",
        "method": "generateApplicationId",
        "summary": (
            "1.処理概要\n"
            "　採番ユーティリティを利用して、出張申請の申請IDを採番して返却する。採番フォーマットは"
            " BT ＋ YYYYMMDD ＋ 連番6桁（計16桁）。\n\n"
            "2.注意事項\n"
            "　連番はシーケンスを利用し、抜け番を許容する。本コンポーネントは出張申請登録（BTS01）の"
            "登録イベントから呼び出す。"
        ),
        "params": [
            p("申請ID", "O", "String", "-", "採番した申請ID（16桁：BT＋YYYYMMDD＋連番6桁）"),
        ],
        "cruds": [
            crud("BT_APPLICATION_SEQ（シーケンス）", r="○",
                 note="申請ID採番用シーケンスから連番を取得する"),
        ],
        "errors": NO_ERROR,
        "detail": [
            {"B": "1. 採番処理"},
            {"C": "　採番ユーティリティを呼び出し、申請ID採番用シーケンスから連番（6桁）を取得する。"},
            {"C": "　⇒使用ユーティリティ：【nablarch.common.idgenerator.SequenceIdGenerator】"},
            {"B": "2. 編集処理"},
            {"C": "　'BT' ＋ システム日付（YYYYMMDD） ＋ 連番（6桁ゼロ埋め）を連結し、16桁の申請IDを編集する。"},
            {"B": "3. 戻り値返却"},
            {"C": "　編集した申請IDを呼び元へ返却する。"},
        ],
    },
]


# ------------------------------------------------------------------
# 記入
# ------------------------------------------------------------------
def fill_sheet(ws, cc: dict):
    # 超過行数を算出（下のセクションから挿入して上のアンカーを保つ）
    pe = max(0, len(cc["params"]) - PARAM_SLOTS)
    ce = max(0, len(cc["cruds"]) - CRUD_SLOTS)
    ee = max(0, len(cc["errors"]) - ERR_SLOTS)
    if ee:
        insert_rows_keep_merges(ws, ERR_INSERT_AT, ee)
        for i in range(ee):
            clone_row_style(ws, ERR_START, ERR_INSERT_AT + i)
    if ce:
        insert_rows_keep_merges(ws, CRUD_INSERT_AT, ce)
        for i in range(ce):
            clone_row_style(ws, CRUD_START, CRUD_INSERT_AT + i)
    if pe:
        insert_rows_keep_merges(ws, PARAM_INSERT_AT, pe)
        for i in range(pe):
            clone_row_style(ws, PARAM_START + PARAM_SLOTS - 1, PARAM_INSERT_AT + i)

    # 挿入後の最終アンカー
    param_start = PARAM_START
    crud_start = CRUD_START + pe
    err_start = ERR_START + pe + ce
    detail_start = DETAIL_START + pe + ce + ee

    # コンポーネント定義ヘッダ
    put(ws, ID_CELL, cc["id"])
    put(ws, NAME_CELL, cc["name"])
    put(ws, PROC_CELL, cc["proc"])
    put(ws, SUMMARY_CELL, cc["summary"])
    put(ws, CLASS_CELL, cc["class"])
    put(ws, METHOD_CELL, cc["method"])

    # 各表
    fill_table(ws, param_start, PARAM_SLOTS + pe, PARAM_COL, cc["params"], PARAM_START)
    fill_table(ws, crud_start, CRUD_SLOTS + ce, CRUD_COL, cc["cruds"], CRUD_START)
    fill_table(ws, err_start, ERR_SLOTS + ee, ERR_COL, cc["errors"], ERR_START)

    # 処理定義（自由記述）
    for i, rowdict in enumerate(cc["detail"]):
        r = detail_start + i
        assert r < detail_start + DETAIL_SLOTS, f"{cc['id']}: 処理定義が記述領域を超過"
        for col, val in rowdict.items():
            put(ws, f"{col}{r}", val)


def fill_toc(wb):
    toc = wb["目次"]
    for i, cc in enumerate(COMPONENTS):
        put(toc, f"B{7 + i}", cc["sheet"])


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    base = wb[BASE_SHEET]
    sheets = [base]
    for _ in range(len(COMPONENTS) - 1):
        sheets.append(wb.copy_worksheet(base))
    for ws, cc in zip(sheets, COMPONENTS):
        ws.title = cc["sheet"]
        fill_sheet(ws, cc)

    order = ["表紙", "変更履歴", "目次"] + [cc["sheet"] for cc in COMPONENTS]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    # 複製で print_area が消えたコンポーネントシートを内容全体に張り直す。印刷右端は AI(35)。
    for ws in sheets:
        set_print_area(ws, right_col=35)

    fill_toc(wb)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
