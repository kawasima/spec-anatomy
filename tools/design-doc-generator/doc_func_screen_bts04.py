"""システム機能設計書(画面) — BTS04 最終承認（1画面取引）。

最終承認は「出張申請最終承認画面(WBT0401)」の1画面で構成する取引。実績登録済の出張申請
について、申請者の上長（課長・部長）が予定費用と実績費用を照合して最終承認し、立て替えた
金額を経理システムへ連携する。従来SIの設計をそのまま写す。特に次の点は「直す」対象では
なく「そのまま書く」対象:

- 画面項目定義はテーブル駆動。情報取得元に「テーブル.カラム」を書き、内部設計情報の
  画面項目名(物理)にDBの物理カラム名をそのまま書く。費用比較の差額・合計は派生表示だが、
  派生元の業務概念は現れず、予定/実績カラムの引き算・合計として書く。
- 最終承認の可否判定と状態更新を、最終承認イベント処理詳細に自然言語の手続きとして埋没
  させる。approver_id が申請者の上長(BT_EMPLOYEE.manager_id)か、appl_status が'40'か、と
  いった判定を並べ、なぜ上長でなければならないか(Why)は書かない。
- 精算額の算出を、独立した共通コンポーネント【CC0002：精算額計算】の呼び出しとして設計する。
  自社負担なら実績費用合計、先方負担なら0円という業務ロジックはこのコンポーネントに埋没する。
  （afterの仕様モデルではこの概念は「最終承認する」behaviorに吸収され、独立関数としては消える。）
- 経理連携は共通コンポーネント【CC0003：経理連携データ作成】の呼び出しとして、算出した精算額を
  経理I/Fファイル（IBT01）へ出力する手続きとして書く。さらに固定長レイアウト（外部インタフェース
  設計書 IBT01 の明細レコードに従う）や、精算額が0円でもヘッダ・データ・トレーラを各1件必ず
  出力するといったファイル都合の詳細を、画面イベント詳細にそのまま書き込む。（afterではこの
  ファイル都合の詳細はShellの永続／外部I/Fに隔離され、画面の仕様からは切り離される。）
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(画面)_BTS04_最終承認.xlsx"
OUTPUT = "システム機能設計書(画面)_BTS04_最終承認.xlsx"
PRODUCT = "システム機能設計書（画面）\n\nBTS04/最終承認"

OVERVIEW_SHEET = "1.1. 取引概要"   # テンプレの取引概要シート
BASE_SCREEN = "2. 画面ID(画面名)"  # 複製元の画面シート

# 取引概要
TRANSACTION = {
    "id": "BTS04",
    "name": "最終承認",
    "overview": (
        "実績登録済（申請状態APPL_STATUS='40'）の出張申請について、申請者の上長（課長・部長）が"
        "予定費用と実績費用を照合し、最終承認する場合に本業務取引を使用する。"
        "本取引は出張申請最終承認画面（WBT0401）の1画面で構成する。"
        "最終承認時に共通コンポーネント【CC0002：精算額計算】により精算額を算出し、"
        "共通コンポーネント【CC0003：経理連携データ作成】により精算額を経理システムへ連携する。"
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


def put_none(ws, coord: str):
    from common import _anchor_coord
    ws[_anchor_coord(ws, coord)] = None


def clear_cells(ws, row: int, cols):
    for col in cols:
        put_none(ws, f"{col}{row}")


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
def item(no, name, kind, src, edit="-", init="-", req="-", domain="-", phys="-"):
    return {"no": no, "name": name, "kind": kind, "src": src, "edit": edit,
            "init": init, "req": req, "domain": domain, "phys": phys}


# 画面項目はDBカラムに1:1（テーブル駆動）。差額・合計は予定/実績カラムの派生表示。
WBT0401_ITEMS = [
    # --- 参照領域 ---
    item(1, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="読み取り専用。BT+YYYYMMDD+連番6桁で表示", domain="申請ID", phys="application_id"),
    item(2, "申請者", "label", "BT_EMPLOYEE.employee_name",
         edit="読み取り専用。申請者（applicant_id）の氏名を表示", domain="氏名", phys="employee_name"),
    item(3, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="読み取り専用", domain="出張目的", phys="purpose"),
    item(4, "出張開始日", "label", "BT_APPLICATION.start_date",
         edit="読み取り専用。YYYY/MM/DD形式", domain="日付", phys="start_date"),
    item(5, "出張終了日", "label", "BT_APPLICATION.end_date",
         edit="読み取り専用。YYYY/MM/DD形式", domain="日付", phys="end_date"),
    item(6, "費用負担区分", "label", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001のコード値名称を表示（01:自社負担 / 02:先方負担）",
         domain="費用負担区分", phys="cost_bearing"),
    # --- 費用比較領域（明細行項目） ---
    item(7, "費目", "label", "BT_PLANNED_COST.category / BT_ACTUAL_COST.category",
         edit="コードC0010001のコード値名称を表示（01:交通費 / 02:宿泊費 / 03:交際費）。明細の行項目",
         domain="費目", phys="category"),
    item(8, "予定金額", "label", "BT_PLANNED_COST.planned_amount",
         edit="#,##0 円で表示。明細の行項目", domain="金額", phys="planned_amount"),
    item(9, "実績金額", "label", "BT_ACTUAL_COST.actual_amount",
         edit="#,##0 円で表示。予定金額を超過する行は赤字で表示。明細の行項目",
         domain="金額", phys="actual_amount"),
    item(10, "差額", "label", "BT_ACTUAL_COST.actual_amount − BT_PLANNED_COST.planned_amount",
         edit="実績金額から予定金額を減算した値を #,##0 円で表示。明細の行項目",
         domain="金額", phys="-"),
    item(11, "合計", "label",
         "BT_PLANNED_COST.planned_amount（合計） / BT_ACTUAL_COST.actual_amount（合計）",
         edit="予定金額・実績金額をそれぞれ合計し #,##0 円でフッタ行に表示",
         domain="金額", phys="-"),
    item(12, "差額合計", "label",
         "BT_ACTUAL_COST.actual_amount（合計） − BT_PLANNED_COST.planned_amount（合計）",
         edit="実績金額合計から予定金額合計を減算した値を #,##0 円でフッタ行に表示",
         domain="金額", phys="-"),
    # --- 操作領域 ---
    item(13, "最終承認ボタン", "button", "-",
         edit="ラベル「最終承認」。押下で最終承認イベントを起動する", domain="-", phys="-"),
    item(14, "戻るボタン", "button", "-",
         edit="ラベル「一覧に戻る」。押下で出張申請一覧画面へ遷移する", domain="-", phys="-"),
]


def io(no, name, io_="I", c="-", r="-", u="-", d="-", lock="-", kind="テーブル", note="-"):
    return {"no": no, "name": name, "kind": kind, "io": io_,
            "c": c, "r": r, "u": u, "d": d, "lock": lock, "note": note}


WBT0401_IO = [
    io(1, "BT_APPLICATION", io_="I/O", r="○", u="○",
       note="対象の出張申請を取得する。最終承認時に appl_status・finalized_at・approver_id を更新する"),
    io(2, "BT_PLANNED_COST", io_="I", r="○", note="対象申請の予定費用明細を取得する"),
    io(3, "BT_ACTUAL_COST", io_="I", r="○", note="対象申請の実績費用明細を取得する"),
    io(4, "BT_EMPLOYEE", io_="I", r="○", note="申請者・上長（承認者）の氏名・上長関係を取得する"),
]


def evt(no, name, timing, summary, dest, comm):
    return {"no": no, "name": name, "timing": timing,
            "summary": summary, "dest": dest, "comm": comm}


WBT0401_EVT = [
    evt(1, "初期表示", "‐",
        "一覧画面から引き継いだ申請IDをキーに対象申請と予定・実績費用を取得し、"
        "参照領域と費用比較領域を表示する。",
        "-", "あり(同期)"),
    evt(2, "最終承認", "「最終承認」ボタン押下",
        "承認可否をチェックのうえ申請状態を最終承認済（'50'）に更新し、精算額を算出して"
        "経理連携を行い、出張申請一覧画面へ遷移する。",
        "出張申請一覧", "あり(同期)"),
    evt(3, "戻る", "「一覧に戻る」ボタン押下",
        "処理を行わず、出張申請一覧画面に戻る。",
        "出張申請一覧", "なし"),
]

# ---- 2.6 画面イベント詳細（自由記述）----
# 2.6.2 最終承認イベント = 承認可否判定・精算額計算・経理連携の埋没ロジック（この設計書の核心）
WBT0401_DETAIL = [
    {"D": "2.6.1. 初期表示イベント"},
    {"E": "(1) データ取得処理"},
    {"F": "・出張申請一覧画面から引き継いだ application_id をキーに、BT_APPLICATION（出張申請）を1件取得する。"},
    {"F": "・application_id をキーに、BT_PLANNED_COST（予定費用）・BT_ACTUAL_COST（実績費用）を明細単位で取得する。"},
    {"F": "・applicant_id をキーに BT_EMPLOYEE から申請者の氏名を、approver_id をキーに上長（承認者）の氏名を取得する。"},
    {"E": "(2) 表示処理"},
    {"F": "・参照領域に申請ID・申請者・出張目的・出張期間・費用負担区分を表示する。"},
    {"F": "・費用比較領域に費目単位で予定金額・実績金額・差額を表示し、実績金額が予定金額を超過する行は赤字で表示する。"},
    {"F": "・予定金額合計・実績金額合計・差額合計をフッタ行に表示する。"},
    {},
    {"D": "2.6.2. 最終承認イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "本画面ではバリデーションを行わない（表示内容を確認し「最終承認」ボタンを押下するのみ）。"},
    {"E": "(2) 承認可否チェック処理"},
    {"F": "(1) approver_id（ログインユーザの社員ID）が申請者の上長でない場合"
          "（BT_EMPLOYEE.manager_id ≠ approver_id）、メッセージMSGE0002を表示し、後続処理を実施せず終了する。"},
    {"F": "(2) appl_status が '40'（実績登録済）以外の場合、状態が変化した旨のエラーメッセージを表示し、"
          "後続処理を実施せず終了する。"},
    {"E": "(3) 更新処理"},
    {"F": "BT_APPLICATION の appl_status に '50'（最終承認済）を、finalized_at にシステム日時を、"
          "approver_id にログインユーザ（上長）の社員IDをセットし、version_no を +1 して1件UPDATEする。"},
    {"E": "(4) 精算額算出処理"},
    {"F": "共通コンポーネント【CC0002：精算額計算】を呼び出し、精算額を算出する。"},
    {"F": "cost_bearing が '01'（自社負担）の場合は実績費用（BT_ACTUAL_COST.actual_amount）の合計額を、"
          "'02'（先方負担）の場合は0円を精算額とする。"},
    {"E": "(5) 経理連携処理"},
    {"F": "共通コンポーネント【CC0003：経理連携データ作成】を呼び出し、(4)で算出した精算額を経理I/Fファイル"
          "（IBT01：経理システム連携ファイル）へ出力する。出力レコードは固定長とし、レイアウトは下表のとおりとする。"},
    {"F": "精算額が0円の場合も、ヘッダレコード・データレコード・トレーラレコードを各1件必ず出力する"
          "（0円時のレコード抑止は行わない）。"},
    {"G": "項目", "K": "開始", "N": "長さ", "Q": "内容"},
    {"G": "レコード区分", "K": 1, "N": 1, "Q": "明細レコードを表す固定値 '2'。"},
    {"G": "申請ID", "K": 2, "N": 16,
     "Q": "application_id。半角英数字16桁。左詰めとし、残りは半角空白で埋める。"},
    {"G": "申請者社員番号", "K": 18, "N": 10, "Q": "applicant_id。半角英数字10桁。"},
    {"G": "精算額", "K": 28, "N": 9,
     "Q": "(4)で算出した精算額。半角数字9桁、右詰め前ゼロ埋め（0円の場合も 000000000 を出力する）。"},
    {"G": "費用負担区分", "K": 38, "N": 2, "Q": "cost_bearing。2桁（01:自社負担 / 02:先方負担）。"},
    {"G": "最終承認日", "K": 40, "N": 8, "Q": "finalized_at の日付部。YYYYMMDD形式の8桁。"},
    {"G": "部門コード", "K": 48, "N": 30, "Q": "申請者の所属部門コード（BT_EMPLOYEE.department_code）。"},
    {"G": "FILLER", "K": 78, "N": 24, "Q": "半角空白で埋める。"},
    {"F": "ヘッダレコードにはレコード区分'1'・ファイルID・作成日を、トレーラレコードにはレコード区分'9'・"
          "明細件数・精算額合計を出力する。レコードの詳細レイアウトは外部インタフェース設計書(IBT01)による。"},
    {"E": "(6) 表示処理"},
    {"F": "経理連携完了メッセージ（MSG10003）を表示し、出張申請一覧画面（WBT0501）へ遷移する。"},
]


def hand(no, name, store, value, desc, note="-"):
    return {"no": no, "name": name, "store": store, "value": value, "desc": desc, "note": note}


SCREENS = [
    {
        "title": "2. WBT0401(出張申請最終承認画面)",
        "b5": "2. WBT0401(出張申請最終承認画面)",
        "area": "領域名：出張申請最終承認",
        "items": WBT0401_ITEMS,
        "io": WBT0401_IO,
        "events": WBT0401_EVT,
        "detail": WBT0401_DETAIL,
        "hand_event": "（1） 初期表示イベント",
        "hand_group": "項目グループ：最終承認",
        "hand_prefix": "プレフィックス：BTS04",
        "hand_items": [
            hand(1, "申請ID", "リクエストスコープ", "選択した申請の application_id",
                 "出張申請一覧画面で選択した申請の申請ID。初期表示で対象申請の取得キーとして受け取る。"),
        ],
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
    # 2.2 一覧表示（本取引は一覧表示なし）
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

    # 画面シート（本取引は1画面。複製は不要）
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
