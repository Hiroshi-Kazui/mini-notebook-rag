# Mini-Notebook RAG

A simple RAG (Retrieval-Augmented Generation) application for PDF analysis inspired by NotebookLM, built for learning LLM fundamentals.

## 概要

このプロジェクトは、PDFドキュメントからベクトルデータベースを構築し、質問応答を行うシステムです。Google Gemini APIを使用して埋め込みと回答生成を行い、ChromaDBでベクトル検索を実現しています。

### 主要機能

- 📄 **PDF処理**: PDFからテキストを抽出し、チャンク化
- 🔍 **ベクトル検索**: ChromaDBを使用した類似度検索
- 🤖 **AI回答生成**: Google Gemini Flashによる高品質な回答生成
- 💬 **Webインターフェース**: Streamlitによる使いやすいチャットUI
- 🇯🇵 **日本語サポート**: 日本語コンテンツに最適化
- 📚 **複数PDF処理**: 複数のPDFファイルを一括処理
- 💾 **会話履歴の永続化**: 最大50メッセージの会話履歴を自動保存
- 🔄 **自動リトライ**: API呼び出しの自動リトライ機能
- 📊 **ログ機能**: 詳細なログ記録とエラートラッキング
- ✅ **テストカバレッジ**: ユニットテストによる品質保証

### 技術スタック

- **PDF処理**: PyMuPDF
- **テキスト分割**: LangChain Text Splitters
- **埋め込み**: Google Gemini text-embedding-004
- **ベクトルDB**: ChromaDB
- **生成モデル**: Google Gemini Flash
- **UI**: Streamlit
- **環境**: Python 3.8+, Windows 11対応

## 🔧 技術実装の詳細

### RAGパイプラインのアーキテクチャ

```
PDF → Extract → Chunk → Embed → Store → Search → Rerank → Generate
```

#### 1. PDF処理（Ingestion）
- **ツール**: PyMuPDF (fitz)
- **処理速度**: 約10ページ/秒
- **特徴**: テキスト抽出精度が高く、日本語対応が優秀
- **実装**: [src/ingestion/extract.py](src/ingestion/extract.py)

```python
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    doc = fitz.open(pdf_path)
    extracted = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        extracted.append({
            "page": page_num,
            "content": text,
            "metadata": {"source": pdf_path}
        })
    return extracted
```

#### 2. チャンキング戦略
- **ライブラリ**: LangChain RecursiveCharacterTextSplitter
- **チャンクサイズ**: 500文字
- **オーバーラップ**: 50文字（10%）
- **理由**: 日本語の文脈を保持しつつ、コンテキストウィンドウ内に収める最適サイズ
- **実装**: [src/ingestion/chunking.py](src/ingestion/chunking.py)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "、", " ", ""]
)
```

#### 3. 埋め込み（Embedding）
- **モデル**: Google Gemini text-embedding-004
- **次元数**: 768次元
- **タスクタイプ**: RETRIEVAL_DOCUMENT（保存時） / RETRIEVAL_QUERY（検索時）
- **特徴**: 日本語に最適化、無料枠で開発可能
- **実装**: [src/embedding/store.py](src/embedding/store.py)

```python
import google.generativeai as genai

gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model_name="models/text-embedding-004",
    task_type="RETRIEVAL_DOCUMENT"  # or "RETRIEVAL_QUERY"
)
```

#### 4. ベクトルデータベース
- **DB**: ChromaDB（永続化モード）
- **検索方式**: コサイン類似度
- **インデックス**: HNSW（Hierarchical Navigable Small World）自動最適化
- **実装**: [src/embedding/store.py](src/embedding/store.py)

```python
import chromadb

client = chromadb.PersistentClient(path="storage/chroma")
collection = client.get_or_create_collection(
    name="notebook_rag_collection",
    embedding_function=gemini_ef
)
```

#### 5. 検索手法（Retrieval）

**標準ベクトル検索:**
- Top-K: 3-5件を直接取得
- 処理時間: 50-200ms

**高度な検索（LLMリランキング）:**
```
Step 1: ベクトル検索で広く取得（100件）
         ↓ コサイン類似度による初期フィルタ
Step 2: LLMで関連性を再評価（20件に絞り込み）
         ↓ セマンティック理解による精密評価
Step 3: 最終的に3-5件を使用して回答生成
         ↓ 最も関連性の高いコンテキストのみ使用
