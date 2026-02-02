import os
import sys
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.ingestion.extract import extract_text_from_pdf
from src.ingestion.chunking import chunk_text, save_processed_data
from src.embedding.store import store_embeddings
from src.retrieval.search import semantic_search
from src.retrieval.reranker import rerank_with_llm
from src.utils.logger import setup_logger
from src.utils.error_handler import handle_errors, APIRetryHandler, get_user_friendly_error_message
from src.types import ProcessResult, GenerateAnswerResult, DBStatus, MultiplePDFProcessResult, ClearDatabaseResult
from src.config.settings import settings

load_dotenv()

# ロガーのセットアップ
logger = setup_logger("streamlit_helpers")

# APIリトライハンドラー
retry_handler = APIRetryHandler(max_retries=3, backoff_factor=2.0)


@handle_errors(logger)
def process_uploaded_pdf(uploaded_file, raw_dir: str = "data/raw",
                        processed_dir: str = "data/processed",
                        storage_path: str = "storage/chroma") -> ProcessResult:
    """
    アップロードされたPDFを処理: 保存 -> 抽出 -> チャンク化 -> 埋め込み

    Returns:
        Dict with keys: 'success' (bool), 'message' (str), 'filename' (str), 'chunks_count' (int)
    """
    logger.info(f"PDFファイル処理開始: {uploaded_file.name}")

    try:
        # ファイルサイズチェック（10MB制限）
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10:
            logger.warning(f"ファイルサイズが大きすぎます: {file_size_mb:.2f}MB")
            return {
                'success': False,
                'message': f'ファイルサイズが大きすぎます（{file_size_mb:.2f}MB）。10MB以下のファイルをアップロードしてください。',
                'filename': uploaded_file.name,
                'chunks_count': 0
            }

        # 1. PDFを保存
        os.makedirs(raw_dir, exist_ok=True)
        pdf_path = os.path.join(raw_dir, uploaded_file.name)

        logger.debug(f"PDFを保存: {pdf_path}")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 2. テキスト抽出
        logger.info("テキスト抽出を開始")
        extracted_data = extract_text_from_pdf(pdf_path)
        logger.info(f"テキスト抽出完了: {len(extracted_data)}ページ")

        # 3. チャンク化
        logger.info("テキストチャンク化を開始")
        chunks = chunk_text(extracted_data)
        chunks_count = len(chunks)
        logger.info(f"チャンク化完了: {chunks_count}チャンク")

        # 4. 処理済みデータを保存
        os.makedirs(processed_dir, exist_ok=True)
        processed_filename = uploaded_file.name.replace('.pdf', '.json')
        processed_path = os.path.join(processed_dir, processed_filename)
        save_processed_data(chunks, processed_path)
        logger.debug(f"処理済みデータを保存: {processed_path}")

        # 5. 埋め込みを保存（リトライ付き）
        logger.info("埋め込み生成を開始")
        def embed_with_retry():
            return store_embeddings(processed_path, storage_path)

        retry_handler.execute(embed_with_retry)
        logger.info("埋め込み生成完了")

        return {
            'success': True,
            'message': f'PDFの処理が完了しました！ {chunks_count}個のチャンクを生成しました。',
            'filename': uploaded_file.name,
            'chunks_count': chunks_count
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}',
            'filename': uploaded_file.name if uploaded_file else None,
            'chunks_count': 0
        }




