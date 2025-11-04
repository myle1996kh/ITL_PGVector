"""
Test OpenRouter API Key Directly

This script tests the OpenRouter API key without database access.
It makes a simple LLM call to verify if the key is valid.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from config import settings


def test_openrouter_api_key():
    """Test OpenRouter API key with a simple LLM call."""

    print("=" * 80)
    print("OpenRouter API Key Test")
    print("=" * 80)

    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"   API Base URL: {settings.OPENROUTER_BASE_URL}")
    print(f"   API Key: {settings.OPENROUTER_API_KEY[:30]}...")
    print(f"   Model: openai/gpt-4o-mini")

    # Create LLM client (same as llm_manager.py does)
    print(f"\n🔧 Creating ChatOpenAI client...")
    try:
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=100,
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": "https://agenthub.local",
                    "X-Title": "AgentHub"
                }
            }
        )
        print(f"✅ Client created successfully")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False

    # Make a simple test call
    print(f"\n🚀 Making test LLM call...")
    print(f"   Query: 'Hello, are you working?'")

    try:
        response = llm.invoke([
            HumanMessage(content="Hello, are you working? Reply with just 'Yes' if you can read this.")
        ])

        print(f"\n✅ SUCCESS! OpenRouter API key is valid!")
        print(f"\n📨 Response:")
        print(f"   {response.content}")

        return True

    except Exception as e:
        error_str = str(e)
        print(f"\n❌ FAILED! OpenRouter API key is invalid")
        print(f"\n🔍 Error Details:")
        print(f"   {error_str}")

        # Parse error for common issues
        if "401" in error_str:
            print(f"\n💡 Analysis:")
            print(f"   HTTP 401 = Authentication Failed")
            if "User not found" in error_str:
                print(f"   → OpenRouter does not recognize this API key")
                print(f"   → The key may be deleted, expired, or never existed")
            else:
                print(f"   → The API key format is invalid")
        elif "403" in error_str:
            print(f"\n💡 Analysis:")
            print(f"   HTTP 403 = Forbidden")
            print(f"   → The API key exists but doesn't have permission for this model")
            print(f"   → Check your OpenRouter account plan/credits")
        elif "429" in error_str:
            print(f"\n💡 Analysis:")
            print(f"   HTTP 429 = Rate Limited")
            print(f"   → Too many requests, wait and retry")
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            print(f"\n💡 Analysis:")
            print(f"   HTTP 5xx = Server Error")
            print(f"   → OpenRouter service issue, not your API key")

        print(f"\n📋 Next Steps:")
        print(f"   1. Visit: https://openrouter.ai/keys")
        print(f"   2. Check if key '{settings.OPENROUTER_API_KEY[:20]}...' exists")
        print(f"   3. If not, create a new API key")
        print(f"   4. Update backend/.env with new key")
        print(f"   5. Run: python update_api_key.py")

        return False


def test_alternative_simple():
    """Simple alternative test using requests library."""
    print(f"\n" + "=" * 80)
    print("Alternative Test: Direct HTTP Request")
    print("=" * 80)

    try:
        import requests

        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agenthub.local",
            "X-Title": "AgentHub"
        }
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "Say 'test' if you receive this"}
            ],
            "max_tokens": 10
        }

        print(f"\n📤 Sending POST request to:")
        print(f"   {url}")
        print(f"   Authorization: Bearer {settings.OPENROUTER_API_KEY[:30]}...")

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Body: {response.text[:500]}")

        if response.status_code == 200:
            print(f"\n✅ API key is valid!")
            data = response.json()
            if "choices" in data:
                print(f"   LLM Response: {data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"\n❌ API key is invalid!")
            return False

    except ImportError:
        print(f"\n⚠️  'requests' library not installed, skipping alternative test")
        return None
    except Exception as e:
        print(f"\n❌ Alternative test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n")

    # Test 1: Using LangChain (same as production code)
    test1_result = test_openrouter_api_key()

    # Test 2: Direct HTTP request (backup verification)
    test2_result = test_alternative_simple()

    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test 1 (LangChain): {'✅ PASSED' if test1_result else '❌ FAILED'}")
    if test2_result is not None:
        print(f"Test 2 (Direct HTTP): {'✅ PASSED' if test2_result else '❌ FAILED'}")

    if test1_result:
        print(f"\n🎉 Your OpenRouter API key is working correctly!")
        print(f"   The issue with AgentHub is likely something else.")
    else:
        print(f"\n🔴 Your OpenRouter API key is NOT working!")
        print(f"   This is why AgentHub fails with 401 errors.")
        print(f"\n   Get a new key from: https://openrouter.ai/keys")

    sys.exit(0 if test1_result else 1)
