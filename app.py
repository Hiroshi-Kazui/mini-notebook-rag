import streamlit as st
import sys
import os
import glob
import time

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.ui.streamlit_helpers import (
    process_uploaded_pdf,
    process_multiple_pdfs,
    get_processed_pdfs,
    generate_answer_ui,
    format_sources,
    clear_chat_history,
    check_db_status,
    clear_database
)
from src.utils.chat_history import ChatHistoryManager

# 起動時に古い一時ファイルをクリーンアップ
def cleanup_temp_files_on_startup():
    """アプリ起動時に1時間以上前の一時ファイルを削除"""
    try:
        current_time = time.time()
        max_age_seconds = 60 * 60  # 1時間

        patterns = ["tmpclaude-*-cwd", "tmp*-cwd"]
        deleted_count = 0

        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted_count += 1
                except Exception:
                    pass

        if deleted_count > 0:
            print(f"🧹 {deleted_count}個の古い一時ファイルを削除しました")
    except Exception:
        pass  # エラーは無視

# 起動時にクリーンアップ実行
cleanup_temp_files_on_startup()

# ページ設定
st.set_page_config(
    page_title="Mini-Notebook RAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 日本語フォント対応のカスタムCSS
st.markdown("""
<style>
    * {
        font-family: "Hiragino Kaku Gothic Pro", "Yu Gothic", "Meiryo", sans-serif;
    }
    .stChatMessage {
        font-size: 14px;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# チャット履歴マネージャーの初期化
if 'chat_manager' not in st.session_state:
    st.session_state.chat_manager = ChatHistoryManager(max_messages=50)

# セッション状態の初期化
if 'messages' not in st.session_state:
    # 永続化された履歴をロード
    st.session_state.messages = st.session_state.chat_manager.load_history()
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False
if 'current_pdf' not in st.session_state:
    st.session_state.current_pdf = None
if 'db_ready' not in st.session_state:
    db_status = check_db_status()
    st.session_state.db_ready = db_status['exists'] and db_status['document_count'] > 0


def main():
    # タイトル
    st.title("🤖 Mini-Notebook RAG")
    st.caption("Japanese PDF Q&A powered by Google Gemini")

    # サイドバー
    with st.sidebar:
        st.header("📄 PDF Upload")

        # 複数PDF処理モードの選択
        upload_mode = st.radio(
            "アップロードモード",
            ["単一ファイル", "複数ファイル"],
            horizontal=True
        )

        if upload_mode == "単一ファイル":
            # PDFアップローダー（単一）
            uploaded_file = st.file_uploader(
                "PDFファイルを選択",
                type=['pdf'],
                help="日本語のPDFドキュメントをアップロードしてください"
            )

            if uploaded_file is not None:
                st.session_state.pdf_uploaded = True
                st.session_state.current_pdf = uploaded_file.name

                # 処理ボタン
                if st.button("PDFを処理", type="primary", use_container_width=True):
                    with st.spinner('PDFを処理中...'):
                        result = process_uploaded_pdf(uploaded_file)

                        if result['success']:
                            st.success(result['message'])
                            st.session_state.pdf_processed = True
                            st.session_state.db_ready = True
                        else:
                            st.error(result['message'])
                            st.session_state.pdf_processed = False
        else:
            # PDFアップローダー（複数）
            uploaded_files = st.file_uploader(
                "PDFファイルを選択（複数可）",
                type=['pdf'],
                accept_multiple_files=True,
                help="複数の日本語PDFドキュメントをアップロードしてください"
            )

            if uploaded_files:
                st.info(f"{len(uploaded_files)}ファイル選択中")

                # 処理ボタン
                if st.button("すべて処理", type="primary", use_container_width=True):
                    with st.spinner(f'{len(uploaded_files)}ファイルを処理中...'):
                        result = process_multiple_pdfs(uploaded_files)

                        if result['success']:
                            st.success(result['message'])
                            st.session_state.pdf_processed = True
                            st.session_state.db_ready = True

                            # 詳細表示
                            with st.expander("処理詳細"):
                                for r in result['results']:
                                    status = "✅" if r['success'] else "❌"
                                    st.caption(f"{status} {r['filename']}: {r['chunks_count']}チャンク")
                        else:
                            st.error(result['message'])
                            st.session_state.pdf_processed = False

        # ステータス表示
        st.header("📊 Status")

        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.pdf_uploaded:
                st.success("✓ PDF読込")
            else:
                st.info("○ PDF待機")

        with col2:
            if st.session_state.db_ready:
                st.success("✓ DB準備完了")
            else:
                st.warning("○ DB未準備")

        if st.session_state.current_pdf:
            st.caption(f"現在のPDF: {st.session_state.current_pdf}")

        # データベース情報
        db_status = check_db_status()
        if db_status['exists'] and db_status['document_count'] > 0:
            st.info(f"📦 保存チャンク数: {db_status['document_count']}")

        # チャット履歴情報
        msg_count = st.session_state.chat_manager.get_message_count()
        if msg_count > 0:
            st.info(f"💬 チャット履歴: {msg_count}/50メッセージ")

        # 設定
        st.header("⚙️ Settings")

        # リランキング設定
        with st.expander("🔍 LLMリランキング設定"):
            st.caption("ベクトル検索で広めに取得 → LLMで関連性を評価 → 上位のみ使用")

            initial_k = st.slider(
                "初期取得件数",
                min_value=20,
                max_value=153,
                value=100,
                help="ベクトル検索で最初に取得するチャンク数（広めに取る）"
            )

            final_k = st.slider(
                "リランキング後の件数",
                min_value=5,
                max_value=50,
                value=20,
                help="LLMリランキング後に残すチャンク数"
            )

        n_results = st.slider(
            "最終使用チャンク数",
            min_value=1,
            max_value=20,
            value=3,
            help="回答生成に実際に使用するチャンク数"
        )

        show_sources = st.checkbox(
            "ソース参照を表示",
            value=True,
            help="回答にソース情報を表示"
        )

        # コントロールボタン
        st.header("🛠️ Controls")

        if st.button("🗑️ チャット履歴をクリア", use_container_width=True):
            clear_chat_history(st.session_state)
            st.session_state.chat_manager.clear_history()
            st.rerun()

        if st.button("💥 データベースをクリア", use_container_width=True, type="secondary"):
            result = clear_database()
            if result['success']:
                st.success(result['message'])
                st.session_state.db_ready = False
                st.session_state.pdf_processed = False
                st.rerun()
            else:
                st.error(result['message'])

    # メインエリア
    if not st.session_state.db_ready:
        st.info("👈 サイドバーからPDFをアップロードして、処理を開始してください。")
        st.markdown("""
        ### 使い方
        1. サイドバーでPDFファイルを選択
        2. 「PDFを処理」ボタンをクリック
        3. 処理が完了したら、下の入力欄で質問を入力
        4. AIが資料に基づいて回答します

        ### サンプルクエリ
        - "ナアマンについて教えてください"
        - "教える技術を磨くにはどうすればいいですか？"
        - "エホバを信頼することの大切さについて"
        - "忍耐について聖書は何と言っていますか？"
        """)
    else:
        # チャット履歴を表示
        for message in st.session_state.messages:
            with st.chat_message(message['role']):
                st.write(message['content'])

                # ソース参照を表示
                if 'sources' in message and message['sources'] and show_sources:
                    with st.expander("📚 参照ソース"):
                        for source in message['sources']:
                            if isinstance(source, tuple) and len(source) >= 4:
                                if len(source) == 5:
                                    # 新形式: (page, src_file, url, text, chunks_preview)
                                    page, src_file, url, text, chunks = source
                                    with st.expander(f"🔗 {text}"):
                                        st.markdown(f"[PDFを開く]({url})")
                                        st.caption("**参照チャンク:**")
                                        for idx, chunk in enumerate(chunks, 1):
                                            st.caption(f"{idx}. {chunk}")
                                else:
                                    # 旧形式: (page, src_file, url, text)
                                    page, src_file, url, text = source
                                    st.markdown(f"[{text}]({url})")
                            elif isinstance(source, str):
                                st.markdown(source)
                            else:
                                st.caption(str(source))

        # チャット入力
        if prompt := st.chat_input("質問を入力してください..."):
            # ユーザーメッセージを追加（セッションと永続化）
            st.session_state.messages.append({
                'role': 'user',
                'content': prompt
            })
            st.session_state.chat_manager.add_message('user', prompt)

            # ユーザーメッセージを表示
            with st.chat_message('user'):
                st.write(prompt)

            # AIの回答を生成
            with st.chat_message('assistant'):
                with st.spinner('考え中...'):
                    response = generate_answer_ui(
                        prompt,
                        n_results=n_results,
                        initial_k=initial_k,
                        final_k=final_k
                    )

                    if response['success']:
                        st.write(response['answer'])

                        # ソース参照を表示
                        if response['sources'] and show_sources:
                            with st.expander("📚 参照ソース"):
                                for source in response['sources']:
                                    if isinstance(source, tuple) and len(source) >= 4:
                                        if len(source) == 5:
                                            # 新形式: (page, src_file, url, text, chunks_preview)
                                            page, src_file, url, text, chunks = source
                                            with st.expander(f"🔗 {text}"):
                                                st.markdown(f"[PDFを開く]({url})")
                                                st.caption("**参照チャンク:**")
                                                for idx, chunk in enumerate(chunks, 1):
                                                    st.caption(f"{idx}. {chunk}")
                                        else:
                                            # 旧形式: (page, src_file, url, text)
                                            page, src_file, url, text = source
                                            st.markdown(f"[{text}]({url})")
                                    elif isinstance(source, str):
                                        st.markdown(source)
                                    else:
                                        st.caption(str(source))

                        # メッセージ履歴に追加（セッションと永続化）
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': response['answer'],
                            'sources': response['sources']
                        })
                        st.session_state.chat_manager.add_message(
                            'assistant',
                            response['answer'],
                            response['sources']
                        )
                    else:
                        error_msg = response['error']
                        st.markdown(error_msg)
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': error_msg,
                            'sources': []
                        })
                        st.session_state.chat_manager.add_message('assistant', error_msg)


if __name__ == "__main__":
    main()
