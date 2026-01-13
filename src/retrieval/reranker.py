"""
LLMを使用した検索結果のリランキング機能

ベクトル検索で広めに取得した結果から、LLMが質問との関連性を評価し、
最も関連性の高いものを上位に選出します。
"""

import os
from typing import List, Dict, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def rerank_with_llm(
    query: str,
    search_results: List[Dict],
    top_k: int = 20,
    model_name: str = "gemini-2.0-flash-exp"
) -> List[Dict]:
    """
    LLMを使用して検索結果をリランキングする

    Args:
        query: ユーザーの質問
        search_results: ベクトル検索の結果リスト
        top_k: 返す上位件数（デフォルト: 20）
        model_name: 使用するモデル名

    Returns:
        リランキングされた検索結果のリスト（上位top_k件）
    """
    if not search_results:
        return []

    if len(search_results) <= top_k:
        return search_results

    # LLMに渡すプロンプトを構築
    model = genai.GenerativeModel(model_name)

    # 各結果に番号を付けて提示
    candidates_text = "\n\n".join([
        f"[文書{i+1}]\nページ: {result['metadata']['page']}\n内容: {result['content']}"
        for i, result in enumerate(search_results)
    ])

    prompt = f"""以下の質問に対して、提示された文書の中から最も関連性の高いものを選び、関連性の高い順に番号で答えてください。

質問: {query}

文書一覧:
{candidates_text}

回答形式: 関連性の高い順に文書番号をカンマ区切りで列挙してください（例: 3,15,7,22,1）
最大{top_k}件まで選んでください。関連性が低いものは含めないでください。

回答:"""

    try:
        # LLMに評価させる
        response = model.generate_content(prompt)
        ranking_text = response.text.strip()

        # 番号を抽出（カンマ区切り、改行区切りなどに対応）
        import re
        numbers = re.findall(r'\d+', ranking_text)
        ranked_indices = [int(n) - 1 for n in numbers if 0 < int(n) <= len(search_results)]

        # リランキングされた結果を構築
        reranked_results = []
        for idx in ranked_indices[:top_k]:
            if 0 <= idx < len(search_results):
                result = search_results[idx].copy()
                result['rerank_score'] = len(ranked_indices) - ranked_indices.index(idx)
                reranked_results.append(result)

        # LLMが選ばなかった残りを追加（top_kに満たない場合）
        if len(reranked_results) < top_k:
            remaining_indices = [i for i in range(len(search_results)) if i not in ranked_indices]
            for idx in remaining_indices[:top_k - len(reranked_results)]:
                result = search_results[idx].copy()
                result['rerank_score'] = 0
                reranked_results.append(result)

        return reranked_results

    except Exception as e:
        print(f"リランキング中にエラーが発生: {e}")
        print("元の検索結果をそのまま返します")
        return search_results[:top_k]


def evaluate_relevance_batch(
    query: str,
    search_results: List[Dict],
    model_name: str = "gemini-2.0-flash-exp"
) -> List[Tuple[Dict, float]]:
    """
    各検索結果に関連性スコアを付与する（バッチ処理版）

    Args:
        query: ユーザーの質問
        search_results: ベクトル検索の結果リスト
        model_name: 使用するモデル名

    Returns:
        (検索結果, 関連性スコア)のタプルのリスト
    """
    if not search_results:
        return []

    model = genai.GenerativeModel(model_name)

    # 各結果に番号を付けて提示
    candidates_text = "\n\n".join([
        f"[文書{i+1}]\nページ: {result['metadata']['page']}\n内容: {result['content'][:200]}..."
        for i, result in enumerate(search_results)
    ])

    prompt = f"""以下の質問に対して、各文書の関連性を0.0～1.0の数値で評価してください。
1.0は完全に関連している、0.0は全く関連していないことを示します。

質問: {query}

文書一覧:
{candidates_text}

回答形式: 各文書番号とスコアをカンマ区切りで1行ずつ出力してください（例: 1,0.95）

回答:"""

    try:
        response = model.generate_content(prompt)
        score_text = response.text.strip()

        # スコアを抽出
        scored_results = []
        for line in score_text.split('\n'):
            parts = line.strip().split(',')
            if len(parts) == 2:
                try:
                    doc_num = int(parts[0].strip())
                    score = float(parts[1].strip())
                    if 1 <= doc_num <= len(search_results):
                        idx = doc_num - 1
                        scored_results.append((search_results[idx], score))
                except ValueError:
                    continue

        # スコアで降順ソート
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results

    except Exception as e:
        print(f"関連性評価中にエラーが発生: {e}")
        # エラー時は元の順序でスコア1.0を付与
        return [(result, 1.0) for result in search_results]


if __name__ == "__main__":
    # テスト用コード
    from search import semantic_search

    print("=== リランキング機能のテスト ===\n")

    # テストクエリ
    test_queries = [
        "イエスは心に響く教え方ができました。どうしてですか",
        "ナアマンから何を学べますか",
        "エホバを信頼することの大切さ"
    ]

    for query in test_queries:
        print(f"質問: {query}")
        print("-" * 80)

        # 100件取得
        initial_results = semantic_search(query, top_k=100)
        print(f"初期検索結果: {len(initial_results)}件")

        if initial_results:
            print(f"元の上位3件: ページ {initial_results[0]['metadata']['page']}, "
                  f"{initial_results[1]['metadata']['page']}, "
                  f"{initial_results[2]['metadata']['page']}")

        # リランキング（上位20件に絞る）
        reranked_results = rerank_with_llm(query, initial_results, top_k=20)

        print(f"\nリランキング後: {len(reranked_results)}件")
        if reranked_results:
            print(f"リランキング後の上位3件:")
            for i, result in enumerate(reranked_results[:3], 1):
                page = result['metadata']['page']
                content_preview = result['content'][:100].replace('\n', ' ')
                rerank_score = result.get('rerank_score', 'N/A')
                print(f"  {i}. ページ{page} (スコア: {rerank_score})")
                print(f"     {content_preview}...")

        print("\n" + "=" * 80 + "\n")
