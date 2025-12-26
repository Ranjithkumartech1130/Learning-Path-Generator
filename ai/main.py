import os
import io
import json
import base64
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BugBuster AI Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Models Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD8pxm2qN5_NUrpKEycN5UTywZHnfVLqQY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")

class UserProfile(BaseModel):
    experience_level: str
    skills: List[str]
    learning_goals: List[str]
    interests: List[str]
    time_commitment: str
    learning_style: str
    difficulty_preference: str

class PathRequest(BaseModel):
    user_profile: UserProfile
    goal: str
    additional_skills: Optional[str] = ""
    preferences: Optional[str] = ""
    resume_content: Optional[str] = ""
    use_previous_skills: bool = True

@app.post("/generate-path")
async def generate_path(request: PathRequest):
    try:
        skill_strategy = ("Leverage the user's existing skills to accelerate the path." 
                         if request.use_previous_skills else "Start from foundations.")
        
        prompt = f"""
        Act as a career mentor. Generate a detailed learning path for: {request.goal}

        USER PROFILE:
        - Level: {request.user_profile.experience_level}
        - Skills: {', '.join(request.user_profile.skills)}
        - Strategy: {skill_strategy}

        OUTPUT FORMAT (Markdown):

        ### 📄 Detailed Learning Path
        [Introductory motivational paragraph about their journey to {request.goal}, referencing their current skills]

        ### 📚 Recommended Open Source Resources

        | 🎓 Top Courses | 💻 Practice Platforms | 🤝 Communities |
        | :--- | :--- | :--- |
        | [Course Name](link) | [Platform Name](link) | [Community Name](link) |
        | [Course Name](link) | [Platform Name](link) | [Community Name](link) |
        
        ### 3. OPEN SOURCE LEARNING RESOURCES
        
        *   **Free Online Courses:**
            *   **Topic 1:**
                *   [Resource Name](link) - [Brief description]
                *   [Resource Name](link) - [Brief description]
            *   **Topic 2:**
                *   ...
        
        ### 🚀 Your Personalized Learning Path: Accelerating Towards Mastery
        
        #### 1. OVERVIEW & ASSESSMENT
        *   **Current Skill Assessment:**
            *   **Strengths:** [List strengths]
            *   **Gap Analysis:** [What is missing]

        #### 2. FOUNDATION (Weeks 1-4)
        *   **Focus:** [Topics]
        *   **Action Items:**
            *   [Task 1]
            *   [Task 2]
        
        #### 3. CORE SKILLS (Weeks 5-8)
        *   ...

        #### 4. MASTERY & PROJECTS
        *   ...
        """
        
        response = model.generate_content(prompt)
        return {"success": True, "path": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-flowchart")
async def generate_flowchart(goal: str = "Learning Path"):
    
    # Matplotlib logic from user snippet
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor('#0f172a')
    fig.patch.set_facecolor('#0f172a')
    
    # Draw a winding path
    x = np.linspace(0.1, 0.9, 100)
    y = 0.5 + 0.2 * np.sin(x * 10)
    ax.plot(x, y, color='white', linewidth=4, alpha=0.6)
    
    steps = ["Identify Skills", "Resources", "AI Adoption", "Resume", "Dashboard"]
    colors = ["#3b82f6", "#10b981", "#10b981", "#f59e0b", "#f97316"]
    
    for i, (step, color) in enumerate(zip(steps, colors)):
        px, py = 0.15 + i*0.18, 0.5 + 0.2 * np.sin((0.15 + i*0.18) * 10)
        circle = Circle((px, py), 0.05, color=color, alpha=0.9)
        ax.add_patch(circle)
        ax.text(px, py-0.12, step, color='white', ha='center', fontsize=10, weight='bold')

    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")

@app.post("/generate-resume")
async def generate_resume(request: Dict):
    try:
        user = request.get("user_profile", {})
        goal = request.get("goal", "Software Engineer")
        username = request.get("username", "User")
        email = request.get("email", "user@example.com")
        
        # Extract all user details
        bio = user.get('bio', '')
        experience_level = user.get('experience_level', 'Beginner')
        skills = user.get('skills', [])
        learning_goals = user.get('learning_goals', [])
        interests = user.get('interests', [])
        time_commitment = user.get('time_commitment', '1-5 hours/week')
        learning_style = user.get('learning_style', 'Visual')
        difficulty_preference = user.get('difficulty_preference', 'Beginner-friendly')
        
        prompt = f"""
        Act as an expert resume builder and career counselor. Create a professional, detailed resume for: {username}
        
        COMPLETE USER PROFILE:
        - Name: {username}
        - Email: {email}
        - Target Career Goal: {goal}
        - Experience Level: {experience_level}
        - Professional Bio: {bio if bio else 'Passionate learner dedicated to professional growth'}
        - Current Skills: {', '.join(skills) if skills else 'Building foundational skills'}
        - Learning Goals: {', '.join(learning_goals) if learning_goals else 'Continuous improvement'}
        - Interests: {', '.join(interests) if interests else 'Technology and innovation'}
        - Time Commitment: {time_commitment}
        - Learning Style: {learning_style}
        - Difficulty Preference: {difficulty_preference}

        Generate a comprehensive resume in EXACTLY the following JSON format:
        {{
            "name": "{username}",
            "job_title": "{goal}",
            "summary": "Write a compelling 3-4 sentence professional summary that incorporates their bio, experience level, and career aspirations. Make it personal and specific to their profile.",
            "contact": {{
                "phone": "+1 (555) 123-4567",
                "email": "{email}",
                "location": "Global / Remote",
                "linkedin": "linkedin.com/in/{username.lower().replace(' ', '-')}"
            }},
            "skills": {json.dumps(skills if skills else ["Problem Solving", "Quick Learner", "Team Collaboration"])},
            "experience": [
                {{
                    "title": "Relevant position based on their experience level and skills",
                    "company": "Company Name or 'Self-Directed Learning Projects'",
                    "period": "Recent timeframe",
                    "responsibilities": [
                        "Achievement or responsibility 1 related to their skills",
                        "Achievement or responsibility 2 showcasing growth",
                        "Achievement or responsibility 3 demonstrating impact"
                    ]
                }},
                {{
                    "title": "Another relevant experience or project",
                    "company": "Organization or 'Personal Development'",
                    "period": "Timeframe",
                    "responsibilities": [
                        "Relevant task or achievement",
                        "Another accomplishment"
                    ]
                }}
            ],
            "education": [
                {{
                    "degree": "Relevant degree or certification based on their level",
                    "institution": "University/Institution Name or 'Online Learning Platforms'",
                    "year": "2020-2024"
                }},
                {{
                    "degree": "Additional certification or course",
                    "institution": "Platform name",
                    "year": "2024"
                }}
            ],
            "roadmap": [
                {{
                    "phase": "Foundation Phase (Weeks 1-4)",
                    "courses": ["Specific course 1 for {goal}", "Specific course 2", "Hands-on project 1"]
                }},
                {{
                    "phase": "Intermediate Phase (Weeks 5-8)",
                    "courses": ["Advanced topic 1", "Advanced topic 2", "Real-world project"]
                }},
                {{
                    "phase": "Advanced Phase (Weeks 9-12)",
                    "courses": ["Specialization 1", "Specialization 2", "Portfolio project"]
                }},
                {{
                    "phase": "Mastery Phase (Ongoing)",
                    "courses": ["Industry certifications", "Open-source contributions", "Professional networking"]
                }}
            ],
            "languages": ["English - Fluent", "Add 1-2 more relevant languages"],
            "hobbies": {json.dumps(interests if interests else ["Coding", "Technology", "Continuous Learning"])}
        }}

        IMPORTANT INSTRUCTIONS:
        1. Use ALL the skills provided: {', '.join(skills)}
        2. Incorporate their learning goals: {', '.join(learning_goals)}
        3. Reflect their {experience_level} level throughout
        4. Make the roadmap specific to {goal} with actual course names and technologies
        5. The summary MUST reference their bio and personal background
        6. Experience should align with their current skill set
        7. Make it professional yet personal and authentic
        """
        
        response = model.generate_content(prompt)
        text = response.text
        # Clean up possible markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        resume_data = json.loads(text)
        return {"success": True, "resume": resume_data}
    except Exception as e:
        print(f"Resume generation error: {str(e)}")
        # Return a fallback structured resume with all user details
        return {
            "success": False, 
            "error": str(e),
            "resume": {
                "name": username,
                "job_title": goal,
                "summary": bio if bio else f"Aspiring {goal} with {experience_level.lower()} experience, dedicated to continuous learning and professional growth.",
                "contact": {
                    "phone": "+1 (555) 123-4567", 
                    "email": email, 
                    "location": "Global", 
                    "linkedin": f"linkedin.com/in/{username.lower().replace(' ', '-')}"
                },
                "skills": skills if skills else ["Problem Solving", "Quick Learner"],
                "experience": [
                    {
                        "title": f"{experience_level} Developer",
                        "company": "Self-Directed Learning",
                        "period": "2023 - Present",
                        "responsibilities": [
                            f"Building expertise in {', '.join(skills[:3]) if skills else 'core technologies'}",
                            f"Focused on {', '.join(learning_goals[:2]) if learning_goals else 'professional development'}"
                        ]
                    }
                ],
                "education": [
                    {
                        "degree": "Continuous Learning Program",
                        "institution": "Online Platforms",
                        "year": "2024"
                    }
                ],
                "roadmap": [
                    {
                        "phase": "Foundation",
                        "courses": learning_goals if learning_goals else ["Core Skills Development"]
                    }
                ],
                "languages": ["English - Fluent"],
                "hobbies": interests if interests else ["Technology", "Learning"]
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)