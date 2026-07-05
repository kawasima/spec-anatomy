"""リクエスト一覧 — 出張申請システムの画面リクエスト（イベント）一覧。

各画面取引を、画面が受け付けるリクエスト（初期表示・確認・登録・承認・却下など）
単位に分解して並べる。before ではリクエスト名が「画面名：イベント名」の機械的な
命名に留まり、登録処理や承認処理の中に埋没した業務判定（事前承認要否・精算額計算）は
この一覧からは見えない。バッチ取引（BTB01）は画面リクエストを持たないため対象外。
"""
from __future__ import annotations

from common import open_template, fill_header, fill_table, save

TEMPLATE = "リクエスト一覧.xlsx"
OUTPUT = "リクエスト一覧.xlsx"

# 機能ごとのリクエスト（イベント）。リクエストID = R + 機能ID + 2桁通番。
FUNCTIONS = [
    {
        "func_id": "BTS01",
        "func_name": "出張申請登録",
        "requests": [
            ("初期表示", "出張申請登録画面の初期表示を行う。"),
            ("確認処理", "入力内容の確認処理を行い、事前承認要否を判定する。"),
            ("戻る", "確認画面から入力画面へ戻る。"),
            ("登録処理", "出張申請を登録する。事前承認が必要な場合は上長へ"
             "事前承認依頼メールを送信する。"),
            ("下書き保存処理", "入力中の出張申請を'00'下書きとして保存する。"
             "新規・更新のいずれも同一処理で行う。"),
            ("破棄処理", "'00'下書きの出張申請を削除する。"),
            ("再申請処理", "'31'事前承認却下の申請を修正し、'10'申請済として"
             "再提出する。事前承認要否を再判定する。"),
        ],
    },
    {
        "func_id": "BTS02",
        "func_name": "事前承認",
        "requests": [
            ("初期表示", "出張申請事前承認画面の初期表示を行う。"),
            ("承認処理", "対象申請の事前承認を行う。"),
            ("却下処理", "対象申請の事前承認を却下し、申請者へ却下通知メールを"
             "送信する。"),
        ],
    },
    {
        "func_id": "BTS03",
        "func_name": "出張実績登録",
        "requests": [
            ("初期表示", "出張実績登録画面の初期表示を行う。"),
            ("確認処理", "入力内容の確認処理を行う。"),
            ("戻る", "確認画面から入力画面へ戻る。"),
            ("登録処理", "出張実績を登録し、上長へ最終承認依頼メールを送信する。"),
        ],
    },
    {
        "func_id": "BTS04",
        "func_name": "最終承認",
        "requests": [
            ("初期表示", "出張申請最終承認画面の初期表示を行う。"),
            ("承認処理", "対象申請の最終承認を行い、精算額を確定する。"),
            ("却下処理", "対象申請の最終承認を却下する。"),
        ],
    },
    {
        "func_id": "BTS05",
        "func_name": "出張申請一覧",
        "requests": [
            ("初期表示", "出張申請一覧画面の初期表示を行う。"),
            ("検索処理", "検索条件で出張申請を検索する。"),
            ("取消処理", "最終承認前（'10'〜'40'）の出張申請を取り消し、"
             "appl_statusを'90'（取消済）に更新してcancelled_atを設定する。"),
        ],
    },
]

# sheet '1' の列マップ（空テンプレートで確認。ヘッダ行=7, データ開始行=8）
COLMAP = {
    "C": "no",
    "D": "func_id",
    "G": "func_name",
    "L": "req_id",
    "O": "req_name",
    "V": "desc",
}
START_ROW = 8


def build_records() -> list[dict]:
    records: list[dict] = []
    no = 1
    for f in FUNCTIONS:
        for j, (event, desc) in enumerate(f["requests"]):
            rec = {
                "no": no,
                "req_id": f"R{f['func_id']}{j + 1:02d}",
                "req_name": f"{f['func_name']}：{event}",
                "desc": desc,
            }
            # 機能ID・機能名は各機能グループの先頭行にだけ記入する（縦結合）。
            if j == 0:
                rec["func_id"] = f["func_id"]
                rec["func_name"] = f["func_name"]
            records.append(rec)
            no += 1
    return records


def build() -> str:
    wb = open_template(TEMPLATE)
    # ヘッダは 変更履歴 シートに書き、他シートは INDIRECT 参照で解決される。
    fill_header(wb["変更履歴"], product_name="リクエスト一覧")
    fill_table(wb["1"], START_ROW, COLMAP, build_records())
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
