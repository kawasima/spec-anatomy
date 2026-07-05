"""外部インタフェース設計書（I／Fファイル） — IBT01 経理システム連携ファイル。

最終承認済の出張申請の立替精算額を、日次バッチ（BTB01 経理連携ファイル作成）で
固定長ファイルに出力し、経理システムへ連携する外部インタフェースの設計書。

従来SIの設計をそのまま写す。特に次の点は「直す」対象ではなく「そのまま書く」対象:

- レコード定義はテーブル駆動。各項目の備考に連携元の「テーブル.カラム」（物理名）を書く。
  業務概念の派生元（なぜこの値なのか）は現れない。
- 精算額は BT_ACTUAL_COST.actual_amount を申請単位で合計した値、としか書かない。
  自社負担／先方負担で精算額が変わる判定根拠（Why）はここには書かない。
- 状態や区分はコード値（費用負担区分＝コードC0020001）で持つ。

テンプレート（I／Fファイル書式）は次の構成:
  1. 外部インタフェース仕様 … I/Fの授受条件（入出力種別・相手先・媒体・データ形式ほか）
  2. レコード構成          … ヘッダ／明細／トレーラのレコード種別一覧
  3.x データレイアウト     … レコード種別ごとの項目定義（項目名・項目ID・ドメイン・
                              データ型・長さ・開始位置ほか）。開始位置は長さから自動計算。
"""
from __future__ import annotations

from common import open_template, fill_history, put, save, set_print_area

TEMPLATE = "外部インタフェース設計書_IBT01_経理システム連携ファイル.xlsx"
OUTPUT = "外部インタフェース設計書_IBT01_経理システム連携ファイル.xlsx"
PRODUCT = "外部インタフェース設計書（I／Fファイル）\n\nIBT01/経理システム連携ファイル"

RECORD_LEN = 100  # 固定長レコードのバイト長（全レコード種別共通）

SPEC_SHEET = "1. 外部インタフェース仕様"
STRUCT_SHEET = "2. レコード構成"
BASE_RECORD = "【レコード名】"  # 複製元のレコード定義シート


# ------------------------------------------------------------------
# 1. 外部インタフェース仕様
# ------------------------------------------------------------------
def fill_spec(ws):
    # 入出力種別 / 相手先
    put(ws, "E7", "出力")
    put(ws, "U7", "経理システム")
    # 入出力取引ID/名称 / ファイルID
    put(ws, "E8", "BTB01/経理連携ファイル作成")
    put(ws, "U8", "IBT01")
    # 目的・概要
    put(ws, "B10", "最終承認済の出張申請について、申請者が立て替えた精算額を経理システムへ")
    put(ws, "B11", "連携するためのインタフェースファイル。日次バッチ（BTB01 経理連携ファイル作成）で")
    put(ws, "B12", "1日分をまとめて固定長ファイルとして出力する。")
    # 作成条件
    put(ws, "B15", "処理サイクルに従い、当日に最終承認（APPL_STATUS='50'）となった出張申請を対象に作成する。")
    put(ws, "B16", "対象申請が0件の場合は、ヘッダレコードとトレーラレコードのみのファイルを作成する。")
    put(ws, "B17", "連携済の申請は再連携しない（連携済フラグにより二重連携を抑止する）。")
    # 媒体（ファイル） / データ形式（固定長）… （ ）内に選択値を記入する
    put(ws, "H19", "ファイル")
    put(ws, "AE19", "固定長")
    # 授受方式 / ﾌｨｰﾙﾄﾞｾﾊﾟﾚｰﾀ
    put(ws, "E21", "ファイル転送")
    put(ws, "U21", "-（固定長のため区切り文字なし）")
    # 暗号化（ ） / 改行コード（ ）
    put(ws, "H23", "無し")
    put(ws, "AB23", "CR+LF")
    # 文字コード / レコード長
    put(ws, "E24", "UTF-8")
    put(ws, "U24", RECORD_LEN)
    # 処理サイクル（ ）内に記入
    put(ws, "H25", "日次（毎営業日・夜間バッチ）")
    # 特記事項
    put(ws, "B29", "＜FILLERの扱い＞")
    put(ws, "B30", "各レコードの余剰領域（FILLER）は半角スペースで埋める。")
    put(ws, "B31", "数値項目は右詰め・前ゼロ埋め、文字項目は左詰め・後方スペース埋めとする。")


