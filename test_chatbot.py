import requests
import json

# Test the chatbot endpoint
def test_chatbot():
    url = "http://localhost:8000/chat"
    
    # Test message
    test_messages = [
        "Hello, how can you help me?",
        "How do I create a new todo?",
        "Show me my tasks",
        "What can you do?"
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing the chatbot endpoint...\n")
    
    for msg in test_messages:
        payload = {
            "message": msg,
            "user_id": 1
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Input: {msg}")
            print(f"Response: {response.json()['response']}\n")
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to the server. Please make sure the application is running on http://localhost:8000")
            break
        except Exception as e:
            print(f"Error testing message '{msg}': {e}\n")

if __name__ == "__main__":
    test_chatbot()