```

**実装**: [src/retrieval/reranker.py](src/retrieval/reranker.py)

```python
def rerank_with_llm(query: str, search_results: List[Dict],
                    top_k: int = 20) -> List[Dict]:
    """LLMを使用して検索結果を再評価"""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # LLMに各結果の関連性を評価させる
    prompt = f"""以下の質問に対して、最も関連性の高い文書を選び、
    関連性の高い順に番号で答えてください。

    質問: {query}
    文書一覧: {candidates}

    回答: """

    response = model.generate_content(prompt)
    # 番号を抽出してリランキング
    return reranked_results
```

**リランキングの効果:**
- 検索精度: 約30%向上（主観評価）
- 特に複雑なクエリで効果大
  - 例: 「イエスは心に響く教え方ができました。どうしてですか」
  - 従来: ページ32, 25, 22（無関係）
  - リランキング後: **ページ3**（正解）✅
- コスト増: API呼び出し1回追加（約0.001円/クエリ）

#### 6. 回答生成（Generation）
- **モデル**: Gemini Flash 2.0
- **プロンプト戦略**:
  - ハルシネーション防止の明示的指示
  - ソース引用の強制
  - 日本語回答の最適化
- **実装**: [src/generation/rag.py](src/generation/rag.py)

```python
prompt = f"""
あなたは提供された資料に基づいて質問に答える、誠実で役立つアシスタントです。

【重要な指示】
1. 以下の資料を**すべて注意深く読み**、質問に関連する情報を探してください
2. 回答の根拠となる資料番号を明記してください（例: [資料 1, 3]）
3. 資料に情報が含まれている場合は、必ず具体的に答えてください
4. 本当に情報が見つからない場合のみ「提供された資料にはその情報が含まれていません」と答えてください

【資料】
{context}

【ユーザーの質問】
{query}

【回答】
"""
```

### パフォーマンス指標

| 項目 | 値 | 測定条件 |
|------|-----|---------|
| PDF処理速度 | 10ページ/秒 | PyMuPDF使用、テキストのみ |
| チャンク生成 | 100チャンク/秒 | LangChain使用 |
| 埋め込み生成 | 10チャンク/秒 | Gemini API制限による |
| ベクトル検索 | 50-200ms | ChromaDB、1,000チャンク時 |
| LLMリランキング | 1-2秒 | 100→20件評価時 |
| 回答生成 | 1-3秒 | Gemini Flash、コンテキスト長による |
| メモリ使用量 | 約500MB | 10,000チャンク保存時 |
| ディスク使用量 | 約2MB | 1,000チャンク（ChromaDB） |

### コスト試算（Google Gemini無料枠）

| 項目 | 無料枠 | 本プロジェクトでの消費 | 推定コスト（有料時） |
|------|--------|---------------------|-------------------|
| Embedding API | 1,500リクエスト/日 | 100チャンク = 100リクエスト | 無料 |
| Generation API | 15リクエスト/分 | クエリ1回 = 1-2リクエスト | 無料 |
| Reranking | - | クエリ1回 = 1リクエスト | 無料 |

**開発・検証での推定:**
- PDF 10ファイル処理: 約1,000リクエスト
- クエリ100回テスト: 200リクエスト
- **→ 無料枠内で十分開発可能** ✅

### 実装で工夫した点

#### 1. Windows環境の文字化け対策
```python
# src/retrieval/search.py
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
```
ローカル開発でのストレスを最小化。コンソール出力の文字化けを防止。

#### 2. 起動時の自動クリーンアップ
```python
# app.py
def cleanup_temp_files_on_startup():
    """アプリ起動時に1時間以上前の一時ファイルを削除"""
    current_time = time.time()
    max_age_seconds = 60 * 60  # 1時間

    for pattern in ["tmpclaude-*-cwd", "tmp*-cwd"]:
        for file_path in glob.glob(pattern):
            if current_time - os.path.getmtime(file_path) > max_age_seconds:
                os.remove(file_path)
```
一時ファイルの蓄積を防止し、ディスク容量を節約。

#### 3. 会話履歴の永続化（サーキュラーバッファ）
```python
# src/utils/chat_history.py
class ChatHistoryManager:
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages

    def add_message(self, role: str, content: str):
        messages.append(new_message)
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]  # 古いものを削除
        self.save_history(messages)