# ------------------------------------------------------------------
# 2. レコード構成
# ------------------------------------------------------------------
# 列: A=No / B=レコード名 / G=ﾚｺｰﾄﾞﾀｲﾌﾟ名 / J=識別方法 / Q=長さ(Byte)
#     S=繰り返し回数 / V=繰り返し単位 / AD=ソートKEY項目名 / AH=昇順/降順
STRUCT_COL = {"A": "no", "B": "name", "G": "type", "J": "ident", "Q": "len",
              "S": "repeat", "V": "unit", "AD": "sortkey", "AH": "order"}
STRUCT_START = 9   # データ行の開始（8行目が見出し）
STRUCT_END = 17    # テンプレに No.=1〜9 が印字済みの最終行

RECORDS_STRUCT = [
    {"no": 1, "name": "ヘッダレコード", "type": "Header",
     "ident": "レコード区分＝'1'", "len": RECORD_LEN, "repeat": 1,
     "unit": "ファイルの先頭に1件のみ", "sortkey": "レコード区分", "order": "昇"},
    {"no": 2, "name": "立替精算明細レコード", "type": "Detail",
     "ident": "レコード区分＝'2'", "len": RECORD_LEN, "repeat": "0～複数",
     "unit": "立替精算1件（出張申請1件）毎に1レコード", "sortkey": "申請ID", "order": "昇"},
    {"no": 3, "name": "トレーラレコード", "type": "Trailer",
     "ident": "レコード区分＝'9'", "len": RECORD_LEN, "repeat": 1,
     "unit": "ファイルの末尾に1件のみ", "sortkey": "-", "order": "-"},
]


def fill_struct(ws):
    for i, rec in enumerate(RECORDS_STRUCT):
        r = STRUCT_START + i
        for col, key in STRUCT_COL.items():
            put(ws, f"{col}{r}", rec.get(key))
    # テンプレに印字済みの余った No.（4〜9）を消す
    for r in range(STRUCT_START + len(RECORDS_STRUCT), STRUCT_END + 1):
        for col in STRUCT_COL:
            put_none(ws, f"{col}{r}")
    # レコード構成イメージ
    put(ws, "D21", "・立替精算データが1件以上ある場合")
    put(ws, "E22", "ヘッダレコード")
    put(ws, "E23", "立替精算明細レコード")
    put(ws, "E24", "（申請件数分の繰り返し）")
    put(ws, "E25", "トレーラレコード")
    put(ws, "O21", "・立替精算データが0件の場合")
    put(ws, "P22", "ヘッダレコード")
    put(ws, "P23", "トレーラレコード")


# ------------------------------------------------------------------
# 3.x データレイアウト（レコード定義）
# ------------------------------------------------------------------
# 列: A=No / B=項目名 / G=項目ID / L=ドメイン名 / Q=必須 / R=データ型 / V=長さ(Byte)
#     X=開始位置(テンプレ数式=V(前)+X(前)で自動計算・記入しない) / Z=ﾃﾞﾌｫﾙﾄ値
#     AB=ﾊﾟﾃﾞｨﾝｸﾞ / AD=小数点位置 / AF=ﾌｫｰﾏｯﾄ仕様 / AI=備考
ITEM_COL = {"A": "no", "B": "name", "G": "id", "L": "domain", "Q": "req",
            "R": "dtype", "V": "len", "Z": "default", "AB": "pad",
            "AD": "dot", "AF": "fmt", "AI": "note"}
ITEM_START = 8   # データ行の開始（7行目が見出し）
ITEM_END = 17    # テンプレに開始位置数式が入る最終行


def field(no, name, id_, domain, dtype, length, req="○", default="-",
          pad="-", dot="-", fmt="-", note="-"):
    return {"no": no, "name": name, "id": id_, "domain": domain, "req": req,
            "dtype": dtype, "len": length, "default": default, "pad": pad,
            "dot": dot, "fmt": fmt, "note": note}


HEADER_FIELDS = [
    field(1, "レコード区分", "recordKbn", "レコード区分", "半角数字", 1,
          default='"1"', note="ヘッダレコードを表す固定値"),
    field(2, "ファイルID", "fileId", "ファイルID", "半角英数字", 8,
          default='"IBT01"', note="当ファイルのID"),
    field(3, "作成日", "createDate", "年月日", "半角数字", 8,
          pad="0", fmt="YYYYMMDD", note="バッチ処理日（システム日付）"),
    field(4, "FILLER", "ex_filler", "-", "半角", 83, req="-", note="スペース埋め"),
]

