"""ドメイン定義書 — 出張申請システムの横断的なデータモデル(ドメイン)定義。

Nablarch開発標準のドメイン定義書に、出張申請システムで用いる業務項目のドメインを
流し込む。ドメイン毎に、桁数・データ型と併せて標準提供のバリデーション処理名
（文字種・文字数・数値範囲・日付書式・コード値有効など）を対応づける。

after（spec-model）では「出張目的」「金額」「却下理由」などは値オブジェクトや型として
表現され、申請状態・費用負担・役職はコードでなく型のORになる。ここ（before）では
すべてが桁数とデータ型に潰れた「ドメイン」の列挙であり、コード各種はコードIDへの参照に
なっている。
"""
from __future__ import annotations

import datetime

from common import open_template, put, fill_table, save, set_print_area
from common import PROJECT

TEMPLATE = "ドメイン定義書.xlsx"
OUTPUT = "ドメイン定義書.xlsx"

DOMAIN_SHEET = "1. ドメイン定義"
START_ROW = 9

# 「1. ドメイン定義」シートの列マップ（記入見本・空テンプレで確認）。
# 桁数は最小=R / 最大=T / 小数部=V、コードはコードID=X / コードパターン=AA。
COLMAP = {
    "A": "no",
    "B": "logical",       # ドメイン名(論理)
    "G": "summary",       # ドメイン概要
    "O": "datatype",      # データ型
    "R": "len_min",       # 桁数(最小)
    "T": "len_max",       # 桁数(最大)
    "V": "decimals",      # 桁数(小数部)
    "X": "code_id",       # コードID
    "AA": "code_pattern", # コードパターン
    "AD": "other",        # その他の定義
    "AL": "validation",   # バリデーション処理名
    "AX": "physical",     # ドメイン名(物理)
    "BC": "charset",      # システム許容文字
    "BH": "annotation",   # 追加アノテーション
}

# バリデーション処理名は「2.1. Nablarch標準提供バリデーション」シートの処理名と一致させる。
V_ALNUM = "文字種バリデーション（半角英数字）"
V_ZENKAKU = "文字種バリデーション（全角文字）"
V_LEN_FIX = "文字数バリデーション（桁数固定）"
V_LEN_MAX = "文字数バリデーション（桁数可変、最大値のみ指定）"
V_NUM_DIGIT_NODEC = "数値桁数バリデーション（小数部未指定）"
V_NUM_MIN = "数値範囲バリデーション（最小値のみ指定）"
V_CODE = "コード値有効バリデーション"
V_DATE = "日付書式バリデーション"

