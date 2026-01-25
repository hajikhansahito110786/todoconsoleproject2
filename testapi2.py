import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Test Google API key
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"Key starts with: {api_key[:10]}...")

try:
    # Configure with API key and options
    genai.configure(
        api_key=api_key,
        # Optional: Uncomment if you need specific configuration
        # transport='rest',  # or 'grpc' or 'grpc_asyncio'
        # client_options={
        #     'api_endpoint': 'https://generativelanguage.googleapis.com/v1beta'
        # }
    )
    print("✓ Google Generative AI configured")
    
    # List available models
    print("\nFetching available models...")
    models = genai.list_models()
    
    # Filter for generate_content capable models
    print("\nModels that support generate_content:")
    gemini_models = []
    for model in models:
        if 'gemini' in model.name.lower():
            supported_methods = model.supported_generation_methods
            if 'generateContent' in supported_methods:
                gemini_models.append(model.name)
                print(f"  - {model.name}")
    
    # Test different models in order
    test_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-001',
        'gemini-2.0-flash-exp',
        'gemini-2.0-flash',
        'gemini-2.0-flash-001',
        'gemini-2.5-flash',
        'models/gemini-1.5-flash',
        'models/gemini-2.0-flash',
    ]
    
    print("\n" + "="*60)
    print("Testing models...")
    
    successful_model = None
    for model_name in test_models:
        try:
            print(f"\nTrying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Test with a simple query
            response = model.generate_content("Say 'Hello' in one word")
            
            if response.text:
                print(f"✓ Success! Response: {response.text}")
                successful_model = model_name
                
                # Test with a todo query
                print(f"\nTesting todo query with {model_name}...")
                todo_response = model.generate_content(
                    "You are a student management system assistant. User asks: 'show todo'. Respond helpfully."
                )
                print(f"Todo response: {todo_response.text[:100]}...")
                break
                
        except Exception as e:
            print(f"✗ Model {model_name} failed: {type(e).__name__}")
            continue
    
    if successful_model:
        print(f"\n✅ Recommended model to use: {successful_model}")
    else:
        print("\n❌ No models worked. Trying direct API call...")
        
        # Try direct API call
        import requests
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
        }
        params = {
            'key': api_key
        }
        data = {
            "contents": [{
                "parts": [{
                    "text": "Say hello in one word"
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, params=params, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"Direct API success: {result}")
        else:
            print(f"Direct API failed: {response.status_code} - {response.text}")
    
except ImportError:
    print("✗ google-generativeai package not installed")
    print("Install with: pip install google-generativeai")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try with older API version
    print("\nTrying with explicit client configuration...")
    try:
        import google.ai.generativelanguage as glm
        from google.api_core import client_options
        
        client_options = client_options.ClientOptions(
            api_endpoint="https://generativelanguage.googleapis.com/v1beta"
        )
        
        client = genai.Client(
            api_key=api_key,
            client_options=client_options
        )
        
        print("✓ Created client with custom endpoint")
        model = client.get_model('models/gemini-1.5-flash')
        print(f"✓ Got model: {model.name}")
        
    except Exception as e2:
        print(f"✗ Client configuration also failed: {e2}")