import requests
import json

print("Testing Backend Endpoints")
print("="*60)

# Test 1: Check if backend is running
print("1. Testing backend health...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Backend is running!")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Cannot connect: {e}")

# Test 2: Check correct chat endpoint
print("\n2. Testing chat endpoint...")
try:
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": "show todo"},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response: {data.get('response', 'No response')[:100]}...")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check wrong endpoint (what frontend is calling)
print("\n3. Testing wrong endpoint (v1/chat)...")
try:
    response = requests.post(
        "http://localhost:8000/v1/chat",
        json={"message": "show todo"},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   ❌ Expected: This endpoint doesn't exist (404)")
except Exception as e:
    print(f"   ✅ Correct: This endpoint fails as expected")

print("\n" + "="*60)
print("SUMMARY:")
print("✅ Backend endpoint: http://localhost:8000/chat")
print("❌ Frontend is calling: http://localhost:8000/v1/chat")
print("\nFix the frontend to call the correct URL!")