```
アプリ再起動後も会話を継続可能。メモリ効率も考慮。

#### 4. 説明可能性（Explainable AI）への対応
- 回答のソース（ページ番号、ファイル名）を明示
- 使用したチャンクをプレビュー表示
- ユーザーが根拠を確認可能
- **信頼性の向上**: ハルシネーション（幻覚）の検証が容易

```python
# app.py - UI実装
with st.expander("📚 参照ソース"):
    for source in response['sources']:
        page, src_file, url, text, chunks = source
        with st.expander(f"🔗 {text}"):
            st.markdown(f"[PDFを開く]({url})")
            st.caption("**参照チャンク:**")
            for idx, chunk in enumerate(chunks, 1):
                st.caption(f"{idx}. {chunk}")
```

#### 5. APIリトライ機能（指数バックオフ）
```python
# src/utils/error_handler.py
class APIRetryHandler:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.backoff_factor ** attempt
                time.sleep(wait_time)
```
ネットワーク不安定時の耐障害性向上。

### スケーラビリティ考慮

**現在の制約（学習・検証用設計）:**
- 単一PDF最大: 10MB
- 同時処理PDF: 制限なし（メモリ次第）
- ベクトルDB: ローカルディスク（ChromaDB）
- 計算リソース: ローカルマシン
- 同時ユーザー: 1名（Streamlitローカル実行）

**本番環境への移行案:**

```python
# 現在（学習・検証用）
vector_store = chromadb.PersistentClient(path="./storage/chroma")

# 本番環境案1: クラウドベクトルDB（スケーラブル）
from pinecone import Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
vector_store = pc.Index("production-rag")

# 本番環境案2: エンタープライズDB（大規模データ）
import weaviate
client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
)
```

**スケーリング時の考慮事項:**

| 項目 | 現在（学習用） | 本番環境案 |
|------|------------|----------|
| ファイルストレージ | ローカルディスク | S3/Google Cloud Storage |
| 非同期処理 | 同期処理 | Celery/AWS Lambda/Cloud Functions |
| キャッシング | なし | Redis/Memcached |
| 負荷分散 | なし | API Gateway + Load Balancer |
| 認証・認可 | なし | OAuth 2.0 / JWT |
| モニタリング | ローカルログ | Datadog/CloudWatch/Prometheus |
| データベース | ChromaDB (SQLite) | Pinecone/Weaviate/Qdrant |

**スケーリング例（1,000ユーザー対応）:**
```python
# Celeryによる非同期PDF処理
from celery import Celery

app = Celery('mini_rag', broker='redis://localhost:6379')

@app.task
def process_pdf_async(pdf_path: str, user_id: str):
    """非同期でPDFを処理"""
    extracted = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(extracted)
    store_embeddings(chunks, collection_name=f"user_{user_id}")
    return {"status": "completed", "chunks": len(chunks)}

# FastAPIによるREST API化
from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post("/api/upload")
async def upload_pdf(file: UploadFile):
    task = process_pdf_async.delay(file.filename, current_user.id)
    return {"task_id": task.id, "status": "processing"}
```

## 前提条件

- Python 3.8以上
- Google Gemini API キー（[Google AI Studio](https://makersuite.google.com/app/apikey)で取得）

## インストール

1. **リポジトリをクローン**

```bash
git clone https://github.com/[your-username]/mini-notebook-rag.git
cd mini-notebook-rag
```

2. **依存関係をインストール**

```bash
pip install -r requirements.txt
```

3. **環境設定**

`.env`ファイルを作成し、Google Gemini APIキーを設定:

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```
GOOGLE_API_KEY=your_api_key_here
```

## 使い方

### オプション A: Streamlit UI（推奨）

1. **Streamlitアプリを起動**

```bash
streamlit run app.py
```

2. **ブラウザでアクセス**

自動的にブラウザが開きます（開かない場合は `http://localhost:8501` にアクセス）

3. **PDFをアップロードして質問**

- サイドバーでPDFファイルを選択
- 「PDFを処理」ボタンをクリック
- 処理完了後、チャット入力欄で質問を入力
- **複数PDFの処理**: 「複数ファイル」モードを選択し、複数のPDFを一括アップロード

### オプション B: コマンドライン（個別モジュール）

各モジュールを個別に実行することも可能です:

```bash
# 1. PDF抽出
python src/ingestion/extract.py

# 2. テキストチャンク化
python src/ingestion/chunking.py

# 3. 埋め込み保存
python src/embedding/store.py

# 4. ベクトル検索（テスト）
python src/retrieval/search.py

# 5. RAG回答生成（テスト）
python src/generation/rag.py
```

## サンプルクエリ

サンプルPDF（宗教教育資料）に基づく質問例:

- "ナアマンについて教えてください"
- "教える技術を磨くにはどうすればいいですか？"
- "エホバを信頼することの大切さについて"
- "忍耐について聖書は何と言っていますか？"

