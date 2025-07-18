#!/usr/bin/env python3
"""
Debug script to test CORS and connectivity between Gradio and FastAPI
"""
import requests
import asyncio
import websockets
import json

def test_api_connection():
    """Test basic API connectivity"""
    print("Testing API connection...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ API Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        return False
    return True

def test_cors_headers():
    """Test CORS headers"""
    print("\nTesting CORS headers...")
    try:
        # Simulate a browser request with Origin header
        headers = {
            "Origin": "http://localhost:7860",
            "Content-Type": "application/json"
        }
        response = requests.options("http://localhost:8000/scan/start", headers=headers)
        print(f"✅ CORS Preflight Status: {response.status_code}")
        print("CORS Headers:")
        for header, value in response.headers.items():
            if "access-control" in header.lower():
                print(f"  {header}: {value}")
    except Exception as e:
        print(f"❌ CORS Test Failed: {e}")

def test_scan_endpoint():
    """Test scan endpoint with proper headers"""
    print("\nTesting scan endpoint...")
    try:
        headers = {
            "Origin": "http://localhost:7860",
            "Content-Type": "application/json"
        }
        data = {"interface": "both", "mode": "active"}
        response = requests.post("http://localhost:8000/scan/start", 
                               json=data, 
                               headers=headers)
        print(f"✅ Scan Start Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Scan Test Failed: {e}")

async def test_websocket():
    """Test WebSocket connection"""
    print("\nTesting WebSocket connection...")
    try:
        uri = "ws://localhost:8000/stream"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            # Try to receive a message (with timeout)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"Received: {message}")
            except asyncio.TimeoutError:
                print("No messages received (timeout) - this is normal if no scanning is active")
    except Exception as e:
        print(f"❌ WebSocket Connection Failed: {e}")

def main():
    print("=== BlueFusion CORS Debug Tool ===\n")
    
    # Test API connection
    if not test_api_connection():
        print("\n⚠️  Please ensure the FastAPI server is running:")
        print("   cd src/api && python fastapi_server.py")
        return
    
    # Test CORS
    test_cors_headers()
    
    # Test endpoints
    test_scan_endpoint()
    
    # Test WebSocket
    asyncio.run(test_websocket())
    
    print("\n=== Debug Complete ===")
    print("\nIf all tests passed but Gradio still has issues:")
    print("1. Clear browser cache and cookies")
    print("2. Try using 127.0.0.1 instead of localhost")
    print("3. Check browser console for specific errors")
    print("4. Ensure no browser extensions are blocking requests")

if __name__ == "__main__":
    main()