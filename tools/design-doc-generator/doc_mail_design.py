"""メール設計書 — 出張申請システムの通知メール（MBT01〜MBT03）。

出張申請の事前承認・却下・最終承認の各契機で送信する通知メールを1メール1シートで定義する。
Nablarch開発標準のメール設計書テンプレートは空の状態で埋め込み文字列の明細行を1行しか
持たないため、メールごとの埋め込み文字列件数に合わせて明細行を追加し、電子署名以降の
固定セクション（電子署名・添付ファイル・メールヘッダ）を下方へずらして記入する。

本設計書は従来SIの記述をそのまま写す。件名・本文の可変部は位置指定プレースホルダ（{0}）で
表し、埋め込み文字列定義でプレースホルダ番号（物理名）と編集仕様・取得元を対応づける。
事前承認要否や精算額の判定根拠（Why）は本書には現れず、共通コンポーネント側に埋没している。
"""
from __future__ import annotations

from copy import copy

from common import open_template, fill_history, put, save, _anchor_coord, set_print_area

TEMPLATE = "メール設計書.xlsx"
OUTPUT = "メール設計書_BT_出張申請.xlsx"
PRODUCT = "メール設計書"

BASE_SHEET = "1.  メール名 ( メールID )"  # 複製元のメール定義シート

# ---- メール定義シートの固定セル位置（空テンプレで確認） ----
CELL_TITLE = "B5"        # 「1. メール名(メールID)」見出し
CELL_OVERVIEW = "H7"     # メール概要
CELL_SUBJECT = "H8"      # 件名・内容
CELL_SUBJECT_ENC = "H9"  # 件名・文字コード
CELL_FROM = "H10"
CELL_REPLYTO = "H11"
CELL_TO = "H12"
CELL_CC = "H13"
CELL_BCC = "H14"
CELL_BODY_ENC = "H15"    # 本文・文字コード
CELL_FORMAT = "H16"      # メール形式
CELL_BODY = "C18"        # 本文（C18:AH50 の結合セル）
CELL_TMPL_ID = "H53"     # メールテンプレートID
CELL_TMPL_NAME = "H54"   # メールテンプレート名

EMBED_HEADER_ROW = 56    # 埋め込み文字列の見出し行（項目名/物理名/…）
EMBED_START_ROW = 57     # 埋め込み文字列の明細開始行（空テンプレは1行のみ）
EMBED_COL = {"C": "name", "H": "phys", "M": "width", "P": "edit", "AC": "note"}

# 電子署名以降の固定セクション（空テンプレ上の行番号を基準に、埋め込み件数に応じて下方へずらす）
BOTTOM_BASE = 59         # 電子署名 の行（埋め込みが1件のときの位置）
BOTTOM_BLOCK = [
    # (元行, ラベル列, ラベル, 値列, 値)  値列が None ならラベルのみ
    (59, "C", "電子署名", "H", "不要"),
    (60, "C", "添付ファイル", "H", "なし"),
    (61, "C", "添付ファイル概要", "H", "-"),
    (62, "C", "添付ファイル種類", "H", "-"),
    (63, "C", "添付ファイルの作成仕様", "H", "-"),
    (65, "C", "メールヘッダ", None, None),
    (66, "C", "ヘッダ名", "H", "内容"),
    (67, "C", "-", "H", "-"),
]


# ------------------------------------------------------------------
# 行スタイル複製（doc_func_screen と同方針。単一行結合のみ写す）
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
    ws[_anchor_coord(ws, coord)] = None


def clear_row(ws, row: int, cols):
    for col in cols:
        put_none(ws, f"{col}{row}")


# ------------------------------------------------------------------
# メール定義データ
# ------------------------------------------------------------------
def embed(name, phys, width, edit, note="-"):
    return {"name": name, "phys": phys, "width": width, "edit": edit, "note": note}


