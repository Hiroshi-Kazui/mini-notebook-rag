"""
PDF配信用の簡易HTTPサーバー
ポート8502でdata/rawディレクトリ内のPDFを配信します
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8503
DIRECTORY = "data/raw"

class PDFHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # CORSヘッダーを追加
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    # ディレクトリが存在することを確認
    os.makedirs(DIRECTORY, exist_ok=True)
    
    with socketserver.TCPServer(("", PORT), PDFHandler) as httpd:
        print(f"📄 PDF配信サーバーを起動しました: http://localhost:{PORT}")
        print(f"📁 配信ディレクトリ: {os.path.abspath(DIRECTORY)}")
        print("Ctrl+C で停止します")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ サーバーを停止しました")
