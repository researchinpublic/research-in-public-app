"""Run the Streamlit web application."""

import subprocess
import sys
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables from .env file first
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ Warning: GEMINI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment variables.")
        print("\nTo set it:")
        print("  export GEMINI_API_KEY='your_key_here'  # Linux/Mac")
        print("  $env:GEMINI_API_KEY='your_key_here'    # Windows PowerShell")
        print("  or create a .env file with: GEMINI_API_KEY=your_key_here")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/main.py"])

