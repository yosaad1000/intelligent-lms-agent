#!/usr/bin/env python3
"""
Simple HTTP server to serve frontend files for testing
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

def serve_frontend():
    """Serve frontend files on localhost"""
    
    # Change to frontend directory
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    os.chdir(frontend_dir)
    
    # Start HTTP server
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 Serving frontend at http://localhost:{PORT}")
            print(f"📋 Open http://localhost:{PORT}/index.html to test authentication")
            print("🛑 Press Ctrl+C to stop the server")
            
            # Open browser automatically
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    serve_frontend()