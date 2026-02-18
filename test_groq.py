"""
Test script to verify Groq API connection with Llama 3.2 1B.
"""
import os
from langchain_groq import ChatGroq


def test_groq_connection():
    """Test connection to Groq API."""
    
    print("="*80)
    print("Testing Groq API with Llama 3.2 1B")
    print("="*80)
    
    # Check for API key
   
   
api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set!")
        print("Please set it with: set GROQ_API_KEY=your_api_key_here")
        return False
    
    print(f"\n✅ API key found: {api_key[:10]}...")
    
    # Initialize LLM
    print("\n[Test 1] Initializing ChatGroq with llama-3.2-1b-preview...")
    try:
        llm = ChatGroq(
            model="llama-3.2-1b-preview",
            api_key=api_key,
            temperature=0.7
        )
        print("✅ LLM initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        return False
    
    # Test simple inference
    print("\n[Test 2] Testing simple inference...")
    try:
        response = llm.invoke("Say hello in one sentence.")
        print(f"✅ Inference successful!")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return False
    
    # Test with messages
    print("\n[Test 3] Testing with chat messages...")
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content="You are a helpful fitness assistant."),
            HumanMessage(content="What is the best exercise for chest?")
        ]
        response = llm.invoke(messages)
        print(f"✅ Chat inference successful!")
        print(f"Response: {response.content[:200]}...")
    except Exception as e:
        print(f"❌ Chat inference failed: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ All tests passed! Groq API is working correctly.")
    print("="*80)
    return True


if __name__ == "__main__":
    test_groq_connection()
