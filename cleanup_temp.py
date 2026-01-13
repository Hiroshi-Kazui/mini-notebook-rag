#!/usr/bin/env python3
"""
一時ファイルを自動削除するスクリプト
"""
import os
import glob
import time
from pathlib import Path


def cleanup_temp_files(max_age_minutes=60):
    """
    一時ファイルを削除

    Args:
        max_age_minutes: この時間（分）より古いファイルを削除
    """
    # プロジェクトルートディレクトリ
    project_root = Path(__file__).parent

    # 削除対象のパターン
    patterns = [
        "tmpclaude-*-cwd",
        "tmp*-cwd",
        "*.tmp",
        ".temp_*"
    ]

    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_minutes * 60

    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            try:
                # ファイルの最終更新時刻を確認
                file_age = current_time - os.path.getmtime(file_path)

                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"削除: {file_path.name} (作成から {file_age/60:.1f} 分経過)")
            except Exception as e:
                print(f"エラー: {file_path.name} の削除に失敗 - {e}")

    if deleted_count > 0:
        print(f"\n✅ 合計 {deleted_count} 個の一時ファイルを削除しました")
    else:
        print("✅ 削除対象の一時ファイルはありません")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="一時ファイルを自動削除")
    parser.add_argument(
        "--max-age",
        type=int,
        default=60,
        help="この時間（分）より古いファイルを削除 (デフォルト: 60分)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="経過時間に関わらず、すべての一時ファイルを削除"
    )

    args = parser.parse_args()

    if args.force:
        cleanup_temp_files(max_age_minutes=0)
    else:
        cleanup_temp_files(max_age_minutes=args.max_age)