DETAIL_FIELDS = [
    field(1, "レコード区分", "recordKbn", "レコード区分", "半角数字", 1,
          default='"2"', note="明細レコードを表す固定値"),
    field(2, "申請ID", "applicationId", "申請ID", "半角英数字", 16,
          note="BT_APPLICATION.application_id"),
    field(3, "申請者社員番号", "applicantEmployeeNo", "社員番号", "半角英数字", 10,
          note="BT_APPLICATION.applicant_id（＝BT_EMPLOYEE.employee_id）"),
    field(4, "精算額", "settlementAmount", "金額", "半角数字", 9,
          pad="0", note="BT_ACTUAL_COST.actual_amount を申請単位で合計した金額"),
    field(5, "費用負担区分", "costBearing", "費用負担区分", "半角", 2,
          note="BT_APPLICATION.cost_bearing（コードC0020001）"),
    field(6, "最終承認日", "finalApprovalDate", "年月日", "半角数字", 8,
          pad="0", fmt="YYYYMMDD", note="BT_APPLICATION.finalized_at の日付部"),
    field(7, "部門コード", "departmentCode", "部門コード", "半角英数字", 30,
          note="BT_EMPLOYEE.department_code（申請者の所属部門コード）"),
    field(8, "FILLER", "ex_filler", "-", "半角", 24, req="-", note="スペース埋め"),
]

TRAILER_FIELDS = [
    field(1, "レコード区分", "recordKbn", "レコード区分", "半角数字", 1,
          default='"9"', note="トレーラレコードを表す固定値"),
    field(2, "明細件数", "detailCount", "件数", "半角数字", 9,
          pad="0", note="ヘッダとトレーラを除く明細レコードの件数"),
    field(3, "精算額合計", "totalSettlementAmount", "金額", "半角数字", 11,
          pad="0", note="全明細の精算額（settlementAmount）の合計"),
    field(4, "FILLER", "ex_filler", "-", "半角", 79, req="-", note="スペース埋め"),
]


RECORD_SHEETS = [
    {"title": "3.1. ヘッダレコード", "a5": "3.1. ヘッダレコード", "fields": HEADER_FIELDS},
    {"title": "3.2. 立替精算明細レコード", "a5": "3.2. 立替精算明細レコード", "fields": DETAIL_FIELDS},
    {"title": "3.3. トレーラレコード", "a5": "3.3. トレーラレコード", "fields": TRAILER_FIELDS},
]


def fill_record(ws, sheet):
    put(ws, "A5", sheet["a5"])
    fields = sheet["fields"]
    for i, fld in enumerate(fields):
        r = ITEM_START + i
        for col, key in ITEM_COL.items():
            put(ws, f"{col}{r}", fld.get(key))
    # 余った行の No.・開始位置数式などを消す（未使用行の数式が0起点で表示されるのを防ぐ）
    for r in range(ITEM_START + len(fields), ITEM_END + 1):
        for col in list(ITEM_COL.keys()) + ["C", "X"]:
            put_none(ws, f"{col}{r}")


# ------------------------------------------------------------------
def put_none(ws, coord: str):
    from common import _anchor_coord
    ws[_anchor_coord(ws, coord)] = None


def fill_toc(wb):
    toc = wb["目次"]
    put(toc, "B7", "1. 外部インタフェース仕様")
    put(toc, "B9", "2. レコード構成")
    put(toc, "B11", "3. データレイアウト")
    for i, sh in enumerate(RECORD_SHEETS):
        put(toc, f"C{12 + i}", sh["a5"])


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    fill_spec(wb[SPEC_SHEET])
    fill_struct(wb[STRUCT_SHEET])

    # レコード定義シート: 複製元から必要枚数を複製してから記入する
    base = wb[BASE_RECORD]
    sheets = [base]
    for _ in range(len(RECORD_SHEETS) - 1):
        sheets.append(wb.copy_worksheet(base))
    for ws, sheet in zip(sheets, RECORD_SHEETS):
        ws.title = sheet["title"]
        fill_record(ws, sheet)

    # シート順を 表紙,変更履歴,目次,1.仕様,2.構成,[3.x],データ に整える
    order = ["表紙", "変更履歴", "目次", SPEC_SHEET, STRUCT_SHEET] + \
            [sh["title"] for sh in RECORD_SHEETS] + ["データ"]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    # 複製で print_area が消えたレコード定義シートを内容全体に張り直す。印刷右端は AO(41)。
    for ws in sheets:
        set_print_area(ws, right_col=41)

    fill_toc(wb)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
