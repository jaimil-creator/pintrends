import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Test different Gemini models
models_to_test = [
    "gemini-3-pro-preview",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

for model_name in models_to_test:
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print('='*60)
    
    try:
        # Test with system role (Gemini 3 style)
        contents = [
            types.Content(
                role="system",
                parts=[types.Part.from_text(text="You are a helpful assistant.")],
            ),
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Say hello")],
            ),
        ]
        
        config = types.GenerateContentConfig()
        
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        
        print(f"✅ SUCCESS with system role!")
        print(f"Response: {response.text[:100]}")
        
    except Exception as e:
        print(f"❌ FAILED with system role: {e}")
        
        # Try without system role (older Gemini style)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello"
            )
            print(f"✅ SUCCESS without system role!")
            print(f"Response: {response.text[:100]}")
        except Exception as e2:
            print(f"❌ FAILED without system role too: {e2}")
