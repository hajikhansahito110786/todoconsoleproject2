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
    genai.configure(api_key=api_key)
    print("✓ Google Generative AI configured")
    
    # List available models
    models = genai.list_models()
    print("\nAvailable models:")
    for model in models:
        if 'gemini' in model.name.lower():
            print(f"  - {model.name}")
    
    # Test a simple query
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say hello in one word")
    print(f"\nTest response: {response.text}")
    
except Exception as e:
    print(f"✗ Error: {e}")