MBT01 = {
    "id": "MBT01",
    "name": "事前承認依頼メール",
    "overview": (
        "事前承認要否判定により事前承認が必要と判定された出張申請について、"
        "申請者の上長に対して事前承認を依頼する通知メール。出張申請登録時に送信する。"
    ),
    "subject": "【出張申請】事前承認のお願い（{0}）",
    "from": "出張旅費システム送信専用メールアドレス",
    "reply_to": "-",
    "to": "申請者の上長のメールアドレス（BT_EMPLOYEE.manager_id が指す社員のメールアドレス）",
    "cc": "-",
    "bcc": "-",
    "tmpl_id": "TBT01",
    "tmpl_name": "事前承認依頼テンプレート",
    "body": (
        "{1} 様\n\n"
        "以下の出張申請について、事前承認が必要となりました。\n"
        "内容をご確認のうえ、事前承認をお願いいたします。\n\n"
        "■申請ID\n{0}\n\n"
        "■申請者\n{1}\n\n"
        "■出張目的\n{2}\n\n"
        "■予定費用合計\n{3} 円\n\n"
        "■事前承認が必要となった理由\n{4}\n\n"
        "本メールは出張旅費システムより自動送信しています。"
    ),
    "embeds": [
        embed("申請ID", "{0}", 16, "半角英数字16桁", "BT_APPLICATION.application_id"),
        embed("申請者氏名", "{1}", 50, "全角氏名。敬称は付与しない",
              "BT_EMPLOYEE.employee_name（applicant_id で取得）"),
        embed("出張目的", "{2}", 500, "全角500文字以内", "BT_APPLICATION.purpose"),
        embed("予定費用合計", "{3}", 10, "3桁カンマ区切り",
              "BT_PLANNED_COST.planned_amount の申請単位合計"),
        embed("事前承認理由", "{4}", 100,
              "事前承認が必要と判定された理由（予定費用合計10万円以上／役職なし／先方負担）を出力する。",
              "共通コンポーネントCC0001の判定結果より設定"),
    ],
}

MBT02 = {
    "id": "MBT02",
    "name": "事前承認却下通知メール",
    "overview": (
        "上長が出張申請の事前承認を却下した場合に、申請者に対して却下と却下理由を"
        "通知する通知メール。事前承認画面での却下時に送信する。"
    ),
    "subject": "【出張申請】事前承認却下のお知らせ（{0}）",
    "from": "出張旅費システム送信専用メールアドレス",
    "reply_to": "-",
    "to": "申請者のメールアドレス（BT_APPLICATION.applicant_id が指す社員のメールアドレス）",
    "cc": "-",
    "bcc": "-",
    "tmpl_id": "TBT02",
    "tmpl_name": "事前承認却下通知テンプレート",
    "body": (
        "{1} 様\n\n"
        "以下の出張申請について、事前承認が却下されました。\n"
        "却下理由をご確認のうえ、内容を見直して再申請してください。\n\n"
        "■申請ID\n{0}\n\n"
        "■却下理由\n{2}\n\n"
        "本メールは出張旅費システムより自動送信しています。"
    ),
    "embeds": [
        embed("申請ID", "{0}", 16, "半角英数字16桁", "BT_APPLICATION.application_id"),
        embed("申請者氏名", "{1}", 50, "全角氏名。敬称は付与しない",
              "BT_EMPLOYEE.employee_name（applicant_id で取得）"),
        embed("却下理由", "{2}", 500, "全角500文字以内", "BT_APPLICATION.rejection_reason"),
    ],
}

MBT03 = {
    "id": "MBT03",
    "name": "最終承認依頼メール",
    "overview": (
        "出張実績の登録が完了した出張申請について、申請者の上長に対して最終承認を"
        "依頼する通知メール。出張実績登録の完了時に送信する。"
    ),
    "subject": "【出張申請】最終承認のお願い（{0}）",
    "from": "出張旅費システム送信専用メールアドレス",
    "reply_to": "-",
    "to": "申請者の上長のメールアドレス（BT_EMPLOYEE.manager_id が指す社員のメールアドレス）",
    "cc": "-",
    "bcc": "-",
    "tmpl_id": "TBT03",
    "tmpl_name": "最終承認依頼テンプレート",
    "body": (
        "{1} 様\n\n"
        "以下の出張申請について、出張実績の登録が完了しました。\n"
        "内容をご確認のうえ、最終承認をお願いいたします。\n\n"
        "■申請ID\n{0}\n\n"
        "■申請者\n{1}\n\n"
        "■出張目的\n{2}\n\n"
        "■実績費用合計\n{3} 円\n\n"
        "本メールは出張旅費システムより自動送信しています。"
    ),
    "embeds": [
        embed("申請ID", "{0}", 16, "半角英数字16桁", "BT_APPLICATION.application_id"),
        embed("申請者氏名", "{1}", 50, "全角氏名。敬称は付与しない",
              "BT_EMPLOYEE.employee_name（applicant_id で取得）"),
        embed("出張目的", "{2}", 500, "全角500文字以内", "BT_APPLICATION.purpose"),
        embed("実績費用合計", "{3}", 10, "3桁カンマ区切り",
              "BT_ACTUAL_COST.actual_amount の申請単位合計"),
    ],
}

