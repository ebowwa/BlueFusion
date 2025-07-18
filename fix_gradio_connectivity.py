#!/usr/bin/env python3
"""
Fix script to update URLs and improve connectivity between Gradio and FastAPI
"""
import os
import sys

def update_file_urls():
    """Update URLs to use 127.0.0.1 instead of localhost for better compatibility"""
    
    replacements = [
        ("src/ui/data_models.py", [
            ('API_BASE = "http://localhost:8000"', 'API_BASE = "http://127.0.0.1:8000"'),
            ('WS_URL = "ws://localhost:8000/stream"', 'WS_URL = "ws://127.0.0.1:8000/stream"')
        ]),
        ("src/ui/client.py", [
            ('def __init__(self, base_url: str = "http://localhost:8000"):', 
             'def __init__(self, base_url: str = "http://127.0.0.1:8000"):')
        ]),
        ("src/ui/websocket_handler.py", [
            ('def __init__(self, ws_url: str = "ws://localhost:8000/stream"):', 
             'def __init__(self, ws_url: str = "ws://127.0.0.1:8000/stream"):')
        ])
    ]
    
    for file_path, changes in replacements:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"Updating {file_path}...")
            with open(full_path, 'r') as f:
                content = f.read()
            
            for old, new in changes:
                if old in content:
                    content = content.replace(old, new)
                    print(f"  ✓ Replaced: {old} -> {new}")
            
            with open(full_path, 'w') as f:
                f.write(content)
        else:
            print(f"  ⚠️  File not found: {file_path}")

def create_test_html():
    """Create a simple HTML file to test CORS directly"""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>BlueFusion CORS Test</title>
</head>
<body>
    <h1>BlueFusion CORS Test</h1>
    <button onclick="testAPI()">Test API Connection</button>
    <button onclick="testWebSocket()">Test WebSocket</button>
    <div id="results"></div>
    
    <script>
        const API_URL = 'http://127.0.0.1:8000';
        const WS_URL = 'ws://127.0.0.1:8000/stream';
        
        function log(message) {
            const results = document.getElementById('results');
            results.innerHTML += '<p>' + message + '</p>';
        }
        
        async function testAPI() {
            log('Testing API connection...');
            try {
                const response = await fetch(API_URL + '/');
                const data = await response.json();
                log('✅ API Connected: ' + JSON.stringify(data));
                
                // Test CORS with POST
                const scanResponse = await fetch(API_URL + '/scan/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({interface: 'both', mode: 'active'})
                });
                const scanData = await scanResponse.json();
                log('✅ CORS POST successful: ' + JSON.stringify(scanData));
            } catch (error) {
                log('❌ API Error: ' + error.message);
            }
        }
        
        function testWebSocket() {
            log('Testing WebSocket connection...');
            const ws = new WebSocket(WS_URL);
            
            ws.onopen = () => {
                log('✅ WebSocket connected');
            };
            
            ws.onerror = (error) => {
                log('❌ WebSocket error: ' + error);
            };
            
            ws.onmessage = (event) => {
                log('📨 WebSocket message: ' + event.data);
            };
            
            ws.onclose = () => {
                log('WebSocket closed');
            };
        }
    </script>
</body>
</html>"""
    
    test_file = os.path.join(os.path.dirname(__file__), "test_cors.html")
    with open(test_file, 'w') as f:
        f.write(html_content)
    print(f"\nCreated test file: {test_file}")
    print("Open this file in your browser to test CORS directly")

def main():
    print("=== BlueFusion Connectivity Fix ===\n")
    
    # Update URLs
    print("1. Updating URLs to use 127.0.0.1 instead of localhost...")
    update_file_urls()
    
    # Create test file
    print("\n2. Creating CORS test file...")
    create_test_html()
    
    print("\n=== Fix Applied ===")
    print("\nNext steps:")
    print("1. Restart the FastAPI server")
    print("2. Restart the Gradio interface")
    print("3. Open test_cors.html in your browser to verify CORS")
    print("4. If issues persist, check firewall/antivirus settings")

if __name__ == "__main__":
    main()