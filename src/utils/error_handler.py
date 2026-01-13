import functools
import traceback
from typing import Callable, Any
from .logger import default_logger


def handle_errors(logger=None):
    """
    関数のエラーハンドリングデコレータ

    Args:
        logger: 使用するロガー（デフォルトはdefault_logger）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            log = logger or default_logger
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                log.error(f"ファイルが見つかりません: {e}")
                raise
            except ValueError as e:
                log.error(f"値エラー: {e}")
                raise
            except ConnectionError as e:
                log.error(f"接続エラー: {e}")
                raise
            except Exception as e:
                log.error(f"予期しないエラーが発生しました: {e}")
                log.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator


def safe_execute(func: Callable, default_return: Any = None, logger=None) -> Any:
    """
    関数を安全に実行し、エラー時はデフォルト値を返す

    Args:
        func: 実行する関数
        default_return: エラー時の戻り値
        logger: 使用するロガー

    Returns:
        関数の戻り値、またはエラー時はdefault_return
    """
    log = logger or default_logger
    try:
        return func()
    except Exception as e:
        log.error(f"関数実行中にエラー: {e}")
        log.debug(traceback.format_exc())
        return default_return


class APIRetryHandler:
    """
    API呼び出しのリトライ処理を行うクラス
    """
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        Args:
            max_retries: 最大リトライ回数
            backoff_factor: バックオフ係数（待機時間の倍率）
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = default_logger

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        関数をリトライ付きで実行

        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数

        Returns:
            関数の戻り値

        Raises:
            最後のエラー（全リトライ失敗時）
        """
        import time

        last_exception = None
        wait_time = 1.0

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"API呼び出し失敗 (試行 {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    self.logger.info(f"{wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                    wait_time *= self.backoff_factor

        self.logger.error(f"全てのリトライが失敗しました: {last_exception}")
        raise last_exception


def get_user_friendly_error_message(error: Exception) -> str:
    """
    APIエラーをユーザーにわかりやすい日本語メッセージに変換
    
    Args:
        error: 発生したエラー
        
    Returns:
        ユーザー向けのわかりやすいエラーメッセージ
    """
    error_str = str(error)
    
    # 429 クォータ超過エラー
    if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
        return """
⚠️ **API利用制限に達しました**

Google Gemini APIの無料枠の制限に達しました。以下のいずれかをお試しください：

1. **数分待ってから再度お試しください**（推奨）
   - 無料枠は時間経過でリセットされます
   
2. **質問の頻度を減らす**
   - 連続して質問を送信すると制限に達しやすくなります
   
3. **Google AI Studioで使用状況を確認**
   - https://ai.google.dev/

詳細: 無料枠では1分あたり最大20リクエストまでです。
"""
    
    # 401/403 認証エラー
    elif "401" in error_str or "403" in error_str or "authentication" in error_str.lower() or "api key" in error_str.lower():
        return """
🔑 **API認証エラー**

Google Gemini APIキーが無効または設定されていません。

**解決方法:**
1. `.env` ファイルに正しいAPIキーが設定されているか確認
2. APIキーが有効期限内か確認
3. Google AI Studioで新しいAPIキーを取得: https://ai.google.dev/

現在の設定: `.env` ファイルの `GOOGLE_API_KEY` を確認してください。
"""
    
    # 500番台 サーバーエラー
    elif "500" in error_str or "502" in error_str or "503" in error_str:
        return """
🔧 **サーバーエラー**

Google Gemini APIのサーバーで一時的な問題が発生しています。

**解決方法:**
- しばらく待ってから再度お試しください
- 問題が続く場合は、Google AI Studioのステータスページを確認: https://status.cloud.google.com/

これは一時的な問題で、通常数分で解決します。
"""
    
    # ネットワークエラー
    elif "connection" in error_str.lower() or "network" in error_str.lower() or "timeout" in error_str.lower():
        return """
🌐 **ネットワーク接続エラー**

インターネット接続に問題があるか、APIサーバーに到達できません。

**解決方法:**
1. インターネット接続を確認
2. ファイアウォールやプロキシ設定を確認
3. しばらく待ってから再度お試しください
"""
    
    # PDFファイルエラー
    elif "pdf" in error_str.lower() or "file not found" in error_str.lower():
        return f"""
📄 **PDFファイルエラー**

PDFファイルの処理中に問題が発生しました。

**解決方法:**
1. PDFファイルが破損していないか確認
2. ファイルサイズが10MB以下か確認
3. 別のPDFファイルで試してみる

エラー詳細: {error_str}
"""
    
    # その他のエラー
    else:
        return f"""
❌ **エラーが発生しました**

予期しないエラーが発生しました。

**解決方法:**
1. ページをリロードして再度お試しください
2. 問題が続く場合は、開発者にお問い合わせください

エラー詳細: {error_str}
"""