MAILS = [MBT01, MBT02, MBT03]


# ------------------------------------------------------------------
# 記入
# ------------------------------------------------------------------
def fill_mail(ws, no: int, mail: dict):
    title = f"{no}. {mail['name']}({mail['id']})"
    put(ws, CELL_TITLE, title)
    put(ws, CELL_OVERVIEW, mail["overview"])
    put(ws, CELL_SUBJECT, mail["subject"])
    put(ws, CELL_SUBJECT_ENC, "UTF-8")
    put(ws, CELL_FROM, mail["from"])
    put(ws, CELL_REPLYTO, mail["reply_to"])
    put(ws, CELL_TO, mail["to"])
    put(ws, CELL_CC, mail["cc"])
    put(ws, CELL_BCC, mail["bcc"])
    put(ws, CELL_BODY_ENC, "UTF-8")
    put(ws, CELL_FORMAT, "TEXT")
    put(ws, CELL_BODY, mail["body"])
    put(ws, CELL_TMPL_ID, mail["tmpl_id"])
    put(ws, CELL_TMPL_NAME, mail["tmpl_name"])

    embeds = mail["embeds"]
    n = len(embeds)
    offset = n - 1  # 電子署名以降の固定セクションを下方へずらす行数

    # (1) 先に電子署名以降のブロックを複製して下方へ退避する。
    #     元行（59〜）が埋め込み明細に上書きされる前に、原本の書式を読んで複製する。
    #     元行 < 複製先 なので、元行の大きい方から処理すれば読取り前の上書きは起きない。
    if offset > 0:
        for orig, lcol, label, vcol, val in sorted(BOTTOM_BLOCK, key=lambda x: -x[0]):
            clone_row_style(ws, orig, orig + offset)
            clear_row(ws, orig, ["C", "H", "M", "P", "AC"])
    # (2) 退避後の行にラベル・値を記入する。
    for orig, lcol, label, vcol, val in BOTTOM_BLOCK:
        dst = orig + offset
        put(ws, f"{lcol}{dst}", label)
        if vcol is not None:
            put(ws, f"{vcol}{dst}", val)

    # (3) 埋め込み文字列明細（EMBED_START_ROW からn行。2行目以降は明細行の書式を複製する）。
    #     元の電子署名等の行（59〜）に食い込む場合も、(1)で退避済みなので上書きしてよい。
    for i, rec in enumerate(embeds):
        r = EMBED_START_ROW + i
        if i > 0:
            clone_row_style(ws, EMBED_START_ROW, r)
        for col, key in EMBED_COL.items():
            put(ws, f"{col}{r}", rec[key])

    # (4) 最終明細と電子署名の間に残る区切り行を掃除する。
    sep = EMBED_START_ROW + n
    clear_row(ws, sep, ["C", "H", "M", "P", "AC"])


def fill_toc(wb):
    toc = wb["目次"]
    for i, mail in enumerate(MAILS):
        put(toc, f"B{7 + i}", f"{i + 1}. {mail['name']}({mail['id']})")


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    base = wb[BASE_SHEET]
    sheets = [base]
    for _ in range(len(MAILS) - 1):
        sheets.append(wb.copy_worksheet(base))
    for i, (ws, mail) in enumerate(zip(sheets, MAILS), start=1):
        ws.title = f"{i}. {mail['name']}({mail['id']})"
        fill_mail(ws, i, mail)

    order = ["表紙", "変更履歴", "目次"] + [ws.title for ws in sheets]
    wb._sheets.sort(key=lambda s: order.index(s.title))

    # 複製で print_area が消えた／内容がはみ出したメール定義シートを内容全体に張り直す。印刷右端は AI(35)。
    for ws in sheets:
        set_print_area(ws, right_col=35)

    fill_toc(wb)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