## プロジェクト構造

```
mini-notebook-rag/
├── app.py                      # Streamlit メインアプリケーション
├── requirements.txt            # Python依存関係
├── .env.example               # 環境変数テンプレート
├── .env                       # 環境変数（gitignore）
├── README.md                  # このファイル
│
├── src/                       # ソースコード
│   ├── __init__.py
│   ├── ingestion/            # PDF処理モジュール
│   │   ├── __init__.py
│   │   ├── extract.py        # PDF抽出
│   │   └── chunking.py       # テキストチャンク化
│   ├── embedding/            # 埋め込みモジュール
│   │   ├── __init__.py
│   │   └── store.py          # ChromaDBへの保存
│   ├── retrieval/            # 検索モジュール
│   │   ├── __init__.py
│   │   └── search.py         # ベクトル検索
│   ├── generation/           # 生成モジュール
│   │   ├── __init__.py
│   │   └── rag.py            # RAG回答生成
│   ├── ui/                   # UIモジュール
│   │   ├── __init__.py
│   │   └── streamlit_helpers.py  # Streamlitヘルパー関数
│   └── utils/                # ユーティリティ
│       ├── __init__.py
│       ├── logger.py         # ログ機能
│       ├── error_handler.py  # エラーハンドリング
│       └── chat_history.py   # 会話履歴管理
│
├── data/                      # データディレクトリ
│   ├── raw/                  # 元のPDFファイル
│   └── processed/            # 処理済みJSONファイル
│
├── storage/                   # ストレージ
│   ├── chroma/               # ChromaDB永続化ストレージ
│   └── chat_history.json     # 会話履歴（最大50メッセージ）
│
├── logs/                      # ログファイル
│   └── app_YYYYMMDD.log      # 日付別ログ
│
└── tests/                     # テストコード
    ├── __init__.py
    ├── test_extract.py       # PDF抽出テスト
    ├── test_chunking.py      # チャンク化テスト
    └── test_chat_history.py  # 履歴管理テスト
```

## トラブルシューティング

### よくある問題

**1. `GOOGLE_API_KEY not found` エラー**

- `.env`ファイルが正しく作成されているか確認
- APIキーが正しく設定されているか確認

**2. ChromaDB のエラー**

- Windows環境の場合、`pysqlite3-binary`のインストールが必要な場合があります:
  ```bash
  pip install pysqlite3-binary
  ```

**3. 日本語が文字化けする**

- コンソール出力の場合、コマンドプロンプトのエンコーディングをUTF-8に設定:
  ```bash
  chcp 65001
  ```

**4. API レート制限エラー**

- Gemini APIには無料枠のレート制限があります
- 処理する文書のサイズを小さくするか、時間をおいて再試行してください
- 自動リトライ機能が実装されているため、一時的なエラーは自動的に再試行されます

**5. テストの実行**

```bash
# すべてのテストを実行
python -m unittest discover tests -v

# 特定のテストを実行
python tests/test_chat_history.py
```

**6. 一時ファイルのクリーンアップ**

```bash
# 1時間以上前の一時ファイルを削除
python cleanup_temp.py

# すべての一時ファイルを強制削除
python cleanup_temp.py --force

# 30分以上前のファイルを削除
python cleanup_temp.py --max-age 30
```

**注**: アプリ起動時（`streamlit run app.py`）に、1時間以上前の一時ファイルは自動的に削除されます。

## 新機能の詳細

### 会話履歴の永続化

- チャット履歴は `storage/chat_history.json` に自動保存されます
- 最大50メッセージまで保存され、古いものから自動的に削除されます
- アプリを再起動しても履歴が保持されます

### 複数PDF処理

- 一度に複数のPDFファイルをアップロードして処理できます
- 各ファイルの処理状況が個別に表示されます
- 失敗したファイルは詳細が表示されます

### ログ機能

- すべての操作が `logs/app_YYYYMMDD.log` に記録されます
- エラーの詳細なトラッキングとデバッグ情報
- 日付別にログファイルが自動的に作成されます

### エラーハンドリング

- API呼び出しの自動リトライ（最大3回、指数バックオフ）
- ファイルサイズ制限（10MB）の事前チェック
- ユーザーフレンドリーなエラーメッセージ

## ライセンス

MIT License

Copyright (c) 2026 Hiroshi-Kazui

## 謝辞

このプロジェクトは、LLMとRAGシステムの学習を目的として作成されました。Google NotebookLMにインスパイアされています。
