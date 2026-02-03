import streamlit as st
import sys
import os
import glob
import time

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.ui.streamlit_helpers import (
    process_uploaded_pdf,
    process_multiple_pdfs,
    generate_answer_ui,
    clear_chat_history,
    check_db_status,
    clear_database,
    delete_source_from_notebook,
    get_notebook_sources_ui,
)
from src.utils.chat_history import ChatHistoryManager
from src.utils.notebook_manager import NotebookManager


def cleanup_temp_files_on_startup():
    """Delete stale temp files in cwd (older than 1 hour)."""
    try:
        current_time = time.time()
        max_age_seconds = 60 * 60
        patterns = ["tmpclaude-*-cwd", "tmp*-cwd"]
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                except Exception:
                    pass
    except Exception:
        pass


cleanup_temp_files_on_startup()

st.set_page_config(
    page_title="Mini-Notebook RAG",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced CSS for NotebookLM-style clean UI
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600&display=swap');
    
    * { 
        font-family: "Noto Sans JP", "Hiragino Kaku Gothic Pro", "Yu Gothic", "Meiryo", sans-serif; 
    }
    
    /* Header styling */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    .app-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a1a1a;
        margin: 0;
    }
    
    /* Sources panel styling */
    .source-item {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    
    .source-item:hover {
        border-color: #4285f4;
        box-shadow: 0 2px 8px rgba(66, 133, 244, 0.15);
    }
    
    /* Chat styling */
    .stChatMessage { 
        font-size: 14px;
        border-radius: 12px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Settings gear icon */
    .settings-btn {
        background: transparent;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        transition: background 0.2s;
    }
    
    .settings-btn:hover {
        background: #f0f0f0;
    }
    
    /* Upload area styling */
    .uploadedFile {
        border-radius: 8px;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-ready {
        background: #e6f4ea;
        color: #1e8e3e;
    }
    
    .status-pending {
        background: #fef7e0;
        color: #f9a825;
    }
    
    /* Clean expander */
    .streamlit-expanderHeader {
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Modal-like dialog styling */
    div[data-testid="stDialog"] {
        border-radius: 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize notebook manager
if "notebook_mgr" not in st.session_state:
    st.session_state.notebook_mgr = NotebookManager()
notebook_mgr = st.session_state.notebook_mgr
if notebook_mgr.needs_migration():
    result = notebook_mgr.migrate_existing_data()
    if result.get("success"):
        st.success(result.get("message", "Migration completed."))

current_nb_id = notebook_mgr.get_current_notebook()
if "current_notebook_id" not in st.session_state:
    st.session_state.current_notebook_id = current_nb_id

if st.session_state.current_notebook_id != current_nb_id:
    st.session_state.current_notebook_id = current_nb_id

# Initialize chat manager
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatHistoryManager(
        notebook_id=st.session_state.current_notebook_id, max_messages=50
    )

if "messages" not in st.session_state:
    st.session_state.messages = st.session_state.chat_manager.load_history()

if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_pdf" not in st.session_state:
    st.session_state.current_pdf = None
if "db_ready" not in st.session_state:
    db_status = check_db_status()
    st.session_state.db_ready = db_status["exists"] and db_status["document_count"] > 0

# Initialize settings with defaults
if "initial_k" not in st.session_state:
    st.session_state.initial_k = 100
if "final_k" not in st.session_state:
    st.session_state.final_k = 20
if "n_results" not in st.session_state:
    st.session_state.n_results = 3
if "show_sources" not in st.session_state:
    st.session_state.show_sources = True


# Settings dialog
@st.dialog("⚙️ 設定", width="large")
def settings_dialog():
    """Settings modal dialog"""
    st.subheader("LLMリランキング設定")
    
    initial_k = st.slider(
        "初期取得件数",
        min_value=20,
        max_value=153,
        value=st.session_state.initial_k,
        key="settings_initial_k",
    )
    
    final_k = st.slider(
        "リランキング後件数",
        min_value=5,
        max_value=50,
        value=st.session_state.final_k,
        key="settings_final_k",
    )
    
    st.divider()
    st.subheader("表示設定")
    
    n_results = st.slider(
        "使用チャンク数",
        min_value=1,
        max_value=20,
        value=st.session_state.n_results,
        key="settings_n_results",
    )
    
    show_sources = st.checkbox(
        "ソース表示",
        value=st.session_state.show_sources,
        key="settings_show_sources",
    )
    
    st.divider()
    st.subheader("データ管理")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ チャット履歴をクリア", use_container_width=True):
            clear_chat_history(st.session_state)
            st.session_state.chat_manager.clear_history()
            st.rerun()
    
    with col2:
        if st.button("🗄️ データベースをクリア", use_container_width=True, type="secondary"):
            result = clear_database()
            if result["success"]:
                st.success(result["message"])
                st.session_state.db_ready = False
                st.session_state.pdf_processed = False
                time.sleep(1)
                st.rerun()
            else:
                st.error(result["message"])
    
    st.divider()
    if st.button("保存して閉じる", type="primary", use_container_width=True):
        st.session_state.initial_k = initial_k
        st.session_state.final_k = final_k
        st.session_state.n_results = n_results
        st.session_state.show_sources = show_sources
        st.rerun()


# Notebook management dialog
@st.dialog("📓 ノートブック管理", width="large")
def notebook_management_dialog():
    """Notebook management modal dialog"""
    notebooks = notebook_mgr.list_notebooks()
    
    tab1, tab2 = st.tabs(["📋 ノートブック一覧", "➕ 新規作成"])
    
    with tab1:
        if notebooks:
            for nb in notebooks:
                col_a, col_b, col_c = st.columns([4, 2, 1])
                with col_a:
                    is_current = nb["id"] == st.session_state.current_notebook_id
                    name_display = f"**{nb['name']}**" if is_current else nb["name"]
                    st.markdown(name_display)
                    if nb.get("description"):
                        st.caption(nb["description"])
                with col_b:
                    if not is_current:
                        if st.button("切り替え", key=f"switch_{nb['id']}"):
                            notebook_mgr.set_current_notebook(nb["id"])
                            st.session_state.current_notebook_id = nb["id"]
                            st.session_state.chat_manager.switch_notebook(nb["id"])
                            st.session_state.messages = st.session_state.chat_manager.load_history()
                            st.rerun()
                    else:
                        st.caption("✓ 使用中")
                with col_c:
                    disabled = is_current
                    if st.button("🗑️", key=f"del_nb_{nb['id']}", disabled=disabled):
                        result = notebook_mgr.delete_notebook(nb["id"], delete_sources=True)
                        if result["success"]:
                            st.success(result["message"])
                            time.sleep(1)
                        else:
                            st.error(result["message"])
                        st.rerun()
                st.divider()
        else:
            st.info("ノートブックがありません")
    
    with tab2:
        nb_name = st.text_input("名称", max_chars=50, placeholder="新しいノートブック")
        nb_desc = st.text_area("説明（任意）", max_chars=200, placeholder="このノートブックの説明...")
        
        if st.button("作成", type="primary", use_container_width=True):
            if nb_name:
                result = notebook_mgr.create_notebook(nb_name, nb_desc)
                if result["success"]:
                    notebook_mgr.set_current_notebook(result["id"])
                    st.session_state.current_notebook_id = result["id"]
                    st.session_state.chat_manager.switch_notebook(result["id"])
                    st.session_state.messages = st.session_state.chat_manager.load_history()
                    st.success(result["message"])
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.warning("名称を入力してください")


def main():
    # Header with title, notebook selector, and settings
    header_col1, header_col2, header_col3 = st.columns([3, 2, 1])
    
    with header_col1:
        st.markdown("# 📓 Mini-Notebook RAG")
        st.caption("Japanese PDF Q&A powered by Google Gemini")
    
    with header_col2:
        notebooks = notebook_mgr.list_notebooks()
        if notebooks:
            notebook_options = {nb["name"]: nb["id"] for nb in notebooks}
            selected_name = st.selectbox(
                "ノートブック",
                options=list(notebook_options.keys()),
                index=list(notebook_options.values()).index(st.session_state.current_notebook_id)
                if st.session_state.current_notebook_id in notebook_options.values()
                else 0,
                label_visibility="collapsed",
            )
            selected_id = notebook_options[selected_name]
            if selected_id != st.session_state.current_notebook_id:
                notebook_mgr.set_current_notebook(selected_id)
                st.session_state.current_notebook_id = selected_id
                st.session_state.chat_manager.switch_notebook(selected_id)
                st.session_state.messages = st.session_state.chat_manager.load_history()
                st.rerun()
    
    with header_col3:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📋", help="ノートブック管理"):
                notebook_management_dialog()
        with col_b:
            if st.button("⚙️", help="設定"):
                settings_dialog()

    st.divider()

    # Sidebar - Sources and Upload only
    with st.sidebar:
        st.header("📄 Sources")
        
        # Status indicator
        db_status = check_db_status()
        if db_status["exists"] and db_status["document_count"] > 0:
            st.success(f"✓ {db_status['document_count']} ベクトル準備完了")
        else:
            st.info("PDFをアップロードしてください")
        
        st.divider()
        
        # Sources list
        sources = get_notebook_sources_ui(st.session_state.current_notebook_id)
        if sources:
            for src in sources:
                with st.container():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**📄 {src['filename']}**")
                        st.caption(f"{src['chunk_count']} チャンク")
                    with col_b:
                        if st.button("🗑️", key=f"del_{src['filename']}", help="削除"):
                            result = delete_source_from_notebook(
                                st.session_state.current_notebook_id,
                                src["filename"],
                            )
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
                            st.rerun()
                st.divider()
        else:
            st.caption("ソースはまだありません")
        
        st.divider()
        
        # PDF Upload - Multiple files only
        st.subheader("📤 PDFアップロード")
        uploaded_files = st.file_uploader(
            "PDFファイルを選択（複数可）",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="日本語PDFをアップロードしてください",
        )
        
        if uploaded_files:
            st.info(f"📎 {len(uploaded_files)} ファイル選択中")
            if st.button("処理を開始", type="primary", use_container_width=True):
                with st.spinner(f"{len(uploaded_files)} ファイルを処理中..."):
                    result = process_multiple_pdfs(
                        uploaded_files,
                        notebook_id=st.session_state.current_notebook_id,
                    )
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.pdf_processed = True
                        st.session_state.db_ready = True
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result["message"])
                        st.session_state.pdf_processed = False

    # Main chat area
    if not st.session_state.db_ready:
        st.markdown(
            """
            <div style="text-align: center; padding: 4rem 2rem;">
                <h2 style="color: #5f6368;">📄 PDFをアップロードして始めましょう</h2>
                <p style="color: #80868b; font-size: 1.1rem;">
                    サイドバーからPDFファイルをアップロードすると、<br>
                    AIがドキュメントの内容について質問に答えます
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "sources" in message and message["sources"] and st.session_state.show_sources:
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            if isinstance(source, tuple) and len(source) >= 4:
                                if len(source) == 5:
                                    page, src_file, url, text, chunks = source
                                    with st.expander(f"📄 {text}"):
                                        st.markdown(f"[PDFを開く]({url})")
                                        st.caption("**関連チャンク:**")
                                        for idx, chunk in enumerate(chunks, 1):
                                            st.caption(f"{idx}. {chunk}")
                                else:
                                    page, src_file, url, text = source
                                    st.markdown(f"[{text}]({url})")
                            elif isinstance(source, str):
                                st.markdown(source)
                            else:
                                st.caption(str(source))

        # Chat input
        if prompt := st.chat_input("質問を入力してください..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.chat_manager.add_message("user", prompt)

            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("回答生成中..."):
                    response = generate_answer_ui(
                        prompt,
                        notebook_id=st.session_state.current_notebook_id,
                        n_results=st.session_state.n_results,
                        initial_k=st.session_state.initial_k,
                        final_k=st.session_state.final_k,
                    )

                    if response["success"]:
                        st.write(response["answer"])
                        if response["sources"] and st.session_state.show_sources:
                            with st.expander("📚 Sources"):
                                for source in response["sources"]:
                                    if isinstance(source, tuple) and len(source) >= 4:
                                        if len(source) == 5:
                                            page, src_file, url, text, chunks = source
                                            with st.expander(f"📄 {text}"):
                                                st.markdown(f"[PDFを開く]({url})")
                                                st.caption("**関連チャンク:**")
                                                for idx, chunk in enumerate(chunks, 1):
                                                    st.caption(f"{idx}. {chunk}")
                                        else:
                                            page, src_file, url, text = source
                                            st.markdown(f"[{text}]({url})")
                                    elif isinstance(source, str):
                                        st.markdown(source)
                                    else:
                                        st.caption(str(source))

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response["answer"],
                                "sources": response["sources"],
                            }
                        )
                        st.session_state.chat_manager.add_message(
                            "assistant", response["answer"], response["sources"]
                        )
                    else:
                        error_msg = response["error"]
                        st.markdown(error_msg)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_msg, "sources": []}
                        )
                        st.session_state.chat_manager.add_message("assistant", error_msg)


if __name__ == "__main__":
    main()
