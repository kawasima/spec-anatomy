"""テーブル定義書 — 出張申請システムの物理データモデル。

従来SIの設計をそのまま写す。申請のライフサイクルは appl_status(申請状態8コード)という
1カラムで持ち、承認者・承認日時・却下理由・最終承認日時はすべてNULL許容カラムとして
BT_APPLICATIONにぶら下げる。afterのspec-modelでは appl_status が型のOR分割になり、
NULL許容の4カラムは各状態が持つ固有データに分かれるが、ここではその区別は現れない。
"""
from __future__ import annotations

import datetime as _dt

from common import PROJECT, open_template, fill_header, put, save, set_print_area

TEMPLATE = "テーブル定義書.xlsx"
OUTPUT = "テーブル定義書.xlsx"
PRODUCT = "テーブル定義書"

# 表側テンプレシート（複製元）とヘッダ位置
BASE_SHEET = "論理テーブル名"
LOGICAL_NAME_CELL = "F5"   # 論理テーブル名 値
PHYSICAL_NAME_CELL = "W5"  # 物理テーブル名 値
DESC_CELL = "F6"           # テーブル説明 値
COL_START_ROW = 11         # カラム明細の開始行（見出しは8〜10行目）

# カラム明細の列マップ。INDEXは index dict（{列文字: '順序\n方向'}）で個別に持つ。
COL = {
    "no": "A",
    "logical": "B",
    "physical": "G",
    "domain": "L",
    "dtype": "Q",
    "length": "T",
    "pk": "V",
    "required": "W",
    "itemdef": "AE",
    "default": "AO",
    "note": "AS",
}


def _col(no, logical, physical, domain, dtype, length, pk=None, required="○",
         itemdef=None, default=None, index=None, note=None):
    return {
        "no": no, "logical": logical, "physical": physical, "domain": domain,
        "dtype": dtype, "length": length, "pk": pk, "required": required,
        "itemdef": itemdef, "default": default, "index": index or {}, "note": note,
    }


