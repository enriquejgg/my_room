
import anthropic

import os
from dotenv import load_dotenv, find_dotenv

# Find and print the exact .env file being loaded
dotenv_path = find_dotenv()
print(f"📁 .env file found at: {dotenv_path}")
print(f"📂 Current working directory: {os.getcwd()}")
print(f"📄 Script location: {os.path.abspath(__file__)}")

# Load it and show the key being used
load_dotenv(dotenv_path)
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"🔑 Key being used: {api_key[:10]}...{api_key[-4:] if api_key else 'NOT FOUND'}")

def test_anthropic_api_key():
    # Load environment variables from .env file
    load_dotenv(override=True)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file.")
        return False

    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Send a minimal test message
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'API key is working!' and nothing else."}
            ]
        )

        response_text = message.content[0].text
        print(f"✅ SUCCESS! Model response: {response_text}")
        print(f"📊 Usage — Input tokens: {message.usage.input_tokens}, Output tokens: {message.usage.output_tokens}")
        return True

    except anthropic.AuthenticationError:
        print("❌ FAILED: Invalid API key. Check your key and try again.")
    except anthropic.PermissionDeniedError:
        print("❌ FAILED: Permission denied. Your key may lack access to this model.")
    except anthropic.RateLimitError:
        print("⚠️  FAILED: Rate limit exceeded. Wait a moment and retry.")
    except anthropic.APIConnectionError:
        print("❌ FAILED: Could not connect to the Anthropic API. Check your internet.")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")

    return False


if __name__ == "__main__":
    test_anthropic_api_key()