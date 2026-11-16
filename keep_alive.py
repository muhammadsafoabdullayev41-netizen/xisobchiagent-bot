import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

logger = logging.getLogger(__name__)

class SimpleHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Hisobchi Bot 24/7 faol ishlamoqda!")
        
    def log_message(self, format, *args):
        # Keraksiz konsol loglarini kamaytirish
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SimpleHealthHandler)
    logger.info(f"Web server (Render uchun) port {port} da ishga tushdi")
    httpd.serve_forever()

def keep_alive():
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()
