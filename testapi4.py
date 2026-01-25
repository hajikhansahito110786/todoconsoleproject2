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
    # Configure with API key
    genai.configure(api_key=api_key)
    print("✓ Google Generative AI configured")
    
    print("\n" + "="*60)
    print("Testing FULL model names from your list...")
    
    # Use the EXACT names from your available models list
    test_models = [
        'models/gemini-2.0-flash-lite-001',      # Lite version - more likely to work
        'models/gemini-2.0-flash-lite',          # Another lite version
        'models/gemini-2.0-flash',               # Regular flash
        'models/gemini-2.0-flash-001',           # Specific version
        'models/gemini-2.5-flash',               # Latest version
    ]
    
    successful_model = None
    
    for model_name in test_models:
        try:
            print(f"\nTrying model: {model_name}")
            
            # Create the model
            model = genai.GenerativeModel(model_name)
            
            # Test with a VERY simple query (minimal tokens)
            response = model.generate_content("Hello")
            
            if response.text:
                print(f"✓ Success! Response: {response.text}")
                successful_model = model_name
                
                # Test with a todo query
                print(f"\nTesting todo query...")
                todo_prompt = "User asks: show todo. You are a student management assistant. Respond briefly."
                
                todo_response = model.generate_content(todo_prompt)
                print(f"Todo response: {todo_response.text[:100]}...")
                break
                
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Model {model_name} failed: {type(e).__name__}")
            
            if "PermissionDenied" in error_msg:
                print("  ⚠️ Your API key doesn't have access to this model")
            elif "ResourceExhausted" in error_msg:
                print("  ⚠️ Rate limit exceeded. Waiting 2 seconds...")
                import time
                time.sleep(2)
                # Try one more time with simpler query
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content("Hi")
                    if response.text:
                        print(f"✓ Retry success! Response: {response.text}")
                        successful_model = model_name
                        break
                except:
                    continue
            elif "NotFound" in error_msg:
                print("  ⚠️ Model not found")
            continue
    
    if successful_model:
        print(f"\n" + "="*60)
        print(f"✅ SUCCESS! Use this model: '{successful_model}'")
        
        # Create configuration example
        print(f"\nTo use in your backend:")
        print('```python')
        print('import google.generativeai as genai')
        print(f"genai.configure(api_key='{api_key[:10]}...')")
        print(f'model = genai.GenerativeModel("{successful_model}")')
        print('# ... use model.generate_content(prompt)')
        print('```')
        
    else:
        print(f"\n❌ No models worked with standard approach.")
        print("\nTrying ALTERNATIVE approach: Create content directly...")
        
        # Try creating content directly without specifying model
        try:
            # Let the API choose the model
            response = genai.generate_content(
                "Say hello",
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )
            print(f"✓ Direct generate_content worked! Response: {response.text}")
            print("\n✅ Use: genai.generate_content() without specifying model")
            
        except Exception as e:
            print(f"✗ Direct approach failed: {e}")
            
            print("\n" + "="*60)
            print("FINAL OPTIONS:")
            print("1. Check your Google Cloud Console for API key permissions")
            print("2. Try creating a new API key at: https://makersuite.google.com/app/apikey")
            print("3. Use a fallback rule-based chatbot (no API key needed)")
            print("4. Try a different AI service (OpenAI, Anthropic, or local)")
            
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")