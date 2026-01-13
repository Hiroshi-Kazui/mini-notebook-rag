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
