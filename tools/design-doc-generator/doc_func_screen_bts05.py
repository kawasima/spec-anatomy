"""システム機能設計書(画面) — BTS05 出張申請一覧（1画面取引）。

出張申請一覧は「出張申請一覧画面（WBT0501）」1画面で構成する取引。一般社員は自身の
出張申請の状態を確認し、上長は配下の申請を確認する。行クリックで申請の状態に応じた各画面へ
遷移する。従来SIの設計をそのまま写す。特に次の点は「直す」対象ではなく「そのまま書く」対象:

- 一覧の「状態」列は申請状態コード（appl_status）のコード値をそのまま表示する。状態フィルタも
  コード値（'00'〜'90'）で絞り込む。業務的な状態概念は現れず、コード値の羅列で扱う。
- 画面項目定義はテーブル駆動。情報取得元に「テーブル.カラム」を書き、内部設計情報の
  画面項目名（物理）にDBの物理カラム名をそのまま書く。
- 行選択イベントの遷移先を、appl_status のコード値による if 分岐として画面イベント詳細に
  自然言語で羅列する（'00'/'31'なら登録編集、'20'なら事前承認、'21'/'30'なら実績登録、'40'なら
  最終承認…）。なぜその状態がその画面へ向かうのか（Why）は書かない。
- 取消も同様に、取消可能な appl_status（'10'〜'40'）を処理詳細に羅列し、取消時は appl_status を
  '90'（取消済）に UPDATE して cancelled_at を設定する、と手続き的に書く。なぜ '50' 以降が取消
  不可なのか（最終承認後は取り消せない）という理由（Why）は書かない。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(画面)_BTS05_出張申請一覧.xlsx"
OUTPUT = "システム機能設計書(画面)_BTS05_出張申請一覧.xlsx"
PRODUCT = "システム機能設計書（画面）\n\nBTS05/出張申請一覧"

OVERVIEW_SHEET = "1.1. 取引概要"   # テンプレの取引概要シート
BASE_SCREEN = "2. 画面ID(画面名)"  # 画面シート

# 取引概要
TRANSACTION = {
    "id": "BTS05",
    "name": "出張申請一覧",
    "overview": (
        "一般社員が自身の出張申請の一覧および状態を確認する場合、または上長が配下社員の"
        "出張申請を確認する場合に本業務取引を使用する。"
        "本取引は出張申請一覧画面（WBT0501）1画面で構成する。"
        "一覧の各行をクリックすると、当該申請の申請状態（APPL_STATUS）に応じて、"
        "出張申請登録・事前承認・実績登録・最終承認の各画面へ遷移する。"
        "また、最終承認前（APPL_STATUS='10'〜'40'）の申請は、一覧上の取消ボタンから取り消すことができる。"
    ),
    "user": "一般社員 / 上長",
}

# ---- 列マップ（BTS01 と同一テンプレのため共通）----
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
HAND_ROWS = (132, 132, 132)     # 引継ぎ明細
HAND_CLEAR_TO = 134             # テンプレ既存明細行の掃除対象


# ------------------------------------------------------------------
# 汎用ヘルパ（BTS01 と同一）
# ------------------------------------------------------------------
def clone_row_style(ws, src: int, dst: int, max_col: int = 54):
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


def put_none(ws, coord: str):
    from common import _anchor_coord
    ws[_anchor_coord(ws, coord)] = None


def clear_cells(ws, row: int, cols):
    for col in cols:
        put_none(ws, f"{col}{row}")


def write_table(ws, rows_def, colmap, records):
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
# 画面定義データ（WBT0501 出張申請一覧画面）
# ------------------------------------------------------------------
def item(no, name, kind, src, edit="-", init="-", req="-", domain="-", phys="-"):
    return {"no": no, "name": name, "kind": kind, "src": src, "edit": edit,
            "init": init, "req": req, "domain": domain, "phys": phys}


# 2.2 一覧表示
WBT0501_LIST = [
    {"no": 1, "name": "申請一覧", "paging": "あり（20件／ページ）",
     "sort": "申請日時（submitted_at）降順",
     "note": "検索条件に合致する出張申請を一覧表示する。"},
]

# 2.3 画面項目定義（No.1〜4:検索条件 / No.5〜11:一覧明細）
WBT0501_ITEMS = [
    item(1, "状態フィルタ", "select(pulldown)", "BT_APPLICATION.appl_status",
         edit="コードC0030001の申請状態コード（'00'/'10'/'20'/'21'/'30'/'31'/'40'/'50'/'60'/'90'の10コード）"
              "から選択する。選択したコード値でappl_statusを絞り込む。'90'を選択すると取消済の申請を絞り込む。",
         init="全て", domain="申請状態", phys="appl_status"),
    item(2, "申請者フィルタ", "text", "BT_EMPLOYEE.employee_name",
         edit="氏名の前方一致で絞り込む。ログインユーザの役職が上長（配下社員を持つ社員）の場合のみ"
              "表示する。一般社員の場合は非表示とし、自身の申請のみを対象とする。",
         init="（空）", domain="氏名", phys="employee_name"),
    item(3, "申請期間（開始）", "text", "BT_APPLICATION.submitted_at",
         edit="YYYYMMDD形式。submitted_atが本項目以降の申請を対象とする。", init="（空）",
         domain="日付", phys="submitted_at"),
    item(4, "申請期間（終了）", "text", "BT_APPLICATION.submitted_at",
         edit="YYYYMMDD形式。submitted_atが本項目以前の申請を対象とする。", init="（空）",
         domain="日付", phys="submitted_at"),
    item(5, "申請ID", "link", "BT_APPLICATION.application_id",
         edit="申請IDを表示する。クリックで行選択イベントを発火する。",
         domain="申請ID", phys="application_id"),
    item(6, "申請者", "label", "BT_EMPLOYEE.employee_name",
         edit="applicant_idに対応する社員の氏名を表示する。", domain="氏名", phys="employee_name"),
    item(7, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="全角20文字を超える場合は末尾を省略（…）して表示する。",
         domain="出張目的", phys="purpose"),
    item(8, "出張期間", "label", "BT_APPLICATION.start_date / end_date",
         edit="start_date 〜 end_date を YYYYMMDD 〜 YYYYMMDD 形式で表示する。",
         domain="日付", phys="start_date / end_date"),
    item(9, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="当該申請のplanned_amountを合計し #,##0 円で表示する。",
         domain="金額", phys="-"),
    item(10, "状態", "label", "BT_APPLICATION.appl_status",
         edit="appl_status（申請状態コード）の値をそのまま表示する"
              "（'00'/'10'/'20'/'21'/'30'/'31'/'40'/'50'/'60'/'90'）。",
         domain="申請状態", phys="appl_status"),
    item(11, "申請日時", "label", "BT_APPLICATION.submitted_at",
         edit="submitted_atを YYYYMMDD 形式で表示する。NULL（下書き）の場合は「-」を表示する。",
         domain="日付", phys="submitted_at"),
    item(12, "取消ボタン", "button", "-",
         edit="選択行の申請を取り消す。appl_statusが'10'/'20'/'21'/'30'/'31'/'40'の行を選択した場合"
              "のみ活性とする。押下時、取消確認ダイアログを表示する（2.6.5参照）。",
         domain="-", phys="-"),
]


def io(no, name, io_="I", c="-", r="-", u="-", d="-", lock="-", kind="テーブル", note="-"):
    return {"no": no, "name": name, "kind": kind, "io": io_,
            "c": c, "r": r, "u": u, "d": d, "lock": lock, "note": note}


WBT0501_IO = [
    io(1, "BT_APPLICATION", io_="IO", r="○", u="○",
       note="検索条件に合致する出張申請を検索する。取消時はappl_statusを'90'に更新しcancelled_atを設定する"),
    io(2, "BT_EMPLOYEE", io_="I", r="○", note="申請者・上長（配下判定）の情報を取得する"),
    io(3, "BT_PLANNED_COST", io_="I", r="○", note="申請ごとの予定費用合計を集計する"),
]


def evt(no, name, timing, summary, dest, comm):
    return {"no": no, "name": name, "timing": timing,
            "summary": summary, "dest": dest, "comm": comm}


WBT0501_EVT = [
    evt(1, "初期表示", "画面遷移時",
        "ログインユーザを対象に出張申請を検索し、一覧を表示する。上長の場合は申請者フィルタを表示する。",
        "-", "あり(同期)"),
    evt(2, "検索", "「検索」ボタン押下",
        "検索条件（状態フィルタ・申請者フィルタ・申請期間）で出張申請を再検索し、一覧を更新する。",
        "出張申請一覧", "あり(同期)"),
    evt(3, "行選択", "一覧行（申請ID）クリック",
        "選択した申請のappl_statusに応じて遷移先画面を決定し、遷移する。",
        "申請状態により決定（2.6.3参照）", "あり(同期)"),
    evt(4, "新規作成", "「新規申請」ボタン押下",
        "出張申請登録画面を新規入力状態で表示する。",
        "出張申請登録", "なし"),
    evt(5, "取消", "「取消」ボタン押下",
        "選択した申請の取消可否をappl_statusにより判定し、取消可能な場合はappl_statusを'90'（取消済）に"
        "更新し、cancelled_atに取消日時を設定する。",
        "出張申請一覧", "あり(同期)"),
]

# ---- 2.6 画面イベント詳細（自由記述）----
WBT0501_DETAIL = [
    {"D": "2.6.1. 初期表示イベント"},
    {"E": "(1) 検索処理"},
    {"F": "・ログインユーザの役職から配下社員の有無を判定し、配下を持つ場合は上長とみなす。"},
    {"F": "・一般社員の場合、applicant_id＝ログインユーザの社員IDの出張申請のみを検索対象とする。"},
    {"F": "・上長の場合、配下社員（manager_id＝ログインユーザの社員ID）の出張申請を検索対象とし、"
          "申請者フィルタを表示する。"},
    {"F": "・検索結果は申請日時（submitted_at）の降順に整列し、20件／ページでページングする。"},
    {"E": "(2) 表示処理"},
    {"F": "・一覧の「状態」列にはappl_statusのコード値をそのまま表示する。"},
    {"F": "・予定費用合計は、申請ごとにBT_PLANNED_COST.planned_amountを合計して表示する。"},
    {"D": "2.6.2. 検索イベント"},
    {"E": "(1) 検索条件の組み立て"},
    {"F": "・状態フィルタが「全て」以外の場合、appl_status＝選択コード値を検索条件に加える。"},
    {"F": "・申請者フィルタが入力されている場合（上長のみ）、employee_nameの前方一致を条件に加える。"},
    {"F": "・申請期間（開始／終了）が入力されている場合、submitted_atの範囲条件を加える。"},
    {"F": "・組み立てた条件でBT_APPLICATIONを再検索し、一覧を更新する。"},
    {"D": "2.6.3. 行選択イベント"},
    {"E": "(1) 遷移先決定処理"},
    {"F": "選択行のappl_statusの値により、遷移先画面を次のとおり決定する。"},
    {"F": "・appl_statusが'00'の場合、出張申請登録画面（WBT0101）を編集モードで表示する。"},
    {"F": "・appl_statusが'10'の場合、出張申請参照画面（本取引では対象外）を表示する。"},
    {"F": "・appl_statusが'20'の場合、出張申請事前承認画面（WBT0201）を表示する。"},
    {"F": "・appl_statusが'21'の場合、出張実績登録画面（WBT0301）を表示する。"},
    {"F": "・appl_statusが'30'の場合、出張実績登録画面（WBT0301）を表示する。"},
    {"F": "・appl_statusが'31'の場合、出張申請登録画面（WBT0101）を編集モード（差し戻し修正）で表示する。"},
    {"F": "・appl_statusが'40'の場合、出張申請最終承認画面（WBT0401）を表示する。"},
    {"F": "・appl_statusが'50'の場合、出張申請参照画面（本取引では対象外）を表示する。"},
    {"F": "遷移時はapplication_idとappl_statusを遷移先画面へ引き継ぐ。"},
    {"D": "2.6.4. 新規作成イベント"},
    {"E": "(1) 表示処理"},
    {"F": "出張申請登録画面（WBT0101）を新規入力状態で表示する。引き継ぎ項目はなし。"},
    {"D": "2.6.5. 取消イベント"},
    {"E": "(1) 取消可否判定"},
    {"F": "選択行のappl_statusにより取消の可否を判定する。appl_statusが'10'/'20'/'21'/'30'/'31'/'40'の"
          "いずれかの場合のみ取消可能とし、取消ボタンを活性とする。appl_statusが'00'の場合は取消不可とし、"
          "下書きの破棄（WBT0101）で対応する。appl_statusが'50'/'60'/'90'のいずれかの場合は取消不可とし、"
          "取消ボタンを非活性とする。"},
    {"E": "(2) 取消処理"},
    {"F": "取消ボタン押下時、取消確認ダイアログを表示する。利用者が確認した場合、BT_APPLICATION.appl_statusを"
          "'90'（取消済）にUPDATEし、cancelled_atに取消日時（システム日時）を設定する。取消完了メッセージを"
          "表示し、一覧を再表示する。"},
]


def hand(no, name, store, value, desc, note="-"):
    return {"no": no, "name": name, "store": store, "value": value, "desc": desc, "note": note}


WBT0501_HAND = [
    hand(1, "申請ID", "リクエストスコープ", "選択行のapplication_id",
         "行選択した出張申請の申請ID。遷移先画面で対象申請を特定する。"),
    hand(2, "申請状態", "リクエストスコープ", "選択行のappl_status",
         "行選択した出張申請の申請状態コード。遷移先画面での表示・制御に用いる。"),
]


SCREEN = {
    "title": "2. WBT0501(出張申請一覧画面)",
    "b5": "2. WBT0501(出張申請一覧画面)",
    "area": "領域名：出張申請一覧（検索条件・一覧明細）",
    "list": WBT0501_LIST,
    "items": WBT0501_ITEMS,
    "io": WBT0501_IO,
    "events": WBT0501_EVT,
    "detail": WBT0501_DETAIL,
    "hand_event": "（1） 行選択イベント",
    "hand_group": "項目グループ：出張申請一覧",
    "hand_prefix": "プレフィックス：BTS05",
    "hand_items": WBT0501_HAND,
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
    # 2.2 一覧表示
    write_table(ws, LIST_ROWS, LIST_COL, sc["list"])
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

    # 画面シート（1枚）
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