TABLES = [
    {
        "logical": "出張申請",
        "physical": "BT_APPLICATION",
        "desc": "出張申請1件の申請内容・状態・承認情報を保持する。申請の状態は申請状態(APPL_STATUS)で表し、承認・却下に伴う項目はNULL許容カラムで保持する。",
        "columns": [
            _col(1, "申請ID", "APPLICATION_ID", "申請ID", "NCHAR", 16, pk=1,
                 itemdef="申請を一意に識別するキー。共通コンポーネントCC0004(申請ID採番)で採番する。"),
            _col(2, "申請者社員ID", "APPLICANT_ID", "社員番号", "NCHAR", 10,
                 itemdef="申請者の社員ID。BT_EMPLOYEE.EMPLOYEE_IDを参照する。",
                 index={"X": "1\nA"}),
            _col(3, "出張目的", "PURPOSE", "出張目的", "NVARCHAR2", 500,
                 itemdef="出張の目的。"),
            _col(4, "出張開始日", "START_DATE", "日付", "NCHAR", 8,
                 itemdef="出張の開始日(YYYYMMDD)。"),
            _col(5, "出張終了日", "END_DATE", "日付", "NCHAR", 8,
                 itemdef="出張の終了日(YYYYMMDD)。"),
            _col(6, "費用負担区分", "COST_BEARING", "費用負担区分", "NCHAR", 2,
                 itemdef="費用負担区分(01:自社負担 / 02:先方負担)。コードC0020001を参照する。"),
            _col(7, "申請状態", "APPL_STATUS", "申請状態", "NCHAR", 2, default="00",
                 itemdef="申請状態(00:下書き / 10:申請済 / 20:事前承認待ち / 21:事前承認不要 / 30:事前承認済 / 31:事前承認却下 / 40:実績登録済 / 50:最終承認済)。コードC0030001を参照する。画面遷移・登録処理で本カラムを更新する。"),
            _col(8, "申請日時", "SUBMITTED_AT", "日時", "TIMESTAMP", 0, required="×",
                 itemdef="申請を提出した日時。下書き状態ではNULL。"),
            _col(9, "承認者社員ID", "APPROVER_ID", "社員番号", "NCHAR", 10, required="×",
                 itemdef="事前承認・最終承認を行う上長の社員ID。承認前はNULL。BT_EMPLOYEE.EMPLOYEE_IDを参照する。",
                 index={"Y": "1\nA"}),
            _col(10, "事前承認日時", "APPROVED_AT", "日時", "TIMESTAMP", 0, required="×",
                 itemdef="事前承認された日時。事前承認前・事前承認不要の場合はNULL。"),
            _col(11, "却下理由", "REJECTION_REASON", "却下理由", "NVARCHAR2", 500, required="×",
                 itemdef="事前承認が却下された場合の理由。却下されていない場合はNULL。"),
            _col(12, "最終承認日時", "FINALIZED_AT", "日時", "TIMESTAMP", 0, required="×",
                 itemdef="最終承認された日時。最終承認前はNULL。"),
            _col(13, "取消日時", "CANCELLED_AT", "日時", "TIMESTAMP", 0, required="×",
                 itemdef="申請が取り消された日時。取消済(90)の場合に記録する。取り消されていない場合はNULL。"),
            _col(14, "版番号", "VERSION_NO", "版番号", "NUMBER", 4, default=1,
                 itemdef="排他制御(楽観ロック)に用いる版番号。"),
        ],
    },
    {
        "logical": "出張予定費用",
        "physical": "BT_PLANNED_COST",
        "desc": "出張申請の予定費用を明細単位で保持する。事前承認要否の判定に用いる予定費用合計はこの明細の合計から算出する。",
        "columns": [
            _col(1, "申請ID", "APPLICATION_ID", "申請ID", "NCHAR", 16, pk=1,
                 itemdef="出張申請の申請ID。BT_APPLICATION.APPLICATION_IDを参照する。"),
            _col(2, "明細番号", "LINE_NO", "明細番号", "NUMBER", 3, pk=2,
                 itemdef="申請内で予定費用明細を一意にする連番。"),
            _col(3, "発生日", "EXPENSE_DATE", "日付", "NCHAR", 8,
                 itemdef="費用が発生する予定日(YYYYMMDD)。"),
            _col(4, "費目", "CATEGORY", "費目", "NCHAR", 2,
                 itemdef="費目(01:交通費 / 02:宿泊費 / 03:交際費)。コードC0010001を参照する。"),
            _col(5, "予定金額", "PLANNED_AMOUNT", "金額", "NUMBER", 9,
                 itemdef="当該明細の予定金額(円)。"),
        ],
    },
    {
        "logical": "出張実績費用",
        "physical": "BT_ACTUAL_COST",
        "desc": "出張後に登録する実績費用を明細単位で保持する。精算額計算・経理連携はこの実績費用を用いる。",
        "columns": [
            _col(1, "申請ID", "APPLICATION_ID", "申請ID", "NCHAR", 16, pk=1,
                 itemdef="出張申請の申請ID。BT_APPLICATION.APPLICATION_IDを参照する。"),
            _col(2, "明細番号", "LINE_NO", "明細番号", "NUMBER", 3, pk=2,
                 itemdef="申請内で実績費用明細を一意にする連番。"),
            _col(3, "発生日", "EXPENSE_DATE", "日付", "NCHAR", 8,
                 itemdef="費用が発生した日(YYYYMMDD)。"),
            _col(4, "費目", "CATEGORY", "費目", "NCHAR", 2,
                 itemdef="費目(01:交通費 / 02:宿泊費 / 03:交際費)。コードC0010001を参照する。"),
            _col(5, "実績金額", "ACTUAL_AMOUNT", "金額", "NUMBER", 9,
                 itemdef="当該明細の実績金額(円)。"),
        ],
    },
    {
        "logical": "社員",
        "physical": "BT_EMPLOYEE",
        "desc": "申請者および承認者(上長)となる社員の情報を保持する。役職・上長は事前承認要否の判定に用いる。",
        "columns": [
            _col(1, "社員ID", "EMPLOYEE_ID", "社員番号", "NCHAR", 10, pk=1,
                 itemdef="社員を一意に識別するID。"),
            _col(2, "氏名", "EMPLOYEE_NAME", "氏名", "NVARCHAR2", 50,
                 itemdef="社員の氏名。"),
            _col(3, "役職", "POSITION_CODE", "役職", "NCHAR", 2,
                 itemdef="役職(10:一般社員 / 20:主任 / 30:課長 / 40:部長 / 99:役職なし)。コードC0040001を参照する。"),
            _col(4, "所属部門コード", "DEPARTMENT_CODE", "部門コード", "NCHAR", 30,
                 itemdef="社員が所属する部門のコード。BT_DEPARTMENT.DEPARTMENT_CODEを参照する。"),
            _col(5, "上長社員ID", "MANAGER_ID", "社員番号", "NCHAR", 10, required="×",
                 itemdef="上長の社員ID。事前承認・最終承認の承認者となる。上長が存在しない場合はNULL。BT_EMPLOYEE.EMPLOYEE_IDを参照する。",
                 index={"X": "1\nA"}),
        ],
    },
    {
        "logical": "部門",
        "physical": "BT_DEPARTMENT",
        "desc": "社員が所属する部門を保持するマスタ。帳票の所属部門表示および経理連携ファイルの部門コード出力に用いる。",
        "columns": [
            _col(1, "部門コード", "DEPARTMENT_CODE", "部門コード", "NCHAR", 30, pk=1,
                 itemdef="部門を一意に識別するコード。"),
            _col(2, "部門名", "DEPARTMENT_NAME", "部門名", "NVARCHAR2", 80,
                 itemdef="部門の名称。"),
            _col(3, "部門長社員ID", "MANAGER_EMPLOYEE_ID", "社員番号", "NCHAR", 10,
                 itemdef="部門長の社員ID。申請者の上長が未設定の場合、事前承認・最終承認の承認者を本部門長で代行する。BT_EMPLOYEE.EMPLOYEE_IDを参照する。"),
        ],
    },
    {
        "logical": "出張者",
        "physical": "BT_TRAVELER",
        "desc": "出張申請1件に対する出張者を明細単位で保持する。出張申請登録画面の出張者一覧で入力された複数出張者を永続化する。",
        "columns": [
            _col(1, "申請ID", "APPLICATION_ID", "申請ID", "NCHAR", 16, pk=1,
                 itemdef="出張申請の申請ID。BT_APPLICATION.APPLICATION_IDを参照する。"),
            _col(2, "明細番号", "LINE_NO", "明細番号", "NUMBER", 3, pk=2,
                 itemdef="申請内で出張者明細を一意にする連番。"),
            _col(3, "社員ID", "EMPLOYEE_ID", "社員番号", "NCHAR", 10,
                 itemdef="出張者の社員ID。BT_EMPLOYEE.EMPLOYEE_IDを参照する。"),
        ],
    },
]


