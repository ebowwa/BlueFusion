#!/usr/bin/env python3
"""
Test frontend-backend communication
"""
import requests
import json

print("Testing BlueFusion Frontend-Backend Communication")
print("=" * 50)

# Test 1: API Status
print("\n1. Testing API Status...")
try:
    response = requests.get("http://localhost:8000/")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: CORS Headers
print("\n2. Testing CORS Headers...")
try:
    response = requests.options("http://localhost:8000/devices", 
                              headers={"Origin": "http://localhost:7860"})
    print(f"   Status Code: {response.status_code}")
    print(f"   CORS Headers:")
    for header in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
        print(f"     {header}: {response.headers.get(header, 'Not set')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Start Scanning
print("\n3. Testing Start Scan...")
try:
    response = requests.post("http://localhost:8000/scan/start",
                           json={"interface": "both", "mode": "active"},
                           headers={"Origin": "http://localhost:7860"})
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Get Devices
print("\n4. Testing Get Devices...")
try:
    response = requests.get("http://localhost:8000/devices?interface=both",
                          headers={"Origin": "http://localhost:7860"})
    print(f"   Status Code: {response.status_code}")
    device_data = response.json()
    macbook_count = len(device_data.get('macbook', []))
    sniffer_count = len(device_data.get('sniffer', []))
    print(f"   MacBook devices: {macbook_count}")
    print(f"   Sniffer devices: {sniffer_count}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("If all tests pass, the frontend should be able to communicate with the backend!")
print("\nTo use the UI:")
print("1. Open http://localhost:7860")
print("2. Go to Control tab -> Start Scan")
print("3. Go to Devices tab -> Refresh Devices")
print("4. Go to Service Explorer -> Refresh Device List")