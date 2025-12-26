import requests
import json

try:
    data = {
        "user_profile": {
            "experience_level": "Beginner",
            "skills": ["python"],
            "learning_goals": ["web dev"],
            "interests": ["coding"],
            "time_commitment": "5 hours",
            "learning_style": "text",
            "difficulty_preference": "easy"
        },
        "goal": "Become a Web Developer"
    }
    print("Sending request to http://127.0.0.1:8001/generate-path...")
    response = requests.post("http://127.0.0.1:8001/generate-path", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
