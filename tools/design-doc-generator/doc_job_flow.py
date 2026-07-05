"""ネット・ジョブフロー — 出張申請サブシステム（BT）のバッチ運用フロー。

本ブックはジョブネットとジョブの起動順序を図形（ジョブネット枠・ジョブ枠・矢印）で
描画する成果物である。openpyxl は図形を保持できないため、ここではテキストの
表領域（スケジュール条件・ジョブネットID/名・ジョブ（バッチ処理ID/名）・起動時刻・
先行/後続ジョブ）のみを、見本の図中ラベルと同じセル位置に記入する。ジョブフローの
図形キャンバスには手を触れない。凡例（AP65〜AP70）はテンプレの記載を残す。

対象はバッチ取引 BTB01 経理連携ファイル作成。最終承認済の立替精算額を集計して
経理システム連携ファイルを作成するジョブを、日次夜間のスケジュールで単独起動する。
先行・後続を持たない単一ジョブ構成のため、依存関係は「なし」と明記する。
"""
from __future__ import annotations

from common import open_template, fill_history, put, save

TEMPLATE = "ネット・ジョブフロー_BT_出張申請.xlsx"
OUTPUT = "ネット・ジョブフロー_BT_出張申請.xlsx"
PRODUCT = "ネット・ジョブフロー"

# テンプレの（空の）フロー図シート。見本ではスケジュール条件がシート名になる。
BASE_SHEET = "1.1.  スケジュール条件 "
SCHEDULE = "1.1. 日次(夜間)"

# ジョブネット／ジョブの識別（BTB01 経理連携ファイル作成バッチ）。
JOBNET_ID = "NBT0601"
JOBNET_NAME = "経理連携ファイル作成"
JOB_ID = "BTB0101"          # バッチ処理ID
JOB_NAME = "経理連携ファイル作成バッチ"
START_TIME = "起動時刻：02:00"
END_TIME = "最遅終了時刻：05:00"


def fill_flow(ws):
    """フロー図中のテキストラベル（表領域）を見本の配置に倣って記入する。

    見本（月次夜間）では、ジョブネット見出しを C 列、その配下のジョブを D 列に置き、
    起動時刻・最遅終了時刻をジョブネット見出しの直下に記す。図形（枠・矢印）は空のまま。
    """
    # スケジュール条件（節見出し）。B5「1. ネット・ジョブフロー」はテンプレ既定を残す。
    put(ws, "C6", SCHEDULE)
    # ジョブネット
    put(ws, "C8", f"{JOBNET_ID}：{JOBNET_NAME}")
    put(ws, "C9", START_TIME)
    put(ws, "C10", END_TIME)
    # ジョブ（バッチ処理ID：バッチ処理名）
    put(ws, "D12", f"{JOB_ID}：{JOB_NAME}")
    # 先行／後続ジョブ（単一ジョブのため依存なし）
    put(ws, "D14", "先行ジョブ：なし（日次夜間スケジュールにより単独起動）")
    put(ws, "D15", "後続ジョブ：なし")


def fill_toc(wb):
    toc = wb["目次"]
    # B7「1. ネット・ジョブフロー」はテンプレ既定を残し、スケジュール条件のみ更新する。
    put(toc, "C8", SCHEDULE)


def build() -> str:
    wb = open_template(TEMPLATE)
    fill_history(wb, product_name=PRODUCT)

    ws = wb[BASE_SHEET]
    ws.title = SCHEDULE
    fill_flow(ws)
    fill_toc(wb)
    return save(wb, OUTPUT)


if __name__ == "__main__":
    print("wrote", build())
