import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "mini_notebook_rag", log_level: str = "INFO") -> logging.Logger:
    """
    アプリケーション用のロガーをセットアップ

    Args:
        name: ロガー名
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        設定済みのロガーインスタンス
    """
    # ログディレクトリの作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # ログファイル名（日付付き）
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    # ロガーの取得
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # 既存のハンドラをクリア（重複を防ぐ）
    if logger.handlers:
        logger.handlers.clear()

    # フォーマッタの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ファイルハンドラ（UTF-8エンコーディング）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# デフォルトロガーインスタンス
default_logger = setup_logger()
