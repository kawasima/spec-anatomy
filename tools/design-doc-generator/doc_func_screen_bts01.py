"""システム機能設計書(画面) — BTS01 出張申請登録（3画面取引）。

出張申請登録は「入力(WBT0101)→確認(WBT0102)→完了(WBT0103)」の3画面で構成する取引。
従来SIの設計をそのまま写す。特に次の点は「直す」対象ではなく「そのまま書く」対象:

- 画面項目定義はテーブル駆動。情報取得元に「テーブル.カラム」を書き、内部設計情報の
  画面項目名(物理)にDBの物理カラム名をそのまま書く。業務概念の派生元は現れない。
- 事前承認要否の判定を、確認画面の登録イベント処理詳細に自然言語のif羅列として埋没させる。
  なぜ10万円なのか・なぜ役職なしなのか・なぜ先方負担なのか(Why)は書かない。判定結果は
  申請状態コード(APPL_STATUS)の数値で表す。
- 登録処理で appl_status を更新し、approver_id等はNULLのまま、version_noに1を、
  application_idを採番する手続きを処理詳細に書く。
- 画面引継ぎ項目で入力→確認→完了へ出張申請の項目一式をまるごと引き継ぐ(スタンプ結合的)。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, write_detail_region, set_print_area

TEMPLATE = "システム機能設計書(画面)_BTS01_出張申請登録.xlsx"
OUTPUT = "システム機能設計書(画面)_BTS01_出張申請登録.xlsx"
PRODUCT = "システム機能設計書（画面）\n\nBTS01/出張申請登録"

OVERVIEW_SHEET = "1.1. 取引概要"   # テンプレの取引概要シート（複製元ではない）
BASE_SCREEN = "2. 画面ID(画面名)"  # 複製元の画面シート

# 取引概要
TRANSACTION = {
    "id": "BTS01",
    "name": "出張申請登録",
    "overview": (
        "一般社員が出張の予定（出張目的・出張期間・費用負担区分・出張者・予定費用明細）を入力し、"
        "出張申請を登録する場合に本業務取引を使用する。"
        "新規登録のほか、下書き（APPL_STATUS='00'）および事前承認却下による差し戻し（APPL_STATUS='31'）の"
        "申請を読み込んで編集・再申請する編集モードを備える。"
        "本取引は出張申請登録画面（入力）→出張申請登録確認画面（確認）→出張申請登録完了画面（完了）の"
        "3画面で構成する。登録時に事前承認要否および承認者を判定し、申請状態（APPL_STATUS）に反映する。"
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


WBT0101_ITEMS = [
    item(1, "出張目的", "textarea", "BT_APPLICATION.purpose",
         edit="全角500文字以内", req="○", domain="出張目的", phys="purpose"),
    item(2, "出張開始日", "text", "BT_APPLICATION.start_date",
         edit="YYYYMMDD形式。カレンダーピッカー", domain="日付", phys="start_date"),
    item(3, "出張終了日", "text", "BT_APPLICATION.end_date",
         edit="YYYYMMDD形式。開始日以降のみ選択可", domain="日付", phys="end_date"),
    item(4, "費用負担区分", "radio", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001（01:自社負担 / 02:先方負担）", init="自社負担（01）",
         domain="費用負担区分", phys="cost_bearing"),
    item(5, "出張者一覧", "label", "BT_EMPLOYEE.employee_name",
         edit="出張者の氏名を一覧表示。追加・削除ボタン付き", init="ログインユーザ",
         domain="氏名", phys="employee_name"),
    item(6, "発生日", "text", "BT_PLANNED_COST.expense_date",
         edit="YYYYMMDD形式。予定費用明細の行項目", domain="日付", phys="expense_date"),
    item(7, "費目", "select(pulldown)", "BT_PLANNED_COST.category",
         edit="コードC0010001（01:交通費 / 02:宿泊費 / 03:交際費）。明細の行項目",
         init="交通費（01）", domain="費目", phys="category"),
    item(8, "予定金額", "text", "BT_PLANNED_COST.planned_amount",
         edit="整数9桁・0以上。#,##0 円で表示。明細の行項目", domain="金額", phys="planned_amount"),
    item(9, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="予定費用明細のplanned_amountを合計して #,##0 円で表示", init="0", req="-",
         domain="金額", phys="-"),
]

WBT0102_ITEMS = [
    item(1, "出張目的", "label", "BT_APPLICATION.purpose",
         edit="読み取り専用", req="-", domain="出張目的", phys="purpose"),
    item(2, "出張開始日", "label", "BT_APPLICATION.start_date",
         edit="読み取り専用", req="-", domain="日付", phys="start_date"),
    item(3, "出張終了日", "label", "BT_APPLICATION.end_date",
         edit="読み取り専用", req="-", domain="日付", phys="end_date"),
    item(4, "費用負担区分", "label", "BT_APPLICATION.cost_bearing",
         edit="コードC0020001のコード値名称を表示", req="-", domain="費用負担区分", phys="cost_bearing"),
    item(5, "出張者一覧", "label", "BT_EMPLOYEE.employee_name",
         edit="出張者の氏名を一覧表示", req="-", domain="氏名", phys="employee_name"),
    item(6, "発生日", "label", "BT_PLANNED_COST.expense_date",
         edit="読み取り専用。予定費用明細の行項目", req="-", domain="日付", phys="expense_date"),
    item(7, "費目", "label", "BT_PLANNED_COST.category",
         edit="コードC0010001のコード値名称を表示。明細の行項目", req="-", domain="費目", phys="category"),
    item(8, "予定金額", "label", "BT_PLANNED_COST.planned_amount",
         edit="#,##0 円で表示。明細の行項目", req="-", domain="金額", phys="planned_amount"),
    item(9, "予定費用合計", "label", "BT_PLANNED_COST.planned_amount（合計）",
         edit="予定費用明細のplanned_amountの合計を #,##0 円で表示", req="-", domain="金額", phys="-"),
]

WBT0103_ITEMS = [
    item(1, "完了メッセージ", "label", "-",
         edit="メッセージMSG10004「出張申請を登録しました。」を表示", req="-", domain="-", phys="-"),
    item(2, "申請ID", "label", "BT_APPLICATION.application_id",
         edit="登録した出張申請の申請IDを表示", req="-", domain="申請ID", phys="application_id"),
]


def io(no, name, io_="I", c="-", r="-", u="-", d="-", lock="-", kind="テーブル", note="-"):
    return {"no": no, "name": name, "kind": kind, "io": io_,
            "c": c, "r": r, "u": u, "d": d, "lock": lock, "note": note}


WBT0101_IO = [
    io(1, "BT_APPLICATION", io_="IO", r="○", c="○", u="○", d="○",
       note="編集時に下書き／差し戻し申請を読込む。下書き保存で登録・更新、破棄で物理削除する"),
    io(2, "BT_PLANNED_COST", io_="IO", r="○", c="○", u="○", d="○",
       note="編集時に予定費用明細を読込む。下書き保存で登録・更新、破棄で物理削除する"),
    io(3, "BT_TRAVELER", io_="IO", r="○", c="○", u="○", d="○",
       note="編集時に出張者を読込む。下書き保存で登録・更新、破棄で物理削除する"),
    io(4, "BT_EMPLOYEE", io_="I", r="○", note="出張者（社員）情報を取得する"),
]
WBT0102_IO = [
    io(1, "BT_APPLICATION", io_="O", c="○", note="出張申請を新規登録する"),
    io(2, "BT_PLANNED_COST", io_="O", c="○", note="予定費用明細を新規登録する"),
    io(3, "BT_TRAVELER", io_="O", c="○", note="出張者を明細件数分新規登録する"),
    io(4, "BT_EMPLOYEE", io_="I", r="○", note="申請者・上長の情報を取得する"),
]
WBT0103_IO = [
    io(1, "-", io_="-", kind="-", note="該当なし"),
]


def evt(no, name, timing, summary, dest, comm):
    return {"no": no, "name": name, "timing": timing,
            "summary": summary, "dest": dest, "comm": comm}


WBT0101_EVT = [
    evt(1, "初期表示", "‐",
        "出張申請登録画面を表示する。新規時は出張者一覧にログインユーザを設定し予定費用明細を1行表示する。"
        "申請ID引継ぎ時は当該申請（'00'下書き／'31'差し戻し）を読み込んで編集モードで表示する。",
        "-", "あり(同期)"),
    evt(2, "確認／再申請", "「確認」／「再申請」ボタン押下",
        "入力内容のバリデーションを行い、出張申請登録確認画面を表示する。新規・'00'下書き編集時は「確認」、"
        "'31'差し戻し編集時は「再申請」ボタンとして活性化する（いずれも確認画面へ遷移）。",
        "出張申請登録確認", "あり(同期)"),
    evt(3, "下書き保存", "「下書き保存」ボタン押下",
        "必須未入力を許容して入力内容を下書き（APPL_STATUS='00'）として保存する。"
        "新規は申請IDを採番し、編集時は同一申請を版番号+1で更新する。",
        "-", "あり(同期)"),
    evt(4, "破棄／戻る", "「破棄」／「戻る」ボタン押下",
        "「破棄」押下時は下書き（APPL_STATUS='00'）を確認の上で物理削除して一覧へ戻る（'00'下書き編集時のみ活性化）。"
        "「戻る」押下時は入力内容を保存せず一覧へ戻る。",
        "出張申請一覧", "あり(同期)"),
    evt(5, "明細追加・削除", "「明細を追加」「削除」ボタン押下",
        "予定費用明細の入力行を追加、または指定行を削除する。",
        "-", "なし"),
]
WBT0102_EVT = [
    evt(1, "登録", "「登録」ボタン押下",
        "入力内容で出張申請を登録（差し戻しの場合は再申請）し、事前承認要否と承認者を判定して"
        "出張申請登録完了画面を表示する。",
        "出張申請登録完了", "あり(同期)"),
    evt(2, "戻る", "「戻る」ボタン押下",
        "出張申請登録画面に戻る。",
        "出張申請登録", "あり(同期)"),
]
WBT0103_EVT = [
    evt(1, "次へ", "「新規申請」ボタン押下",
        "出張申請登録画面を新規入力状態で表示する。",
        "出張申請登録", "あり(同期)"),
]

# ---- 2.6 画面イベント詳細（自由記述）----
WBT0101_DETAIL = [
    {"D": "2.6.1. 初期表示イベント"},
    {"E": "(1) 新規／編集モードの判定"},
    {"F": "・前画面から申請ID（application_id）を引き継いだ場合は編集モードとし、当該申請を"
          "BT_APPLICATION／BT_PLANNED_COST／BT_TRAVELERから読み込んで各画面項目に設定する。"},
    {"F": "・編集モードで扱えるのはappl_status='00'（下書き）または'31'（事前承認却下＝差し戻し）の申請に限る。"},
    {"F": "・申請IDを引き継がない場合は新規モードとし、出張者一覧にログインユーザ（申請者本人）、"
          "費用負担区分に「自社負担(01)」、予定費用明細を1行（費目は交通費(01)）を初期表示する。"},
    {"E": "(2) ボタン活性制御"},
    {"F": "・「下書き保存」は新規・編集いずれも活性化。「破棄」はappl_status='00'（下書き）の編集時のみ、"
          "「再申請」はappl_status='31'（差し戻し）の編集時のみ活性化する。"},
    {},
    {"D": "2.6.2. 確認／再申請イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "No.", "G": "バリデーション名", "M": "バリデーション内容", "W": "メッセージID", "AD": "後続判定"},
    {"F": 1, "G": "単項目必須",
     "M": "出張目的・出張開始日・出張終了日・費用負担区分が入力されていること。",
     "W": "MSG90001", "AD": "終了する"},
    {"F": 2, "G": "日付大小関係", "M": "出張開始日≦出張終了日であること。",
     "W": "MSG90002", "AD": "終了する"},
    {"F": 3, "G": "明細必須",
     "M": "予定費用明細が1件以上入力され、各明細の発生日・費目・予定金額が入力されていること。",
     "W": "MSG90003", "AD": "終了する"},
    {"F": "上記バリデーションで一箇所でもエラーが発生した場合、後続の処理は実施しない。"},
    {"E": "(2) 表示処理"},
    {"F": "入力内容（編集時は申請IDを含む）を出張申請登録確認画面（WBT0102）に引き継ぎ、確認画面を表示する。"},
    {},
    {"D": "2.6.3. 下書き保存イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "必須未入力を許容する（単項目必須・明細必須は検証しない）。入力済み項目の書式（日付形式・"
          "金額桁数）のみ検証し、エラー時はMSG90002等を表示して終了する。"},
    {"E": "(2) DBアクセス（下書き保存処理）"},
    {"F": "appl_status='00'として、BT_APPLICATION・BT_PLANNED_COST・BT_TRAVELERをUPSERTする。"
          "新規は【CC0004：申請ID採番】で申請IDを採番しversion_no=1でINSERT、編集時は同一申請IDを"
          "version_no+1でUPDATEする（明細は当該申請IDを全件DELETE後に再INSERT）。"
          "submitted_at・approver_id・approved_at・rejection_reason・finalized_atはNULLのままとする。"},
    {"E": "(3) 表示処理"},
    {"F": "MSG10006「下書きを保存しました。」を表示し、出張申請登録画面（WBT0101）を編集モードで再表示する。"},
    {},
    {"D": "2.6.4. 破棄イベント"},
    {"E": "(1) 確認処理"},
    {"F": "MSG10007「下書きを破棄します。よろしいですか？」を確認ダイアログで表示し、承認された場合のみ"
          "後続を実施する。破棄はappl_status='00'（下書き）の編集時のみ実施できる。"},
    {"E": "(2) DBアクセス（削除処理）"},
    {"F": "当該申請IDのBT_TRAVELER・BT_PLANNED_COST・BT_APPLICATIONを物理削除（DELETE）する。"},
    {"E": "(3) 表示処理"},
    {"F": "MSG10008「下書きを破棄しました。」を表示し、出張申請一覧画面へ遷移する。"},
]

# WBT0102 登録イベント詳細 = 事前承認要否判定の埋没ロジック（この設計書の核心）
WBT0102_DETAIL = [
    {"D": "2.6.1. 登録イベント"},
    {"E": "(1) バリデーション処理"},
    {"F": "本画面ではバリデーションを行わない（入力値の妥当性は確認イベント（WBT0101）で検証済みのため）。"},
    {},
    {"E": "(2) 申請区分の判定"},
    {"F": "(1) 申請IDを引き継がない、または引き継いだ申請のappl_status='00'（下書き）の場合は新規申請とする。"},
    {"F": "(2) 引き継いだ申請のappl_status='31'（事前承認却下＝差し戻し）の場合は再申請とし、"
          "appl_statusを'10'（申請済）に戻したうえでrejection_reasonをNULLでクリアし、"
          "以降の事前承認要否判定を再実行する。"},
    {},
    {"E": "(3) 申請状態設定処理（事前承認要否判定）"},
    {"F": "(1) 予定費用明細のplanned_amountを合計し、合計≧100000ならappl_statusに'20'をセットする。"},
    {"F": "(2) 申請者のposition_code='99'ならappl_statusに'20'をセットする。"},
    {"F": "(3) cost_bearing='02'ならappl_statusに'20'をセットする。"},
    {"F": "(4) 上記(1)〜(3)のいずれにも該当しない場合、appl_statusに'21'をセットする。"},
    {},
    {"E": "(4) 承認者設定処理"},
    {"F": "(1) approver_idは申請者の上長（BT_EMPLOYEE.manager_id）とする。"},
    {"F": "(2) 申請者のmanager_idがNULLの場合、申請者の所属部門（BT_EMPLOYEE.department_code）の"
          "部門長（BT_DEPARTMENT.manager_employee_id）をapprover_idとする。"},
    {"F": "(3) 上記いずれもNULLの場合、MSGE0004「承認者を決定できません。」を表示し処理を終了する（承認者未決定）。"},
    {},
    {"E": "(5) DBアクセス（登録処理）"},
    {"F": "新規申請は【CC0004：申請ID採番】でapplication_idを採番しversion_no=1でBT_APPLICATION／"
          "BT_PLANNED_COST／BT_TRAVELERへINSERTする。再申請・下書きからの申請は同一申請IDをversion_no+1で"
          "UPDATEする（明細は当該申請IDを全件DELETE後に再INSERT、line_noは1からの連番）。"
          "applicant_id・purpose・start_date・end_date・cost_bearingは画面値、appl_statusは(3)、"
          "approver_idは(4)、submitted_atはシステム日時、approved_at・finalized_atはNULLを設定する。"},
    {},
    {"E": "(6) メール送信処理"},
    {"F": "appl_statusが'20'（事前承認待ち）の場合、事前承認依頼メール（MBT01）を(4)で決定した"
          "承認者（approver_id）へ送信する。"},
    {},
    {"E": "(7) 表示処理"},
    {"F": "登録完了後、申請IDを引き継いで出張申請登録完了画面（WBT0103）を表示する。"},
]

WBT0103_DETAIL = [
    {"D": "2.6.1. 次へイベント"},
    {"E": "(1) 表示処理"},
    {"F": "出張申請登録画面（WBT0101）を新規入力状態で表示する。引き継ぎ項目はクリアする。"},
]


def hand(no, name, store, value, desc, note="-"):
    return {"no": no, "name": name, "store": store, "value": value, "desc": desc, "note": note}


SCREENS = [
    {
        "title": "2. WBT0101(出張申請登録画面)",
        "b5": "2. WBT0101(出張申請登録画面)",
        "area": "領域名：出張申請入力",
        "items": WBT0101_ITEMS,
        "io": WBT0101_IO,
        "events": WBT0101_EVT,
        "detail": WBT0101_DETAIL,
        "hand_event": "（1） 確認／再申請イベント",
        "hand_group": "項目グループ：出張申請登録",
        "hand_prefix": "プレフィックス：BTS01",
        "hand_items": [
            hand(1, "出張申請入力内容一式", "リクエストスコープ", "‐",
                 "出張目的・出張期間・費用負担区分・出張者一覧・予定費用明細を一括して確認画面へ引き継ぐ。",
                 "入力画面の全項目をまとめて引き継ぐ"),
        ],
    },
    {
        "title": "3. WBT0102(出張申請登録確認画面)",
        "b5": "3. WBT0102(出張申請登録確認画面)",
        "area": "領域名：出張申請確認",
        "items": WBT0102_ITEMS,
        "io": WBT0102_IO,
        "events": WBT0102_EVT,
        "detail": WBT0102_DETAIL,
        "hand_event": "（1） 登録イベント",
        "hand_group": "項目グループ：出張申請登録",
        "hand_prefix": "プレフィックス：BTS01",
        "hand_items": [
            hand(1, "申請ID", "リクエストスコープ", "採番したapplication_id",
                 "登録した出張申請の申請ID。完了画面で表示する。"),
            hand(2, "出張申請入力内容一式", "リクエストスコープ", "‐",
                 "出張目的・出張期間・費用負担区分・出張者一覧・予定費用明細を一括して完了画面へ引き継ぐ。"),
        ],
    },
    {
        "title": "4. WBT0103(出張申請登録完了画面)",
        "b5": "4. WBT0103(出張申請登録完了画面)",
        "area": "領域名：登録結果",
        "items": WBT0103_ITEMS,
        "io": WBT0103_IO,
        "events": WBT0103_EVT,
        "detail": WBT0103_DETAIL,
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
