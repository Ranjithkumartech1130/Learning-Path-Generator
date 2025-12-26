import google.generativeai as genai
import os

key = "AIzaSyBYy2BK8qZzqIiQGCWZ9gAAm7R8VEdbTyY"
genai.configure(api_key=key)

# Using gemini-2.0-flash as seen in the list
model = genai.GenerativeModel("gemini-flash-latest")

print("Testing gemini-2.0-flash...")
try:
    response = model.generate_content("Hello")
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
