"""
Test script to verify blog generation API keys
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env file
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("API Key Configuration Test")
print("=" * 60)

# Check API keys
gemini_key = os.getenv("GEMINI_API_KEY")
together_key = os.getenv("TOGETHER_API_KEY")
fal_key = os.getenv("FAL_KEY")

print(f"\n✓ GEMINI_API_KEY: {'✅ Found' if gemini_key else '❌ Missing'} ({gemini_key[:20]}... if gemini_key else 'N/A')")
print(f"✓ TOGETHER_API_KEY: {'✅ Found' if together_key else '❌ Missing'} ({together_key[:20]}... if together_key else 'N/A')")
print(f"✓ FAL_KEY: {'✅ Found' if fal_key else '❌ Missing'} ({fal_key[:20]}... if fal_key else 'N/A')")

if not all([gemini_key, together_key, fal_key]):
    print("\n❌ Some API keys are missing!")
    exit(1)

print("\n" + "=" * 60)
print("Testing Gemini API Connection...")
print("=" * 60)

try:
    from google import genai
    client = genai.Client(api_key=gemini_key)
    
    # Test simple generation
    response = client.models.generate_content(
        model='gemini-3-pro-preview',
        contents="Say hello in one word"
    )
    
    print(f"\n✅ Gemini API Test SUCCESSFUL!")
    print(f"Response: {response.text}")
    
except Exception as e:
    import traceback
    print(f"\n❌ Gemini API Test FAILED!")
    print(f"Error: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    print(f"\nThis is likely because:")
    print("  1. Invalid API key")
    print("  2. API key doesn't have permissions")
    print("  3. Network/firewall issue")
    print(f"\nPlease check your GEMINI_API_KEY")

print("\n" + "=" * 60)