@handle_errors(logger)
def generate_answer_ui(query: str, storage_path: str = "storage/chroma",
                      n_results: int = 3, initial_k: int = 100, final_k: int = 20) -> GenerateAnswerResult:
    """
    RAGパイプラインでクエリに対する回答を生成（UI用）

    Args:
        query: ユーザーの質問
        storage_path: ChromaDBの保存パス
        n_results: 最終的に使用するチャンク数
        initial_k: 初期取得件数
        final_k: リランキング後に残す件数

    Returns:
        Dict with keys: 'success' (bool), 'answer' (str), 'sources' (List[str]), 'error' (str)
    """
    logger.info(f"クエリ処理開始: {query[:50]}...")

    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("API keyが設定されていません")
            return {
                'success': False,
                'answer': '',
                'sources': [],
                'error': 'GOOGLE_API_KEYが.envファイルに設定されていません。'
            }

        # 1. ベクトル検索 (Retrieval) - 広めに取得
        logger.info(f"ベクトル検索開始: 初期取得{initial_k}件")
        initial_results = semantic_search(query, storage_path, top_k=initial_k)
        logger.info(f"ベクトル検索完了: {len(initial_results)}件のチャンクを取得")

        # 2. LLMリランキング
        logger.info(f"LLMリランキング開始: 上位{final_k}件に絞り込み")
        reranked_results = rerank_with_llm(query, initial_results, top_k=final_k)
        logger.info(f"リランキング完了: {len(reranked_results)}件")

        # 3. プロンプト構築とソース情報の整理
        context = ""
        page_sources = {}  # ページごとにチャンクをグループ化

        # 最終的にn_results件のみ使用
        for i, result in enumerate(reranked_results[:n_results]):
            chunk_text = result['content']
            distance = result.get('distance', 0)
            rerank_score = result.get('rerank_score', 0)

            context += f"\n--- 資料 {i+1} ---\n{chunk_text}\n"

            page = result['metadata'].get('page', '不明')
            source = result['metadata'].get('source', '不明')

            # ページごとにグループ化
            page_key = f"{source}_{page}"
            if page_key not in page_sources:
                page_sources[page_key] = {
                    'page': page,
                    'source': source,
                    'chunks': [],
                    'avg_distance': 0,
                    'avg_rerank_score': 0,
                    'count': 0
                }
            # チャンクの最初の100文字をプレビューとして保存
            preview = chunk_text[:100].replace('\n', ' ') + "..." if len(chunk_text) > 100 else chunk_text
            page_sources[page_key]['chunks'].append(preview)
            page_sources[page_key]['avg_distance'] += distance
            page_sources[page_key]['avg_rerank_score'] += rerank_score
            page_sources[page_key]['count'] += 1

        # 平均スコアを計算してソート（リランクスコアで降順）
        for page_key in page_sources:
            page_sources[page_key]['avg_distance'] /= page_sources[page_key]['count']
            page_sources[page_key]['avg_rerank_score'] /= page_sources[page_key]['count']

        sorted_pages = sorted(page_sources.items(),
                            key=lambda x: x[1]['avg_rerank_score'],
                            reverse=True)
        
        # ソース情報をタプル形式で生成（ページごとに1つ、関連度順）
        sources = []
        for page_key, info in sorted_pages:
            page = info['page']
            source = info['source']
            chunk_count = len(info['chunks'])
            url = f"{settings.storage.pdf_server_base_url}/{source}#page={page}"
            text = f"📄 ページ {page} ({source}) - {chunk_count}件"
            # タプル: (page, source, url, text, chunks_preview)
            # chunksもタプルに変換（Streamlitのセッション状態に対応）
            sources.append((page, source, url, text, tuple(info['chunks'])))

        prompt = f"""
あなたは提供された資料に基づいて質問に答える、誠実で役立つアシスタントです。

【重要な指示】
1. 以下の資料を**すべて注意深く読み**、質問に関連する情報を探してください
2. 質問に直接答えている箇所だけでなく、**関連する文脈や背景情報**も含めて回答してください
3. 複数の資料に関連情報がある場合は、それらを**統合して包括的な回答**を作成してください
4. 回答の根拠となる資料番号を明記してください（例: [資料 1, 3]）
5. 資料に情報が含まれている場合は、必ず具体的に答えてください
6. 本当に情報が見つからない場合のみ「提供された資料にはその情報が含まれていません」と答えてください

【資料】
{context}

【ユーザーの質問】
{query}

【回答】
上記の資料に基づいて、質問に対する詳しい回答を日本語で記述してください。
"""

        # 3. 生成 (Generation) - リトライ付き
        logger.info("回答生成開始")

        def generate_with_retry():
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('models/gemini-flash-latest')
            return model.generate_content(prompt)

        response = retry_handler.execute(generate_with_retry)
        logger.info(f"回答生成完了: {len(response.text)}文字")

        return {
            'success': True,
            'answer': response.text,
            'sources': list(dict.fromkeys(sources)),  # 順序を維持して重複除去
            'error': ''
        }

    except Exception as e:
        logger.error(f"回答生成エラー: {e}")
        user_message = get_user_friendly_error_message(e)
        return {
            'success': False,
            'answer': '',
            'sources': [],
            'error': user_message
        }