def fill_book_header(wb):
    ch = wb["変更履歴"]
    put(ch, "E1", PROJECT["pj"])
    put(ch, "E2", PROJECT["system"])
    put(ch, "E3", PROJECT["subsystem"])
    put(ch, "S1", PRODUCT)
    y, m, d = (int(x) for x in PROJECT["created"].split("-"))
    put(ch, "A8", 1)
    put(ch, "B8", "1.0版")
    put(ch, "D8", _dt.datetime(y, m, d))
    put(ch, "G8", "新規")
    put(ch, "J8", "-")
    put(ch, "Q8", "(新規作成)")
    put(ch, "AF8", PROJECT["author"])
    y2, m2, d2 = (int(x) for x in PROJECT["changed"].split("-"))
    put(ch, "A9", 2)
    put(ch, "B9", "1.1版")
    put(ch, "D9", _dt.datetime(y2, m2, d2))
    put(ch, "G9", "修正")
    put(ch, "J9", "-")
    put(ch, "Q9", "(記載内容の修正)")
    put(ch, "AF9", PROJECT["author"])


def fill_table_sheet(ws, table):
    fill_header(ws, product_name=PRODUCT)
    put(ws, LOGICAL_NAME_CELL, table["logical"])
    put(ws, PHYSICAL_NAME_CELL, table["physical"])
    put(ws, DESC_CELL, table["desc"])
    for i, c in enumerate(table["columns"]):
        r = COL_START_ROW + i
        for key, letter in COL.items():
            v = c.get(key)
            if v is not None:
                put(ws, f"{letter}{r}", v)
        for letter, val in c.get("index", {}).items():
            put(ws, f"{letter}{r}", val)


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_book_header(wb)

    # 未記入のテンプレシートから先に必要枚数を複製し、そのあとで記入する
    # （記入済みシートを複製すると前テーブルの明細行が残ってしまうため）。
    base = wb[BASE_SHEET]
    sheets = [base]
    for _ in range(len(TABLES) - 1):
        sheets.append(wb.copy_worksheet(base))
    for idx, (ws, table) in enumerate(zip(sheets, TABLES)):
        ws.title = f"{idx + 1}. {table['logical']}"
        fill_table_sheet(ws, table)

    # シート順を 表紙,変更履歴,目次,[テーブル群],データ に整える
    order = ["表紙", "変更履歴", "目次"] + [s.title for s in sheets] + ["データ"]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    # 目次
    toc = wb["目次"]
    fill_header(toc, product_name=PRODUCT)
    for i, table in enumerate(TABLES):
        put(toc, f"B{7 + i}", f"{i + 1}. {table['logical']}")

    # 複製で print_area が消えたテーブルシートを内容全体に張り直す。印刷右端は AZ(52)。
    for ws in sheets:
        set_print_area(ws, right_col=52)

    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
