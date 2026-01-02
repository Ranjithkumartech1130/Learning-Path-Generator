import google.generativeai as genai
import os
import time

# Explicitly set the NEW key
key = "AIzaSyBcG-Ct_pHaUMhXBOsPvPriFIddPJfVcHI"
genai.configure(api_key=key)

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-2.5-flash"
]

print("Starting model check...")

for model_name in models_to_test:
    print(f"\n--- Testing {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        # Generate a very short response to save tokens
        response = model.generate_content("Hi")
        print(f"SUCCESS: {model_name} looks working!")
        print(f"Response: {response.text}")
        # If we found a working one that is NOT 2.5 (which we know is limited), we prefer it.
        # But we want to see ALL results to make the best choice.
    except Exception as e:
        print(f"FAILED: {model_name}")
        print(f"Error: {e}")
        time.sleep(1) # sleep to avoid rate limiting the check itself
