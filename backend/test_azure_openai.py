#!/usr/bin/env python3
"""
Direct test of Azure OpenAI API
"""

import config
from openai import AzureOpenAI

def test_azure_openai():
    """Test Azure OpenAI API directly"""
    try:
        print("1. Creating Azure OpenAI client...")
        client = AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        print("✓ Azure OpenAI client created")
        
        print("\n2. Testing chat completion...")
        response = client.chat.completions.create(
            model=config.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in one word."}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        print("✓ Chat completion successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Azure OpenAI API...")
    success = test_azure_openai()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
