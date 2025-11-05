#!/usr/bin/env python3
"""
Simple HTTP server to serve the test interface
"""

import http.server
import socketserver
import webbrowser
import os

def serve_interface():
    """Serve the test interface on localhost"""
    
    PORT = 8000
    
    # Change to current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create server
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Serving RAG Chat Test Interface")
        print(f"📍 URL: http://localhost:{PORT}/test_interface.html")
        print(f"🚀 Opening browser...")
        
        # Open browser
        webbrowser.open(f'http://localhost:{PORT}/test_interface.html')
        
        print(f"🔄 Server running on port {PORT}")
        print(f"📋 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped")

if __name__ == "__main__":
    serve_interface()