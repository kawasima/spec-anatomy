"""システム機能設計書(画面) — BTS03 出張実績登録（3画面取引）。

出張実績登録は「入力(WBT0301)→確認(WBT0302)→完了(WBT0303)」の3画面で構成する取引。
出張申請登録(BTS01)と同じ3画面構成をとる。従来SIの設計をそのまま写す。特に次の点は
「直す」対象ではなく「そのまま書く」対象:

- 画面項目定義はテーブル駆動。情報取得元に「テーブル.カラム」を書き、内部設計情報の
  画面項目名(物理)にDBの物理カラム名（BT_ACTUAL_COST.actual_amount 等）をそのまま書く。
  業務概念の派生元は現れない。
- 登録可否の事前条件判定を、確認画面の登録イベント処理詳細に自然言語の手続きとして
  埋没させる。appl_statusが'30'（事前承認済）または'21'（事前承認不要）以外ならエラー、
  という判定だけを書き、なぜ'30'/'21'のみ登録可能なのか(Why)は書かない。状態遷移は
  申請状態コード(APPL_STATUS)の数値（'30'/'21' → '40'）で表す。
- 登録処理で BT_ACTUAL_COST へ実績明細をINSERTし、appl_status を'40'に更新、
  version_no を加算する手続きを処理詳細に書く。
- 画面引継ぎ項目で入力→確認→完了へ出張実績の項目一式をまるごと引き継ぐ(スタンプ結合的)。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(画面)_BTS03_出張実績登録.xlsx"
OUTPUT = "システム機能設計書(画面)_BTS03_出張実績登録.xlsx"
PRODUCT = "システム機能設計書（画面）\n\nBTS03/出張実績登録"

OVERVIEW_SHEET = "1.1. 取引概要"   # テンプレの取引概要シート（複製元ではない）
BASE_SCREEN = "2. 画面ID(画面名)"  # 複製元の画面シート

# 取引概要
TRANSACTION = {
    "id": "BTS03",
    "name": "出張実績登録",
    "overview": (
        "一般社員が出張の実施後、実際に発生した費用（実績費用明細）を入力し、"
        "出張実績を登録する場合に本業務取引を使用する。"
        "参照領域に対象の出張申請（申請ID・出張目的・出張期間・費用負担区分・予定費用合計・"
        "事前承認状態）を表示し、実績費用明細を入力する。"
        "本取引は出張実績登録画面（入力）→出張実績登録確認画面（確認）→出張実績登録完了画面（完了）の"
        "3画面で構成する。登録時に対象申請の状態（APPL_STATUS）を確認し、実績登録済に更新する。"
    ),
    "user": "一般社員",
}

# ---- 列マップ（空テンプレの列位置に合わせる。記入見本とは列がずれるので注意）----
ITEM_COL = {"E": "no", "F": "name", "J": "kind", "N": "src",
            "V": "edit", "AA": "init", "AD": "req", "AE": "domain", "AL": "phys"}
IO_COL = {"D": "no", "E": "name", "K": "kind", "O": "io",
          "P": "c", "Q": "r", "R": "u", "S": "d", "T": "lock", "V": "note"}
EVT_COL = {"D": "no", "E": "name", "K": "timing", "R": "summary", "Z": "dest", "AE": "comm"}
LIST_COL = {"D": "no", "E": "name", "N": "paging", "Q": "sort", "V": "note"}
HAND_COL = {"C": "no", "D": "name", "L": "store", "P": "value", "U": "desc", "AB": "note"}

# 各セクションの開始行 / スタイル付き最終行 / スタイル複製元行
LIST_ROWS = (46, 47, 46)        # 2.2 一覧表示
ITEM_ROWS = (56, 65, 56)        # 2.3 画面項目定義
IO_ROWS = (75, 77, 75)          # 2.4 入出力一覧
EVT_ROWS = (83, 85, 83)         # 2.5 画面イベント一覧
AREA_CELL = "E55"               # 2.3 の領域名ラベル
DETAIL_START = 89               # 2.6 画面イベント詳細（自由記述領域）
DETAIL_LIMIT = 125              # ここから先は画面引継ぎ項目
HAND_EVENT_CELL = "B127"        # 引継ぎ項目のイベント見出し
HAND_GROUP_CELL = "C131"
HAND_PREFIX_CELL = "L131"
HAND_ROWS = (132, 132, 132)     # 引継ぎ明細（styled_endは132、以降はcloneで増やす）
HAND_CLEAR_TO = 134             # テンプレ既存明細行の掃除対象


# ------------------------------------------------------------------
# 汎用ヘルパ
# ------------------------------------------------------------------
def clone_row_style(ws, src: int, dst: int, max_col: int = 54):
    """styled行 src の各セル書式・行高・単一行結合を dst 行へ複製する。"""
    for col in range(1, max_col + 1):
        ws.cell(row=dst, column=col)._style = copy(ws.cell(row=src, column=col)._style)
    if src in ws.row_dimensions:
        ws.row_dimensions[dst].height = ws.row_dimensions[src].height
    # dst 行に残る単一行結合を解除してから src の結合を写す
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row == dst and rng.max_row == dst:
            ws.unmerge_cells(str(rng))
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row == src and rng.max_row == src:
            ws.merge_cells(start_row=dst, start_column=rng.min_col,
                           end_row=dst, end_column=rng.max_col)


def clear_cells(ws, row: int, cols):
    for col in cols:
        put_none(ws, f"{col}{row}")


def put_none(ws, coord: str):
    from common import _anchor_coord
    ws[_anchor_coord(ws, coord)] = None


def write_table(ws, rows_def, colmap, records):
    """スタイル付き行に表を流し込む。records が styled 行数を超えたら書式を複製する。
    余ったスタイル付き行はテンプレの No. 等を消す。"""
    start, styled_end, clone_src = rows_def
    for i, rec in enumerate(records):
        r = start + i
        if r > styled_end:
            clone_row_style(ws, clone_src, r)
        for col, key in colmap.items():
            put(ws, f"{col}{r}", rec.get(key))
    for r in range(start + len(records), styled_end + 1):
        clear_cells(ws, r, colmap.keys())


def write_detail(ws, rows):
    """2.6 画面イベント詳細（自由記述領域）に (rowdict) を上から書く。

    各セルを次のキー列（無ければ印刷右端 AI=35）まで横結合し、wrap_text と行高を設定する
    common.write_detail_region に委譲する（狭い1セルでの日本語の縦折り返しを防ぐ）。"""
    write_detail_region(ws, rows, DETAIL_START, limit=DETAIL_LIMIT, right_col=35)


# ------------------------------------------------------------------
# 画面定義データ
# ------------------------------------------------------------------
def item(no, name, kind, src, edit="-", init="-", req="○", domain="-", phys="-"):
    return {"no": no, "name": name, "kind": kind, "src": src, "edit": edit,
            "init": init, "req": req, "domain": domain, "phys": phys}


# --- WBT0301 出張実績登録画面（入力）---
# 参照領域（申請済み・事前承認済／不要の出張申請を参照専用で表示）+ 実績費用明細領域
WBT0301_ITEMS = [
    item(1, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="対象の出張申請の申請IDを表示（読み取り専用）", req="-",
         domain="申請ID", phys="application_id"),
    item(2, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="読み取り専用", req="-", domain="出張目的", phys="purpose"),
    item(3, "出張期間", "label", "BT_APPLICATION.start_date / BT_APPLICATION.end_date",
         edit="YYYYMMDD 〜 YYYYMMDD 形式で表示（読み取り専用）", req="-",
         domain="日付", phys="start_date / end_date"),
    item(4, "費用負担区分", "label", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001のコード値名称を表示（読み取り専用）", req="-",
         domain="費用負担区分", phys="cost_bearing"),
    item(5, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="予定費用明細のplanned_amountを合計して #,##0 円で表示", req="-",
         domain="金額", phys="-"),
    item(6, "事前承認状態", "label", "BT_APPLICATION.appl_status",
         edit="コードC0030001のコード値名称を表示（'30':事前承認済 / '21':事前承認不要）", req="-",
         domain="申請状態", phys="appl_status"),
    item(7, "実績日付", "text", "BT_ACTUAL_COST.expense_date",
         edit="YYYYMMDD形式。出張期間内のみ選択可。カレンダーピッカー。実績費用明細の行項目",
         domain="日付", phys="expense_date"),
    item(8, "費目", "select(pulldown)", "BT_ACTUAL_COST.category",
         edit="コードC0010001（01:交通費 / 02:宿泊費 / 03:交際費）。明細の行項目",
         init="交通費（01）", domain="費目", phys="category"),
    item(9, "実績金額", "text", "BT_ACTUAL_COST.actual_amount",
         edit="整数9桁・0以上。#,##0 円で表示。明細の行項目",
         domain="金額", phys="actual_amount"),
    item(10, "実績費用合計", "label", "BT_ACTUAL_COST.actual_amount（合計）",
         edit="実績費用明細のactual_amountを合計して #,##0 円で表示", init="0", req="-",
         domain="金額", phys="-"),
]

# --- WBT0302 出張実績登録確認画面（確認）---
WBT0302_ITEMS = [
    item(1, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="読み取り専用", req="-", domain="申請ID", phys="application_id"),
    item(2, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="読み取り専用", req="-", domain="出張目的", phys="purpose"),
    item(3, "出張期間", "label", "BT_APPLICATION.start_date / BT_APPLICATION.end_date",
         edit="YYYYMMDD 〜 YYYYMMDD 形式で表示", req="-",
         domain="日付", phys="start_date / end_date"),
    item(4, "費用負担区分", "label", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001のコード値名称を表示", req="-",
         domain="費用負担区分", phys="cost_bearing"),
    item(5, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="予定費用明細のplanned_amountの合計を #,##0 円で表示", req="-",
         domain="金額", phys="-"),
    item(6, "事前承認状態", "label", "BT_APPLICATION.appl_status",
         edit="コードC0030001のコード値名称を表示", req="-",
         domain="申請状態", phys="appl_status"),
    item(7, "実績日付", "label", "BT_ACTUAL_COST.expense_date",
         edit="読み取り専用。実績費用明細の行項目", req="-", domain="日付", phys="expense_date"),
    item(8, "費目", "label", "BT_ACTUAL_COST.category",
         edit="コードC0010001のコード値名称を表示。明細の行項目", req="-",
         domain="費目", phys="category"),
    item(9, "実績金額", "label", "BT_ACTUAL_COST.actual_amount",
         edit="#,##0 円で表示。明細の行項目", req="-", domain="金額", phys="actual_amount"),
    item(10, "実績費用合計", "label", "BT_ACTUAL_COST.actual_amount（合計）",
         edit="実績費用明細のactual_amountの合計を #,##0 円で表示", req="-",
         domain="金額", phys="-"),
]

# --- WBT0303 出張実績登録完了画面（完了）---
WBT0303_ITEMS = [
    item(1, "完了メッセージ", "label", "-",
         edit="メッセージMSG10005「出張実績を登録しました。」を表示", req="-", domain="-", phys="-"),
    item(2, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="実績を登録した出張申請の申請IDを表示", req="-", domain="申請ID", phys="application_id"),
]


def io(no, name, io_="I", c="-", r="-", u="-", d="-", lock="-", kind="テーブル", note="-"):
    return {"no": no, "name": name, "kind": kind, "io": io_,
            "c": c, "r": r, "u": u, "d": d, "lock": lock, "note": note}


WBT0301_IO = [
    io(1, "BT_APPLICATION", io_="I", r="○", note="対象の出張申請（参照領域）を取得する"),
    io(2, "BT_PLANNED_COST", io_="I", r="○", note="予定費用明細を取得し予定費用合計を算出する"),
]
WBT0302_IO = [
    io(1, "BT_APPLICATION", io_="IO", r="○", u="○",
       note="事前条件チェックのため取得し、appl_statusを実績登録済に更新する"),
    io(2, "BT_ACTUAL_COST", io_="O", c="○", note="実績費用明細を新規登録する"),
    io(3, "BT_PLANNED_COST", io_="I", r="○", note="予定費用合計の再表示のため取得する"),
]
WBT0303_IO = [
    io(1, "-", io_="-", kind="-", note="該当なし"),
]


def evt(no, name, timing, summary, dest, comm):
    return {"no": no, "name": name, "timing": timing,
            "summary": summary, "dest": dest, "comm": comm}


WBT0301_EVT = [
    evt(1, "初期表示", "‐",
        "対象の出張申請の参照情報（申請ID・出張目的・出張期間・費用負担区分・予定費用合計・"
        "事前承認状態）を表示し、実績費用明細を1行表示する。",
        "-", "あり(同期)"),
    evt(2, "確認", "「確認」ボタン押下",
        "入力内容のバリデーションを行い、出張実績登録確認画面を表示する。",
        "出張実績登録確認", "あり(同期)"),
    evt(3, "明細追加・削除", "「明細を追加」「削除」ボタン押下",
        "実績費用明細の入力行を追加、または指定行を削除する。",
        "-", "なし"),
    evt(4, "戻る", "「一覧に戻る」ボタン押下",
        "入力内容を破棄し、出張申請一覧画面に戻る。",
        "出張申請一覧", "なし"),
]
WBT0302_EVT = [
    evt(1, "登録", "「登録」ボタン押下",
        "対象申請の状態を確認のうえ出張実績を登録し、出張実績登録完了画面を表示する。",
        "出張実績登録完了", "あり(同期)"),
    evt(2, "戻る", "「戻る」ボタン押下",
        "出張実績登録画面に戻る。",
        "出張実績登録", "あり(同期)"),
]
WBT0303_EVT = [
    evt(1, "次へ", "「一覧へ」ボタン押下",
        "出張申請一覧画面を表示する。",
        "出張申請一覧", "あり(同期)"),
]

# ---- 2.6 画面イベント詳細（自由記述）----
WBT0301_DETAIL = [
    {"D": "2.6.1. 初期表示イベント"},
    {"E": "(1) 表示処理"},
    {"F": "・遷移元から引き継いだapplication_idをキーにBT_APPLICATION・BT_PLANNED_COSTを取得する。"},
    {"F": "・参照領域に申請ID・出張目的・出張期間・費用負担区分を表示する。"},
    {"F": "・予定費用合計はBT_PLANNED_COST.planned_amountを合計して表示する。"},
    {"F": "・事前承認状態はBT_APPLICATION.appl_statusのコード値名称（'30':事前承認済 / '21':事前承認不要）を表示する。"},
    {"F": "・実績費用明細を1行初期表示する（実績日付・実績金額は空欄、費目の初期選択は交通費(01)）。"},
    {},
    {"D": "2.6.2. 確認イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "No.", "G": "バリデーション名", "M": "バリデーション内容", "W": "メッセージID", "AD": "後続判定"},
    {"F": 1, "G": "明細単項目必須",
     "M": "各明細の実績日付・費目・実績金額が入力されていること。",
     "W": "MSG90001", "AD": "終了する"},
    {"F": 2, "G": "明細必須",
     "M": "実績費用明細が1件以上入力されていること。",
     "W": "MSG90003", "AD": "終了する"},
    {"F": 3, "G": "実績金額範囲", "M": "各明細の実績金額が0以上の整数であること。",
     "W": "MSG90004", "AD": "終了する"},
    {"F": 4, "G": "実績日付範囲",
     "M": "各明細の実績日付が出張期間（start_date〜end_date）内であること。",
     "W": "MSG90005", "AD": "終了する"},
    {"F": "上記バリデーションで一箇所でもエラーが発生した場合、後続の処理は実施しない。"},
    {},
    {"E": "(2) 表示処理"},
    {"F": "入力内容を出張実績登録確認画面（WBT0302）に引き継ぎ、確認画面を表示する。"},
]

# WBT0302 登録イベント詳細 = 実績登録の事前条件チェック＋状態遷移の埋没ロジック（この設計書の核心）
WBT0302_DETAIL = [
    {"D": "2.6.1. 登録イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "本画面ではバリデーションを行わない（入力値の妥当性は確認イベント（WBT0301）で検証済みのため）。"},
    {},
    {"E": "(2) 事前条件チェック処理"},
    {"F": "(a) 引き継いだapplication_idをキーにBT_APPLICATIONを取得し、appl_statusを確認する。"},
    {"F": "(b) appl_statusが'30'（事前承認済）または'21'（事前承認不要）以外の場合、"
          "エラーメッセージ（MSGE0003）を表示して処理を終了する。"},
    {},
    {"E": "(3) DBアクセス（登録処理）"},
    {"F": "(a) 出張実績費用テーブル（BT_ACTUAL_COST）へ実績費用明細を明細件数分INSERTする（line_noは1からの連番）。"},
    {"F": "(b) 出張申請テーブル（BT_APPLICATION）のappl_statusを'40'（実績登録済）に更新し、version_noに1を加算する。"},
    {"F": "(c) 実績登録後、最終承認依頼メール（MBT03）を申請者の上長（BT_EMPLOYEE.manager_id）へ送信する。"},
    {},
    {"E": "(4) 更新項目の設定値"},
    {"G": "登録・更新項目", "P": "設定値"},
    {"G": "BT_ACTUAL_COST.application_id", "P": "対象の申請ID（application_id）"},
    {"G": "BT_ACTUAL_COST.line_no", "P": "1からの連番"},
    {"G": "BT_ACTUAL_COST.expense_date / category / actual_amount", "P": "画面入力値"},
    {"G": "BT_APPLICATION.appl_status", "P": "'40'（実績登録済）"},
    {"G": "BT_APPLICATION.version_no", "P": "更新前のversion_no + 1"},
    {},
    {"E": "(5) 表示処理"},
    {"F": "登録完了後、申請IDを引き継いで出張実績登録完了画面（WBT0303）を表示する。"},
]

WBT0303_DETAIL = [
    {"D": "2.6.1. 次へイベント"},
    {"E": "(1) 表示処理"},
    {"F": "出張申請一覧画面（WBT0501）を表示する。"},
]


def hand(no, name, store, value, desc, note="-"):
    return {"no": no, "name": name, "store": store, "value": value, "desc": desc, "note": note}


SCREENS = [
    {
        "title": "2. WBT0301(出張実績登録画面)",
        "b5": "2. WBT0301(出張実績登録画面)",
        "area": "領域名：出張実績入力",
        "items": WBT0301_ITEMS,
        "io": WBT0301_IO,
        "events": WBT0301_EVT,
        "detail": WBT0301_DETAIL,
        "hand_event": "（1） 確認イベント",
        "hand_group": "項目グループ：出張実績登録",
        "hand_prefix": "プレフィックス：BTS03",
        "hand_items": [
            hand(1, "申請ID", "リクエストスコープ", "application_id",
                 "対象の出張申請の申請ID。確認・完了画面へ引き継ぐ。"),
            hand(2, "出張実績入力内容一式", "リクエストスコープ", "‐",
                 "参照領域の表示内容および実績費用明細を一括して確認画面へ引き継ぐ。",
                 "入力画面の全項目をまとめて引き継ぐ"),
        ],
    },
    {
        "title": "3. WBT0302(出張実績登録確認画面)",
        "b5": "3. WBT0302(出張実績登録確認画面)",
        "area": "領域名：出張実績確認",
        "items": WBT0302_ITEMS,
        "io": WBT0302_IO,
        "events": WBT0302_EVT,
        "detail": WBT0302_DETAIL,
        "hand_event": "（1） 登録イベント",
        "hand_group": "項目グループ：出張実績登録",
        "hand_prefix": "プレフィックス：BTS03",
        "hand_items": [
            hand(1, "申請ID", "リクエストスコープ", "application_id",
                 "実績を登録した出張申請の申請ID。完了画面で表示する。"),
        ],
    },
    {
        "title": "4. WBT0303(出張実績登録完了画面)",
        "b5": "4. WBT0303(出張実績登録完了画面)",
        "area": "領域名：登録結果",
        "items": WBT0303_ITEMS,
        "io": WBT0303_IO,
        "events": WBT0303_EVT,
        "detail": WBT0303_DETAIL,
        "hand_event": "（1） 次へイベント",
        "hand_group": "‐（引き継ぎ項目なし）",
        "hand_prefix": "‐",
        "hand_items": [],
    },
]


# ------------------------------------------------------------------
# 記入
# ------------------------------------------------------------------
def fill_overview(ws):
    put(ws, "G8", TRANSACTION["id"])
    put(ws, "G9", TRANSACTION["name"])
    put(ws, "G10", TRANSACTION["overview"])
    put(ws, "G30", TRANSACTION["user"])


def fill_screen(ws, sc):
    put(ws, "B5", sc["b5"])
    # 2.2 一覧表示（本取引はいずれの画面も一覧表示なし）
    write_table(ws, LIST_ROWS, LIST_COL,
                [{"no": 1, "name": "-", "paging": "-", "sort": "-", "note": "該当なし"}])
    # 2.3 画面項目定義
    put(ws, AREA_CELL, sc["area"])
    write_table(ws, ITEM_ROWS, ITEM_COL, sc["items"])
    # 2.4 入出力一覧
    write_table(ws, IO_ROWS, IO_COL, sc["io"])
    # 2.5 画面イベント一覧
    write_table(ws, EVT_ROWS, EVT_COL, sc["events"])
    # 2.6 画面イベント詳細
    write_detail(ws, sc["detail"])
    # 画面引継ぎ項目
    put(ws, HAND_EVENT_CELL, sc["hand_event"])
    put(ws, HAND_GROUP_CELL, sc["hand_group"])
    put(ws, HAND_PREFIX_CELL, sc["hand_prefix"])
    write_table(ws, HAND_ROWS, HAND_COL, sc["hand_items"])
    # テンプレに残る2つ目のグループ見出し・明細行を掃除する
    end_row = HAND_ROWS[0] + len(sc["hand_items"])
    for r in range(end_row, HAND_CLEAR_TO + 1):
        clear_cells(ws, r, list(HAND_COL.keys()) + ["L"])


def fill_toc(wb):
    toc = wb["目次"]
    put(toc, "B7", "1. 画面取引定義")
    put(toc, "C8", "1.1. 取引概要")
    base = 10
    for i, sc in enumerate(SCREENS):
        put(toc, f"B{base + i * 6}", sc["b5"])


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    # 取引概要シート
    ov = wb[OVERVIEW_SHEET]
    ov.title = "1. 画面取引定義"
    fill_overview(ov)

    # 画面シート: 空の複製元から必要枚数を先に複製してから記入する
    base = wb[BASE_SCREEN]
    sheets = [base]
    for _ in range(len(SCREENS) - 1):
        sheets.append(wb.copy_worksheet(base))
    for ws, sc in zip(sheets, SCREENS):
        ws.title = sc["title"]
        fill_screen(ws, sc)

    # シート順を 表紙,変更履歴,目次,取引概要,[画面群],データ に整える
    order = ["表紙", "変更履歴", "目次", "1. 画面取引定義"] + \
            [sc["title"] for sc in SCREENS] + ["データ"]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    fill_toc(wb)

    # 印刷範囲を内容全体（引継ぎ項目まで）に張り直す。画面機能設計書の印刷右端は AI(35)。
    for ws in [ov] + sheets:
        set_print_area(ws, right_col=35)

    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
