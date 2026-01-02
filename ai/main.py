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
import textwrap

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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

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

class TaskRequest(BaseModel):
    goal: str
    skills: List[str]
    experience_level: str
    focus_area: Optional[str] = "General"

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

        ### 🚀 Your Personalized Curriculum
        
        [Introductory motivational paragraph about their journey to {request.goal}, referencing their current skills]

        ### 📚 Recommended Open Source Resources
        
        | 🎓 Platform / Course | 🔗 Link | 💡 Why this? |
        | :--- | :--- | :--- |
        | [Name] | [Link] | [Benefit] |
        | [Name] | [Link] | [Benefit] |

        ### 🗂️ Detailed Learning Modules
        
        #### 1. Phase 1: Foundations & Core Concepts
        *   **Focus:** [Topics]
        *   **Key Resources:**
            *   [Resource 1](link) - [Brief description]
            *   [Resource 2](link) - [Brief description]
        
        ### 🚀 Your Personalized Learning Path: Accelerating Towards Mastery
        
        #### 1. OVERVIEW & ASSESSMENT
        *   **Current Skill Assessment:**
            *   **Strengths:** [List strengths]
            *   **Gap Analysis:** [What is missing]

        #### 2. Phase 2: Core Expertise & Integration
        *   **Focus:** [Topics]
        *   **Action Items:**
            *   [Task 1]
            *   [Task 2]
        
        #### 3. Phase 3: Advanced Mastery & Real-world Projects
        *   **Focus:** [Deep dive topics]
        *   **Portfolio Project:** [Detailed project idea]

        #### 🚀 Next Steps: Journey to Success
        *   [Certification recommendation]
        *   [Networking strategy]
        *   [Contribution to Open Source]
        """
        
        response = model.generate_content(prompt)
        return {"success": True, "path": response.text}
    except Exception as e:
        print(f"AI Generation Failed: {e}. Returning fallback content.")
        fallback_path = f"""
        # ⚠️ AI Service Unavailable (Quota Exceeded) - Showing Demo Path for **{request.goal}**

        ### 📄 Detailed Learning Path
        Welcome to your personalized journey to becoming a **{request.goal}**. While our AI brain is taking a nap (rate limited), here is a high-quality standard roadmap to get you started!

        ### 📚 Recommended Open Source Resources

        | 🎓 Top Courses | 💻 Practice Platforms | 🤝 Communities |
        | :--- | :--- | :--- |
        | [CS50: Introduction to Computer Science](https://cs50.harvard.edu/) | [LeetCode](https://leetcode.com/) | [Stack Overflow](https://stackoverflow.com/) |
        | [Full Stack Open](https://fullstackopen.com/) | [FreeCodeCamp](https://www.freecodecamp.org/) | [Reddit r/learnprogramming](https://www.reddit.com/r/learnprogramming/) |

        ### 3. OPEN SOURCE LEARNING RESOURCES

        *   **Free Online Courses:**
            *   **Foundations:**
                *   [The Odin Project](https://www.theodinproject.com/) - Full Stack Curriculum
                *   [MDN Web Docs](https://developer.mozilla.org/) - The Bible of Web Dev
            *   **Advanced:**
                *   [System Design Primer](https://github.com/donnemartin/system-design-primer) - For scaling systems

        ### 🚀 Your Personalized Learning Path: Accelerating Towards Mastery

        #### 1. OVERVIEW & ASSESSMENT
        *   **Current Skill Assessment:**
            *   **Strengths:** Your enthusiasm and starting skills!
            *   **Gap Analysis:** Structured project experience.

        #### 2. FOUNDATION (Weeks 1-4)
        *   **Focus:** Core Languages & Tools
        *   **Action Items:**
            *   Master HTML5, CSS3, and JavaScript logic.
            *   Build a Personal Portfolio Website.
            *   Learn Git & GitHub basics.

        #### 3. CORE SKILLS (Weeks 5-8)
        *   **Focus:** Frameworks & Databases
        *   **Action Items:**
            *   Learn a frontend framework (React, Vue, or Angular).
            *   Build a functional To-Do App with local storage.
            *   Understand REST APIs and JSON.

        #### 4. MASTERY & PROJECTS
        *   **Focus:** Integration & Deployment
        *   **Action Items:**
            *   Build a Full Stack Clone (e.g., Twitter/Netflix clone).
            *   Deploy your apps to Vercel or Netlify.
            *   Contribute to an Open Source project.
        """
        return {"success": True, "path": textwrap.dedent(fallback_path)}

class TaskRequest(BaseModel):
    goal: str
    skills: List[str] = []
    experience_level: str
    focus_area: str
    language: str = "python"

@app.post("/generate-tasks")
async def generate_tasks(request: TaskRequest):
    try:
        prompt = f"""
        Act as a coding interviewer. Create 3 structured coding tasks for a user learning: {request.goal}.
        Focus Area: {request.focus_area}
        User Level: {request.experience_level}
        Current Skills: {', '.join(request.skills)}
        Programming Language: {request.language}

        Output a valid JSON array where each object has:
        - "title": Short title
        - "description": Problem statement
        - "starter_code": Initial code stub (imports, function signature, comments ONLY). DO NOT include the solution logic.
        - "solution": The complete solution code
        - "language": "{request.language}"
        
        Example JSON format:
        [
            {{
                "title": "...",
                "description": "...",
                "starter_code": "...",
                "solution": "...",
                "language": "{request.language}"
            }}
        ]
        """
        response = model.generate_content(prompt)
        text = response.text
        # Clean markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        tasks = json.loads(text)
        return {"success": True, "tasks": tasks}
    except Exception as e:
        print(f"Task generation error: {e}")
        # Fallback task based on language? Defaults to Python for now.
        return {
            "success": True, 
            "tasks": [
                {
                    "title": "Simple Greeting", 
                    "description": f"Write a function that prints 'Hello World' in {request.language}.",
                    "starter_code": "# Write your code here" if request.language == "python" else "// Write your code here",
                    "solution": "print('Hello World')",
                    "language": request.language
                }
            ]
        }

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python" # Added language field

@app.post("/run-code")
async def run_code(request: CodeExecutionRequest):
    """
    Executes code. Currently supports Python (exec) and Node.js (subprocess).
    """
    lang = request.language.lower()
    
    if lang == "python":
        try:
            # Create a buffer to capture stdout
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Execute the code in a restricted namespace
                exec_globals = {"__builtins__": __builtins__}
                try:
                    import pandas as pd
                    import numpy as np
                    exec_globals['pd'] = pd
                    exec_globals['np'] = np
                except:
                    pass
                    
                exec(request.code, exec_globals)
                
            output = f.getvalue()
            return {"success": True, "output": output if output else "Code executed successfully (no output)."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif lang == "javascript":
        try:
            # Run node.js subprocess
            import subprocess
            result = subprocess.run(
                ["node", "-e", request.code], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout if result.stdout else "Code executed successfully (no output)."}
            else:
                 return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": f"Node.js execution failed: {str(e)}"}
            
    elif lang == "sql":
        try:
            import sqlite3
            # Create an in-memory database
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # Allow multiple statements (e.g., CREATE TABLE; INSERT; SELECT)
            # separates statements by semi-colon
            statements = [s for s in request.code.split(';') if s.strip()]
            
            output_buffer = []
            
            for statement in statements:
                try:
                    cursor.execute(statement)
                    if statement.strip().lower().startswith("select"):
                        # Fetch results for SELECT queries
                        rows = cursor.fetchall()
                        # Get column names
                        if cursor.description:
                            columns = [description[0] for description in cursor.description]
                            output_buffer.append(f"Result for: {statement.strip()[:50]}...")
                            output_buffer.append(f"{' | '.join(columns)}")
                            output_buffer.append("-" * 30)
                            for row in rows:
                                output_buffer.append(' | '.join(map(str, row)))
                            output_buffer.append("\n")
                    else:
                        conn.commit()
                        output_buffer.append(f"Executed: {statement.strip()[:50]}... (Rows affected: {cursor.rowcount})")
                except Exception as stmt_err:
                     output_buffer.append(f"Error executing statement '{statement.strip()[:30]}...': {str(stmt_err)}")
            
            conn.close()
            final_output = "\n".join(output_buffer)
            return {"success": True, "output": final_output if final_output else "SQL executed successfully (no text output)."}
            
        except Exception as e:
            return {"success": False, "error": f"SQL execution failed: {str(e)}"}

    else:
        return {"success": False, "error": f"Execution for '{lang}' is not supported in this environment yet. But you can still compile it mentally! 🧠"}

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
            "success": True, 
            "error": None,
            "resume": {
                "name": username,
                "job_title": goal,
                "summary": bio if bio else f"Aspiring {goal} with {experience_level.lower()} experience. [Note: This is a DEMO resume generated because the AI service is currently rate-limited.]",
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