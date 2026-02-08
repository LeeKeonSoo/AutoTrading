#!/usr/bin/env python3
"""
Test runner that properly sets up Python path.
Run this from project root: python run_test.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Now we can import from src
    from src.llm.gemini_client import GeminiClient

    print("Testing Gemini Client...")

    try:
        client = GeminiClient()

        if client.test_connection():
            print("✅ Gemini client working!")
        else:
            print("❌ Connection test failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