DOMAINS = [
    {
        "logical": "申請ID", "summary": "出張申請を一意に識別するID。採番機能で採番する",
        "datatype": "半角英数字", "len_min": 16, "len_max": 16,
        "validation": f"{V_ALNUM}\n{V_LEN_FIX}",
        "physical": "applicationId", "charset": "半角英数字", "annotation": "@Id",
    },
    {
        "logical": "社員番号", "summary": "社員を一意に識別する番号",
        "datatype": "半角英数字", "len_min": 10, "len_max": 10,
        "validation": f"{V_ALNUM}\n{V_LEN_FIX}",
        "physical": "employeeId", "charset": "半角英数字",
    },
    {
        "logical": "氏名", "summary": "社員の氏名",
        "datatype": "全角文字", "len_min": 0, "len_max": 50,
        "validation": f"{V_ZENKAKU}\n{V_LEN_MAX}",
        "physical": "employeeName", "charset": "全角文字",
    },
    {
        "logical": "出張目的", "summary": "出張の目的",
        "datatype": "全角文字", "len_min": 0, "len_max": 500,
        "validation": f"{V_ZENKAKU}\n{V_LEN_MAX}",
        "physical": "purpose", "charset": "全角文字",
    },
    {
        "logical": "却下理由", "summary": "事前承認を却下した理由",
        "datatype": "全角文字", "len_min": 0, "len_max": 500,
        "validation": f"{V_ZENKAKU}\n{V_LEN_MAX}",
        "physical": "rejectionReason", "charset": "全角文字",
    },
    {
        "logical": "日付", "summary": "年月日（出張開始日・終了日・費用計上日）",
        "datatype": "日付", "other": "yyyyMMdd形式",
        "validation": V_DATE,
        "physical": "date", "annotation": '@DateFormat("yyyyMMdd")',
    },
    {
        "logical": "金額", "summary": "費用の金額（円）",
        "datatype": "数値（整数）", "len_max": 9, "other": "最小値 = 0",
        "validation": f"{V_NUM_DIGIT_NODEC}\n{V_NUM_MIN}",
        "physical": "amount", "charset": "数値（整数）",
        "annotation": "@NumberRange(min = 0)",
    },
    {
        "logical": "版番号", "summary": "楽観排他制御に用いる版番号",
        "datatype": "数値（整数）", "other": "最小値 = 1",
        "validation": V_NUM_MIN,
        "physical": "versionNo", "charset": "数値（整数）",
        "annotation": "@NumberRange(min = 1)",
    },
    {
        "logical": "費目", "summary": "費用の費目",
        "datatype": "コード", "code_id": "C0010001",
        "validation": V_CODE, "physical": "category", "charset": "半角英数字",
    },
    {
        "logical": "費用負担区分", "summary": "出張費用の負担元区分",
        "datatype": "コード", "code_id": "C0020001",
        "validation": V_CODE, "physical": "costBearing", "charset": "半角英数字",
    },
    {
        "logical": "申請状態", "summary": "出張申請の状態",
        "datatype": "コード", "code_id": "C0030001",
        "validation": V_CODE, "physical": "applStatus", "charset": "半角英数字",
    },
    {
        "logical": "役職", "summary": "社員の役職",
        "datatype": "コード", "code_id": "C0040001",
        "validation": V_CODE, "physical": "positionCode", "charset": "半角英数字",
    },
]


def _d(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


def fill_history(wb, product_name: str):
    """変更履歴シートにプロジェクト識別と変更履歴を記入する。

    各コンテンツシートの1〜3行目ヘッダ（PJ名・作成・変更 等）は
    変更履歴シートの値をINDIRECTで参照する数式になっている。従って値の
    書き込み先は変更履歴シートであり、作成／変更の会社・日付は変更履歴の
    表本体（担当者AF・変更日D）から算出される。
    """
    ws = wb["変更履歴"]
    put(ws, "E1", PROJECT["pj"])
    put(ws, "E2", PROJECT["system"])
    put(ws, "E3", PROJECT["subsystem"])
    put(ws, "S1", product_name)
    # 変更履歴の表本体（No.=A / 版数=B / 変更日=D / 区分=G / 変更項目=J / 変更内容=Q / 担当者=AF）
    put(ws, "A8", 1)
    put(ws, "B8", "1.0版")
    put(ws, "D8", _d(PROJECT["created"]))
    put(ws, "G8", "新規")
    put(ws, "J8", "-")
    put(ws, "Q8", "(新規作成)")
    put(ws, "AF8", PROJECT["author"])
    put(ws, "A9", 2)
    put(ws, "B9", "1.1版")
    put(ws, "D9", _d(PROJECT["changed"]))
    put(ws, "G9", "変更")
    put(ws, "J9", "1. ドメイン定義")
    put(ws, "Q9", "・出張申請システムのドメインを追加")
    put(ws, "AF9", PROJECT["author"])


def build_records() -> list[dict]:
    records: list[dict] = []
    for i, d in enumerate(DOMAINS):
        rec = dict(d)
        rec["no"] = i + 1
        records.append(rec)
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, "ドメイン定義書")
    ws = wb[DOMAIN_SHEET]
    fill_table(ws, START_ROW, COLMAP, build_records())
    # ドメイン件数が既定印刷範囲の行数を超えるため、内容全体に張り直す。
    # 印刷右端は AI(35)（AL/AX/BH のバリデーション・物理名・アノテーションは内部設計情報で印刷範囲外）。
    set_print_area(ws, right_col=35)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