def format_sources(sources: List[str]) -> str:
    """
    ソースリストをフォーマットして文字列として返す
    """
    if not sources:
        return "ソースなし"

    return "\n".join([f"• {source}" for source in sources])


def clear_chat_history(session_state) -> None:
    """
    チャット履歴をクリア
    """
    if 'messages' in session_state:
        session_state.messages = []


def check_db_status(storage_path: str = "storage/chroma") -> DBStatus:
    """
    ChromaDBのステータスを確認

    Returns:
        Dict with keys: 'exists' (bool), 'document_count' (int), 'collections' (List[str])
    """
    try:
        if not os.path.exists(storage_path):
            return {
                'exists': False,
                'document_count': 0,
                'collections': []
            }

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                'exists': False,
                'document_count': 0,
                'collections': [],
                'error': 'API key not configured'
            }

        client = chromadb.PersistentClient(path=storage_path)
        gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=api_key,
            model_name="models/text-embedding-004",
            task_type="RETRIEVAL_QUERY"
        )

        try:
            collection = client.get_collection(
                name="notebook_rag_collection",
                embedding_function=gemini_ef
            )
            count = collection.count()
            return {
                'exists': True,
                'document_count': count,
                'collections': ['notebook_rag_collection']
            }
        except Exception:
            return {
                'exists': True,
                'document_count': 0,
                'collections': []
            }

    except Exception as e:
        return {
            'exists': False,
            'document_count': 0,
            'collections': [],
            'error': str(e)
        }


def clear_database(storage_path: str = "storage/chroma") -> ClearDatabaseResult:
    """
    データベースをクリア

    Args:
        storage_path: Chromaデータベースのパス

    Returns:
        処理結果の辞書
    """
    import shutil

    try:
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            logger.info("データベースをクリアしました")
            return {
                'success': True,
                'message': '✅ データベースをクリアしました。ページをリロード（F5）してから、PDFを再アップロードしてください。'
            }
        else:
            return {
                'success': True,
                'message': 'データベースは既に空です'
            }
    except PermissionError as e:
        logger.error(f"データベースクリアエラー（ファイルロック）: {e}")
        return {
            'success': False,
            'message': '''⚠️ データベースのクリアに失敗しました

**原因**: 別のプロセスがデータベースファイルを使用中です。

**解決方法**:
以下のコマンドでコンテナを再起動してください:

```
docker compose restart
```
'''
        }
    except Exception as e:
        logger.error(f"データベースクリアエラー: {e}")
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }


def process_multiple_pdfs(uploaded_files: List, raw_dir: str = "data/raw",
                         processed_dir: str = "data/processed",
                         storage_path: str = "storage/chroma") -> MultiplePDFProcessResult:
    """
    複数のPDFファイルを一括処理

    Returns:
        Dict with keys: 'success' (bool), 'message' (str), 'results' (List[Dict]), 'total_chunks' (int)
    """
    logger.info(f"複数PDF処理開始: {len(uploaded_files)}ファイル")

    results = []
    total_chunks = 0
    failed_files = []

    for uploaded_file in uploaded_files:
        result = process_uploaded_pdf(uploaded_file, raw_dir, processed_dir, storage_path)
        results.append({
            'filename': uploaded_file.name,
            'success': result['success'],
            'message': result['message'],
            'chunks_count': result['chunks_count']
        })

        if result['success']:
            total_chunks += result['chunks_count']
        else:
            failed_files.append(uploaded_file.name)

    success_count = len([r for r in results if r['success']])
    message = f"{success_count}/{len(uploaded_files)}ファイルを正常に処理しました。合計{total_chunks}チャンク。"

    if failed_files:
        message += f"\n失敗: {', '.join(failed_files)}"

    logger.info(f"複数PDF処理完了: {message}")

    return {
        'success': success_count > 0,
        'message': message,
        'results': results,
        'total_chunks': total_chunks
    }


def get_processed_pdfs(raw_dir: str = "data/raw") -> List[str]:
    """
    処理済みのPDFファイル一覧を取得

    Returns:
        PDFファイル名のリスト
    """
    if not os.path.exists(raw_dir):
        return []

    pdf_files = [f for f in os.listdir(raw_dir) if f.endswith('.pdf')]
    return sorted(pdf_files)
