import fitz  # PyMuPDF
import os
import sys
from typing import List, Dict

# Windows環境でのエンコーディングエラー対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def clean_text(text: str) -> str:
    """
    抽出されたテキストから不自然な改行や余分な空白を除去します。
    """
    import re
    
    # 改行を一旦スペースに置換してトリミング
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if cleaned_lines:
            # 前の行の末尾と現在の行の先頭をチェック
            # 日本語（全角文字）同士の結合ならスペースを入れない
            # 英数字が混ざる場合はスペースを入れる等の考慮が必要だが、
            # 基本的には日本語の連続として結合する
            last_char = cleaned_lines[-1][-1]
            first_char = line[0]
            
            # 前の行が文末記号（。！？）で終わっている場合は改行として扱う（新しいラインへ）
            if re.search(r'[。！？]$', cleaned_lines[-1]):
                cleaned_lines.append(line)
            else:
                # 文中改行とみなして結合
                cleaned_lines[-1] += line
        else:
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    PDFからテキストを抽出し、ページごとの構造化データとして返します。
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    extracted_data = []

    for page_num, page in enumerate(doc):
        # ブロック単位でテキストを取得（レイアウト保持のため）
        blocks = page.get_text("blocks")
        # 読み順（上から下、左から右）にある程度ソートされている
        
        page_content = []
        for b in blocks:
            block_text = b[4] # 5番目の要素がテキスト
            if block_text.strip():
                cleaned_block = clean_text(block_text)
                page_content.append(cleaned_block)
        
        full_text = "\n\n".join(page_content)
        
        extracted_data.append({
            "page": page_num + 1,
            "content": full_text.strip(),
            "metadata": {
                "source": os.path.basename(pdf_path),
                "total_pages": len(doc)
            }
        })
    
    doc.close()
    return extracted_data

if __name__ == "__main__":
    # テスト実行用のロジック
    input_dir = "data/raw"
    files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    
    if not files:
        print(f"No PDF files found in {input_dir}. Please place a PDF file there.")
    else:
        sample_pdf = os.path.join(input_dir, files[0])
        print(f"Processing: {sample_pdf}")
        try:
            data = extract_text_from_pdf(sample_pdf)
            for page_data in data:
                print(f"--- Page {page_data['page']} ---")
                print(page_data['content'][:200] + "...") # 先頭200文字を表示
        except Exception as e:
            print(f"Error: {e}")
