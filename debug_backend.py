import requests
import time

print("Debugging Backend Chat Endpoint")
print("="*60)

# Test with shorter timeout
endpoints = [
    ("/chat", 5),
    ("/health", 2),
    ("/status", 2),
    ("/todos/", 5),
    ("/students/", 5)
]

for endpoint, timeout in endpoints:
    print(f"\nTesting: {endpoint} (timeout: {timeout}s)")
    print("-"*40)
    
    try:
        start_time = time.time()
        
        if endpoint == "/chat":
            response = requests.post(
                f"http://localhost:8000{endpoint}",
                json={"message": "hello"},
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
        else:
            response = requests.get(
                f"http://localhost:8000{endpoint}",
                timeout=timeout
            )
        
        elapsed = time.time() - start_time
        print(f"✓ Success in {elapsed:.2f}s")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
            except:
                print(f"  Response: {response.text[:100]}...")
        else:
            print(f"  Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"✗ TIMEOUT after {timeout}s - Endpoint is hanging!")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

print("\n" + "="*60)
print("If /chat times out but others work, the chat endpoint has an issue.")
print("Check if Google Gemini API is taking too long or stuck in a loop.")