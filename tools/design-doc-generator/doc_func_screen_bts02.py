"""システム機能設計書(画面) — BTS02 事前承認（1画面取引）。

事前承認は「出張申請事前承認画面(WBT0201)」1画面で構成する取引。上長（課長／部長）が
事前承認の必要な出張申請を確認し、承認または却下を行う。従来SIの設計をそのまま写す。
特に次の点は「直す」対象ではなく「そのまま書く」対象:

- 画面項目定義はテーブル駆動。情報取得元に「テーブル.カラム」を書き、内部設計情報の
  画面項目名(物理)にDBの物理カラム名をそのまま書く。業務概念の派生元は現れない。
  事前承認要件も、なぜ事前承認が必要かという業務概念ではなく、appl_status・費用合計・
  role・費用負担区分から都度判定した文言表示として扱う。
- 承認・却下イベントの処理詳細に、承認者＝申請者の上長判定を自然言語のif羅列として
  埋没させる。なぜ上長でなければならないか(Why)は書かない。判定結果は申請状態コード
  (APPL_STATUS)の数値('20'→'30'/'31')で表す。状態は型ではなくコードで遷移する。
- 承認/却下でBT_APPLICATIONのappl_status・approver_id・approved_at・rejection_reasonを
  更新する手続きを処理詳細に書く。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(画面)_BTS02_事前承認.xlsx"
OUTPUT = "システム機能設計書(画面)_BTS02_事前承認.xlsx"
PRODUCT = "システム機能設計書（画面）\n\nBTS02/事前承認"

OVERVIEW_SHEET = "1.1. 取引概要"   # テンプレの取引概要シート
BASE_SCREEN = "2. 画面ID(画面名)"  # 画面シート（本取引は1画面）

# 取引概要
TRANSACTION = {
    "id": "BTS02",
    "name": "事前承認",
    "overview": (
        "上長（課長・部長）が、事前承認の必要な出張申請の内容（申請者・出張目的・出張期間・"
        "予定費用明細・予定費用合計・費用負担区分・事前承認要件）を確認し、承認または却下する場合に"
        "本業務取引を使用する。本取引は出張申請事前承認画面（WBT0201）の1画面で構成する。"
        "承認時は申請状態（APPL_STATUS）を事前承認済（'30'）に、却下時は事前承認却下（'31'）に更新する。"
    ),
    "user": "課長・部長（申請者の上長）",
}

# ---- 列マップ（空テンプレの列位置に合わせる）----
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
# 画面定義データ（WBT0201 出張申請事前承認画面）
# ------------------------------------------------------------------
def item(no, name, kind, src, edit="-", init="-", req="○", domain="-", phys="-"):
    return {"no": no, "name": name, "kind": kind, "src": src, "edit": edit,
            "init": init, "req": req, "domain": domain, "phys": phys}


WBT0201_ITEMS = [
    # ヘッダ領域（テーブル駆動：情報取得元にテーブル.カラム、物理名そのまま）
    item(1, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="申請IDをそのまま表示", req="-", domain="申請ID", phys="application_id"),
    item(2, "申請日時", "label", "BT_APPLICATION.submitted_at",
         edit="YYYY/MM/DD HH:MM形式で表示", req="-", domain="日付", phys="submitted_at"),
    item(3, "申請者", "label", "BT_EMPLOYEE.employee_name",
         edit="applicant_idをキーに取得した申請者の氏名を表示", req="-",
         domain="氏名", phys="employee_name"),
    item(4, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="全文表示", req="-", domain="出張目的", phys="purpose"),
    item(5, "出張期間", "label", "BT_APPLICATION.start_date / end_date",
         edit="YYYY/MM/DD 〜 YYYY/MM/DD形式で表示", req="-",
         domain="日付", phys="start_date / end_date"),
    item(6, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="予定費用明細のplanned_amountを合計して #,##0 円で表示", req="-",
         domain="金額", phys="-"),
    item(7, "費用負担", "label", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001のコード値名称（01:自社負担 / 02:先方負担）を表示", req="-",
         domain="費用負担区分", phys="cost_bearing"),
    # 事前承認要件領域（要否をカラムから都度判定した文言表示。業務概念としては持たない）
    item(8, "事前承認要件", "label", "BT_APPLICATION.appl_status / cost_bearing、BT_PLANNED_COST.planned_amount（合計）",
         edit="該当する事前承認要件の文言を列挙表示（高額出張 / 役職なし申請 / 先方負担申請）", req="-",
         domain="-", phys="-"),
    # 予定費用明細領域（行項目）
    item(9, "発生日", "label", "BT_PLANNED_COST.expense_date",
         edit="YYYY/MM/DD形式で表示。予定費用明細の行項目", req="-",
         domain="日付", phys="expense_date"),
    item(10, "費目", "label", "BT_PLANNED_COST.category",
         edit="コードC0010001のコード値名称を表示。明細の行項目", req="-",
         domain="費目", phys="category"),
    item(11, "予定金額", "label", "BT_PLANNED_COST.planned_amount",
         edit="#,##0 円で表示。明細の行項目", req="-", domain="金額", phys="planned_amount"),
    # 操作領域（却下理由。承認/却下ボタンはイベントで定義）
    item(12, "却下理由", "textarea", "BT_APPLICATION.rejection_reason",
         edit="全角500文字以内（1文字以上）。却下ボタン押下時に入力する", req="△（却下時必須）",
         domain="却下理由", phys="rejection_reason"),
]


def io(no, name, io_="I", c="-", r="-", u="-", d="-", lock="-", kind="テーブル", note="-"):
    return {"no": no, "name": name, "kind": kind, "io": io_,
            "c": c, "r": r, "u": u, "d": d, "lock": lock, "note": note}


WBT0201_IO = [
    io(1, "BT_APPLICATION", io_="I/O", r="○", u="○", lock="○",
       note="対象申請を取得し、承認/却下の結果（appl_status等）を更新する"),
    io(2, "BT_PLANNED_COST", io_="I", r="○", note="予定費用明細・予定費用合計を取得する"),
    io(3, "BT_EMPLOYEE", io_="I", r="○", note="申請者および承認者（上長）の情報を取得する"),
]


def evt(no, name, timing, summary, dest, comm):
    return {"no": no, "name": name, "timing": timing,
            "summary": summary, "dest": dest, "comm": comm}


WBT0201_EVT = [
    evt(1, "初期表示", "‐",
        "出張申請一覧画面または事前承認依頼メールのリンクから遷移し、対象申請（application_id）の"
        "内容・事前承認要件・予定費用明細を表示する。",
        "-", "あり(同期)"),
    evt(2, "承認", "「承認」ボタン押下",
        "承認権限・申請状態を確認のうえ、対象申請を事前承認済（'30'）に更新し、出張申請一覧画面に戻る。",
        "出張申請一覧", "あり(同期)"),
    evt(3, "却下", "「却下」ボタン押下",
        "承認権限・申請状態・却下理由を確認のうえ、対象申請を事前承認却下（'31'）に更新し、出張申請一覧画面に戻る。",
        "出張申請一覧", "あり(同期)"),
]

# ---- 2.6 画面イベント詳細（自由記述）----
# 承認・却下イベントに、承認者＝申請者の上長判定と申請状態コード遷移を埋没させる（Whyは書かない）。
WBT0201_DETAIL = [
    {"D": "2.6.1. 初期表示イベント"},
    {"E": "(1) 表示処理"},
    {"F": "・遷移元（一覧画面／事前承認依頼メール）から引き継いだ申請ID（application_id）をキーに"
          "BT_APPLICATIONを1件取得し、申請ID・申請日時・出張目的・出張期間・費用負担を表示する。"},
    {"F": "・applicant_idをキーにBT_EMPLOYEEを取得して申請者氏名を、application_idをキーに"
          "BT_PLANNED_COSTを取得して予定費用明細・予定費用合計を表示する。"},
    {"F": "・事前承認要件を次のとおり判定し、該当する要件の文言を表示する。"
          "予定費用合計≧100000なら「高額出張」、申請者のposition_code='99'なら「役職なし申請」、"
          "cost_bearing='02'なら「先方負担申請」。"},
    {},
    {"D": "2.6.2. 承認イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "No.", "G": "バリデーション名", "M": "バリデーション内容", "W": "メッセージID", "AD": "後続判定"},
    {"F": 1, "G": "承認権限",
     "M": "approver_id（ログインユーザの社員ID）が、申請者（applicant_id）のBT_EMPLOYEE.manager_idと一致すること。",
     "W": "MSGE0002", "AD": "終了する"},
    {"F": 2, "G": "申請状態",
     "M": "対象申請のappl_statusが'20'（事前承認待ち）であること。",
     "W": "MSGE0001", "AD": "終了する"},
    {"E": "(2) 更新処理"},
    {"F": "・BT_APPLICATIONを次の値で1件UPDATEする。appl_status='30'、"
          "approver_id=ログインユーザの社員ID、approved_at=システム日時、version_no=version_no+1。"},
    {"E": "(3) 表示処理"},
    {"F": "・完了メッセージMSG10001「事前承認が完了しました。」を表示し、出張申請一覧画面に戻る。"},
    {},
    {"D": "2.6.3. 却下イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "No.", "G": "バリデーション名", "M": "バリデーション内容", "W": "メッセージID", "AD": "後続判定"},
    {"F": 1, "G": "承認権限",
     "M": "approver_id（ログインユーザの社員ID）が、申請者（applicant_id）のBT_EMPLOYEE.manager_idと一致すること。",
     "W": "MSGE0002", "AD": "終了する"},
    {"F": 2, "G": "申請状態",
     "M": "対象申請のappl_statusが'20'（事前承認待ち）であること。",
     "W": "MSGE0001", "AD": "終了する"},
    {"F": 3, "G": "却下理由必須",
     "M": "却下理由（rejection_reason）が入力されていること（全角500文字以内、1文字以上）。",
     "W": "MSG90001", "AD": "終了する"},
    {"E": "(2) 更新処理"},
    {"F": "・BT_APPLICATIONを次の値で1件UPDATEする。appl_status='31'、"
          "approver_id=ログインユーザの社員ID、approved_at=システム日時、"
          "rejection_reason=画面入力値（却下理由）、version_no=version_no+1。"},
    {"F": "・却下後、事前承認却下通知メール（MBT02）を申請者へ送信する。"},
    {"E": "(3) 表示処理"},
    {"F": "・完了メッセージMSG10002「事前承認を却下しました。」を表示し、出張申請一覧画面に戻る。"},
]


def hand(no, name, store, value, desc, note="-"):
    return {"no": no, "name": name, "store": store, "value": value, "desc": desc, "note": note}


SCREEN = {
    "title": "2. WBT0201(出張申請事前承認画面)",
    "b5": "2. WBT0201(出張申請事前承認画面)",
    "area": "領域名：出張申請事前承認",
    "items": WBT0201_ITEMS,
    "io": WBT0201_IO,
    "events": WBT0201_EVT,
    "detail": WBT0201_DETAIL,
    "hand_event": "（1） 初期表示イベント",
    "hand_group": "項目グループ：事前承認",
    "hand_prefix": "プレフィックス：BTS02",
    "hand_items": [
        hand(1, "申請ID", "リクエストスコープ", "遷移元から引き継いだapplication_id",
             "事前承認対象の出張申請の申請ID。出張申請一覧画面または事前承認依頼メールから引き継ぐ。"),
    ],
}


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
    # 2.2 一覧表示（本画面は明細を単票表示扱いとし、一覧表示なし）
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
    put(toc, "B10", SCREEN["b5"])


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    # 取引概要シート
    ov = wb[OVERVIEW_SHEET]
    ov.title = "1. 画面取引定義"
    fill_overview(ov)

    # 画面シート（1画面）
    ws = wb[BASE_SCREEN]
    ws.title = SCREEN["title"]
    fill_screen(ws, SCREEN)

    # シート順を 表紙,変更履歴,目次,取引概要,画面,データ に整える
    order = ["表紙", "変更履歴", "目次", "1. 画面取引定義", SCREEN["title"], "データ"]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    fill_toc(wb)

    # 印刷範囲を内容全体（引継ぎ項目まで）に張り直す。画面機能設計書の印刷右端は AI(35)。
    for sh in [ov, ws]:
        set_print_area(sh, right_col=35)

    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
