import json
import os
import sys
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Windows環境でのエンコーディングエラー対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def chunk_text(extracted_data: List[Dict], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
    """
    抽出されたテキストをチャンク（断片）に分割します。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "、", " ", ""]
    )
    
    chunks = []
    for item in extracted_data:
        texts = splitter.split_text(item["content"])
        for i, text in enumerate(texts):
            chunks.append({
                "content": text,
                "metadata": {
                    **item["metadata"],
                    "page": item["page"],
                    "chunk_id": i
                }
            })
    return chunks

def save_processed_data(data: List[Dict], output_path: str):
    """
    処理済みデータをJSONファイルとして保存します。
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    from .extract import extract_text_from_pdf
    
    input_dir = "data/raw"
    output_dir = "data/processed"
    files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    
    if not files:
        print("No PDF files found.")
    else:
        for file_name in files:
            pdf_path = os.path.join(input_dir, file_name)
            print(f"Processing: {file_name}")
            
            # テキスト抽出
            extracted_data = extract_text_from_pdf(pdf_path)
            
            # チャンク分割
            chunks = chunk_text(extracted_data)
            print(f"Generated {len(chunks)} chunks.")
            
            # 保存
            output_filename = file_name.replace(".pdf", ".json")
            output_path = os.path.join(output_dir, output_filename)
            save_processed_data(chunks, output_path)
            print(f"Saved to: {output_path}")
