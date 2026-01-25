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
    print("Testing with YOUR available models...")
    
    # Based on your output, these models should work for you
    test_models = [
        'gemini-1.5-pro-latest',  # This is available for you
        'gemini-flash-latest',    # This is available for you
        'gemini-2.0-flash-exp',   # Might work despite ResourceExhausted
        'gemini-2.5-flash',       # Try with different approach
    ]
    
    successful_model = None
    
    for model_name in test_models:
        try:
            print(f"\nTrying model: {model_name}")
            
            # Create the model
            model = genai.GenerativeModel(model_name)
            
            # Test with a simple query
            response = model.generate_content("Say 'Hello' in one word")
            
            if response.text:
                print(f"✓ Success! Response: {response.text}")
                successful_model = model_name
                
                # Test with a todo query
                print(f"\nTesting todo query...")
                todo_prompt = f"""You are an AI assistant for a student management system.
                
                User asks: "show todo"
                System has: 5 students and 3 todos
                
                Respond helpfully about how to view todos."""
                
                todo_response = model.generate_content(todo_prompt)
                print(f"Todo response: {todo_response.text[:150]}...")
                break
                
        except Exception as e:
            print(f"✗ Model {model_name} failed: {type(e).__name__}")
            if "ResourceExhausted" in str(e):
                print("  (You may have hit rate limits. Trying next model...)")
            elif "PermissionDenied" in str(e):
                print("  (No access to this model with your API key)")
            continue
    
    if successful_model:
        print(f"\n" + "="*60)
        print(f"✅ SUCCESS! Use this model in your backend: '{successful_model}'")
        print(f"\nTo use it, update your app_with_chatbot.py:")
        print(f'  model = genai.GenerativeModel("{successful_model}")')
        
        # Create a simple test to verify it works with system context
        print(f"\n" + "="*60)
        print("Final test with system context...")
        
        final_model = genai.GenerativeModel(successful_model)
        system_context = """You are an AI assistant for a student management system that handles todos and students. 
        The system allows creating, viewing, updating, and deleting todos. 
        Users can assign todos to students, set priorities (low, medium, high), and track status (todo, in_progress, done)."""
        
        test_queries = [
            "show todo",
            "todo list", 
            "how many todos?",
            "create a new todo"
        ]
        
        for query in test_queries:
            prompt = f"{system_context}\n\nUser asks: '{query}'\n\nRespond as a helpful assistant:"
            response = final_model.generate_content(prompt)
            print(f"\nQuery: '{query}'")
            print(f"Response: {response.text[:100]}...")
            
    else:
        print(f"\n❌ None of the specific models worked.")
        print("\nLet's try the list_models approach to see what's truly available...")
        
        models = genai.list_models()
        print("\nAvailable models with generateContent support:")
        count = 0
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
                count += 1
                if count >= 10:  # Show first 10
                    break
        
        print(f"\nTotal models with generateContent: {count}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")