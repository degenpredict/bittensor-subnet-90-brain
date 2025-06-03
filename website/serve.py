#!/usr/bin/env python3
"""
Simple HTTP server to preview the website locally.
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

print(f"""
╔════════════════════════════════════════════════════════════════╗
║              Subnet 90 Website Preview Server                  ║
╚════════════════════════════════════════════════════════════════╝

Starting local server at: http://localhost:{PORT}
Press Ctrl+C to stop the server.
""")

# Change to website directory
os.chdir(DIRECTORY)

# Start server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    # Try to open browser
    try:
        webbrowser.open(f'http://localhost:{PORT}')
        print(f"✅ Browser opened automatically")
    except:
        print(f"📌 Please open http://localhost:{PORT} in your browser")
    
    print("\n🚀 Server running...\n")
    httpd.serve_forever()