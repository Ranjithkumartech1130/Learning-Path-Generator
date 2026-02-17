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
import subprocess

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# AI Models Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
        skill_strategy = ("Leveraging your existing expertise to fast-track your progress." 
                         if request.use_previous_skills else "Starting from foundational principles for a solid base.")
        
        prompt = f"""
        Act as a Principal Engineer and Career Architect. Generate a RIGOROUSLY ACCURATE and hyper-specific learning path for becoming a: {request.goal}

        USER CONTEXT:
        - Experience Level: {request.user_profile.experience_level}
        - Current Skills: {', '.join(request.user_profile.skills)}
        - Learning Strategy: {skill_strategy}

        CRITICAL REQUIREMENTS:
        1. You MUST provide SPECIFIC, REAL URLs - no generic Google/YouTube search links
        2. Include actual course names, GitHub repositories, official documentation sites
        3. For {request.goal}, research and provide the TOP industry-standard resources
        4. Include at least 8-10 specific resources in the Global Master Resources table
        5. Each learning phase should have 5-7 specific, clickable resources with real URLs
        6. Add specialized learning tracks if relevant to {request.goal}
        7. Include practice platforms, communities, and career resources specific to {request.goal}

        EXAMPLES OF GOOD RESOURCES (adapt to {request.goal}):
        - For ML: Coursera ML Specialization, Fast.ai, Kaggle, Papers with Code, scikit-learn docs
        - For Web Dev: MDN Web Docs, FreeCodeCamp, The Odin Project, web.dev, specific framework docs
        - For Data Science: Kaggle Learn, DataCamp, Mode Analytics SQL Tutorial, Pandas docs
        - For Cloud: AWS/GCP/Azure official tutorials, Cloud Academy, A Cloud Guru
        
        OUTPUT FORMAT (Markdown) - FOLLOW THIS EXACT STRUCTURE:

        ### 🚀 Your Personalized Curriculum: {request.goal}
        
        [Write a motivational 2-3 sentence intro referencing their {request.user_profile.experience_level} level and how this path will accelerate their journey to {request.goal}]

        ### 📚 Essential {request.goal} Resources
        
        | 🎓 Resource / Course | 🔗 Direct Link | 💡 Why This Matters |
        | :--- | :--- | :--- |
        | **[Specific Course/Platform Name]** | [Real URL with https://] | [Specific benefit for {request.goal}] |
        | **[Another Specific Resource]** | [Real URL] | [Why it's essential] |
        | **[GitHub Repo or Tool]** | [Real URL] | [What you'll learn] |
        [Continue with 8-10 total resources - ALL with real, working URLs]

        ### 🗂️ Detailed Learning Modules
        
        #### 1. Phase 1: Foundations & Core Concepts (Weeks 1-8)
        *   **Focus:** [Specific foundational topics for {request.goal}]
        *   **📖 Key Resources:**
            *   [Specific Resource Name](https://real-url.com) - Detailed explanation of why needed
            *   [Another Resource](https://real-url.com) - What you'll learn from this
            *   [Third Resource](https://real-url.com) - How it builds your foundation
            *   [Fourth Resource](https://real-url.com) - Practical application
            *   [Fifth Resource](https://real-url.com) - Additional context
        *   **🏁 Milestone Project:** [Specific project idea with technologies to use]
        
        #### 2. Phase 2: Core Expertise & Advanced Skills (Weeks 9-16)
        *   **Focus:** [Intermediate to advanced {request.goal} concepts]
        *   **📖 Key Resources:**
            *   [Specific Resource](https://real-url.com) - Why this matters for Phase 2
            *   [Another Resource](https://real-url.com) - Advanced concepts covered
            *   [Third Resource](https://real-url.com) - Practical implementation
            *   [Fourth Resource](https://real-url.com) - Industry best practices
            *   [Fifth Resource](https://real-url.com) - Real-world applications
        *   **🏁 Milestone Project:** [More complex project description]

        #### 3. Phase 3: Advanced Mastery & Specialization (Weeks 17-24)
        *   **Focus:** [Production-level skills and specializations for {request.goal}]
        *   **📖 Key Resources:**
            *   [Advanced Resource](https://real-url.com) - Expert-level content
            *   [Specialization Resource](https://real-url.com) - Deep dive topic
            *   [Production Resource](https://real-url.com) - Deployment and scaling
            *   [Best Practices](https://real-url.com) - Industry standards
            *   [Advanced Tool](https://real-url.com) - Professional workflows
        *   **🏁 Capstone Project:** [Comprehensive project that demonstrates mastery]

        ### 🎯 Specialized Learning Paths
        [If relevant to {request.goal}, add 2-3 specialization tracks with specific resources]
        
        ### 🛠️ Essential Tools & Frameworks
        [Table of specific tools for {request.goal} with real URLs]
        
        ### 📊 Practice Platforms & Communities
        *   **[Platform Name](real-url)** - What you can practice here
        *   **[Community Name](real-url)** - Why join this community
        *   **[Competition Platform](real-url)** - How to gain experience
        [Add 5-8 specific platforms]

        ### 🎓 Top Courses & Certifications
        *   **[Specific Course Name](real-url)** - Institution/Platform
        *   **[Certification Name](real-url)** - Why it matters
        [Add 4-6 specific courses]

        ### 🚀 Next Steps: Your Journey to {request.goal} Mastery
        
        1. **Week 1-2:** [Specific actionable steps]
        2. **Week 3-4:** [Specific learning goals]
        3. **Week 5-8:** [Specific milestones]
        [Continue with 8-week breakdown]
        
        ### 📚 Recommended Books
        *   **"[Actual Book Title]" by [Author]** - Why read this
        [Add 3-5 real books]
        
        ### 🎯 Career Resources
        *   **[Interview Prep Resource](real-url)** - Description
        *   **[Job Board](real-url)** - Where to find {request.goal} jobs
        [Add 3-5 career resources]

        FINAL CHECK: Every resource MUST have a real, specific URL. No placeholders, no generic search links!
        """
        
        response = model.generate_content(prompt)
        return {"success": True, "path": response.text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"AI Generation Failed: {e}. Returning fallback content.")
        print(f"Goal: {request.goal}, Level: {request.user_profile.experience_level}")
        
        # Dynamic fallback based on goal
        goal_lower = request.goal.lower()
        
        # Determine which fallback to use
        if any(keyword in goal_lower for keyword in ['machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence']):
            fallback_path = generate_ml_fallback(request.goal)
        elif any(keyword in goal_lower for keyword in ['data analyst', 'data analysis', 'data science', 'analytics']):
            fallback_path = generate_data_analyst_fallback(request.goal)
        elif any(keyword in goal_lower for keyword in ['web dev', 'frontend', 'backend', 'full stack', 'react', 'javascript']):
            fallback_path = generate_webdev_fallback(request.goal)
        else:
            # Generic comprehensive fallback
            fallback_path = generate_generic_fallback(request.goal)
        
        return {"success": True, "path": fallback_path, "is_fallback": True}

def generate_ml_fallback(goal):
    return f"""
# 🚀 Your Personalized Curriculum: {goal}

> 💡 **AI Assistant Note:** Our AI is currently at capacity, but we've prepared a comprehensive, curated learning path just for you!

---

## 📚 **Essential Machine Learning & AI Resources**

| 🎓 **Platform / Course** | 🔗 **Link** | 💡 **Why This Matters** |
| :--- | :--- | :--- |
| **🏆 Andrew Ng's ML Course** | [Coursera ML Specialization](https://www.coursera.org/specializations/machine-learning-introduction) | The gold standard for ML beginners - comprehensive and well-structured |
| **⚡ Fast.ai** | [Practical Deep Learning](https://course.fast.ai/) | Top-down approach - build real projects from day 1 |
| **🎯 Google ML Crash Course** | [Google Developers](https://developers.google.com/machine-learning/crash-course) | Free, interactive, with TensorFlow tutorials |
| **📊 Scikit-learn Docs** | [scikit-learn.org](https://scikit-learn.org/stable/tutorial/index.html) | Best resource for classical ML algorithms |
| **🧠 Deep Learning Specialization** | [Coursera Deep Learning](https://www.coursera.org/specializations/deep-learning) | Advanced neural networks by Andrew Ng |
| **🏅 Kaggle Learn** | [kaggle.com/learn](https://www.kaggle.com/learn) | Hands-on micro-courses with real datasets |
| **⭐ Awesome Machine Learning** | [GitHub Awesome ML](https://github.com/josephmisiti/awesome-machine-learning) | Curated list of ML frameworks and libraries |
| **📄 Papers With Code** | [paperswithcode.com](https://paperswithcode.com/) | Latest ML research with implementation code |

---

## 🗂️ **Detailed Learning Modules**

### 📘 **Phase 1: Foundations & Core Concepts** (Weeks 1-8)

**🎯 Focus:** Mathematics, Python, and Classical ML Algorithms

**📖 Key Resources:**
- 🐍 **[Python for Data Science](https://www.kaggle.com/learn/python)** - Master Python basics with interactive exercises
- 🔢 **[NumPy Tutorial](https://numpy.org/doc/stable/user/quickstart.html)** - Essential for numerical computing
- 🐼 **[Pandas Documentation](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html)** - Data manipulation fundamentals
- 📐 **[Khan Academy Linear Algebra](https://www.khanacademy.org/math/linear-algebra)** - Math foundations made easy
- 🎨 **[3Blue1Brown Neural Networks](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)** - Visual intuition for ML concepts
- 📊 **[StatQuest ML Playlist](https://www.youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF)** - Statistics made simple and fun

**🏁 Milestone Project:** Build a house price predictor using linear regression
        
---

### 📗 **Phase 2: Core Expertise & Deep Learning** (Weeks 9-16)

**🎯 Focus:** Neural Networks, TensorFlow/PyTorch, Computer Vision & NLP

**📖 Key Resources:**
- 🔥 **[TensorFlow Tutorials](https://www.tensorflow.org/tutorials)** - Official TensorFlow guides
- ⚡ **[PyTorch Tutorials](https://pytorch.org/tutorials/)** - Official PyTorch learning path
- 👁️ **[CS231n Stanford CNN Course](http://cs231n.stanford.edu/)** - Computer vision fundamentals
- 💬 **[CS224n Stanford NLP Course](http://web.stanford.edu/class/cs224n/)** - Natural language processing
- 🤗 **[Hugging Face Course](https://huggingface.co/learn/nlp-course/chapter1/1)** - Modern NLP with transformers
- 📚 **[Deep Learning Book](https://www.deeplearningbook.org/)** - Comprehensive theory by Ian Goodfellow
- ✨ **[Distill.pub](https://distill.pub/)** - Beautiful ML explanations

**🏁 Milestone Project:** Build an image classifier or sentiment analysis model
        
---

### 📙 **Phase 3: Advanced Mastery & Specialization** (Weeks 17-24)

**🎯 Focus:** MLOps, Production Deployment, Advanced Architectures

**📖 Key Resources:**
- 🚀 **[Full Stack Deep Learning](https://fullstackdeeplearning.com/)** - Production ML systems
- ⚙️ **[MLOps Guide](https://ml-ops.org/)** - Best practices for ML operations
- 🔧 **[TensorFlow Extended (TFX)](https://www.tensorflow.org/tfx/guide)** - End-to-end ML pipelines
- 📊 **[MLflow Documentation](https://mlflow.org/docs/latest/index.html)** - Experiment tracking and deployment
- 📈 **[Weights & Biases Tutorials](https://docs.wandb.ai/tutorials)** - ML experiment management
- 🐳 **[Docker for ML](https://docs.docker.com/get-started/)** - Containerization basics
- ☸️ **[Kubernetes ML Guide](https://kubernetes.io/docs/tutorials/)** - Scaling ML applications
- ☁️ **[AWS SageMaker](https://aws.amazon.com/sagemaker/getting-started/)** - Cloud ML deployment

**🏁 Capstone Project:** Deploy a full ML application with CI/CD pipeline

---

## 🎯 **Specialized Learning Paths**

### 👁️ **Computer Vision Track**
- 📷 **[OpenCV Tutorials](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)** - Image processing fundamentals
- 🎯 **[YOLO Object Detection](https://github.com/ultralytics/yolov5)** - State-of-the-art detection
- 🔍 **[Detectron2](https://github.com/facebookresearch/detectron2)** - Facebook's CV library

### 💬 **Natural Language Processing Track**
- 📝 **[spaCy Course](https://course.spacy.io/)** - Industrial-strength NLP
- 📖 **[NLTK Book](https://www.nltk.org/book/)** - Classic NLP with Python
- 🤖 **[Transformers Documentation](https://huggingface.co/docs/transformers/index)** - Modern NLP models

### 🎮 **Reinforcement Learning Track**
- 🌀 **[OpenAI Spinning Up](https://spinningup.openai.com/)** - Deep RL fundamentals
- 🧠 **[DeepMind RL Course](https://www.deepmind.com/learning-resources/reinforcement-learning-lecture-series-2021)** - Advanced RL concepts
- 🎯 **[Stable Baselines3](https://stable-baselines3.readthedocs.io/)** - RL algorithms implementation

---

## 🛠️ **Essential Tools & Frameworks**

| 🔧 **Tool** | 🔗 **Link** | 💡 **Purpose** |
| :--- | :--- | :--- |
| **📓 Jupyter Notebook** | [jupyter.org](https://jupyter.org/) | Interactive coding environment |
| **☁️ Google Colab** | [colab.research.google.com](https://colab.research.google.com/) | Free GPU for training |
| **🐍 Anaconda** | [anaconda.com](https://www.anaconda.com/) | Python distribution for data science |
| **💻 VS Code** | [code.visualstudio.com](https://code.visualstudio.com/) | Best IDE for ML development |
| **📂 Git & GitHub** | [github.com](https://github.com/) | Version control for projects |

---

## 📊 **Practice Platforms & Datasets**

- 🏆 **[Kaggle Competitions](https://www.kaggle.com/competitions)** - Real-world ML challenges with prizes
- 📚 **[UCI ML Repository](https://archive.ics.uci.edu/ml/index.php)** - Classic datasets for practice
- 🔍 **[Google Dataset Search](https://datasetsearch.research.google.com/)** - Find datasets for any domain
- 📦 **[TensorFlow Datasets](https://www.tensorflow.org/datasets)** - Ready-to-use datasets
- 💻 **[HackerRank AI](https://www.hackerrank.com/domains/ai)** - Coding challenges for ML
- 🧩 **[LeetCode ML Problems](https://leetcode.com/)** - Algorithm practice

---

## 🎓 **University Courses (Free Online)**

- 🏛️ **[MIT 6.S191 Deep Learning](http://introtodeeplearning.com/)** - Intensive 1-week bootcamp
- 🎓 **[Stanford CS229 Machine Learning](https://cs229.stanford.edu/)** - Graduate-level ML course
- 🐻 **[Berkeley CS188 AI](https://inst.eecs.berkeley.edu/~cs188/)** - Artificial Intelligence fundamentals
- 🏫 **[CMU 10-701 ML](http://www.cs.cmu.edu/~tom/10701_sp11/)** - Theoretical foundations

---

## 📱 **Communities & Networking**

- 💬 **[r/MachineLearning](https://www.reddit.com/r/MachineLearning/)** - Latest research and discussions
- 🤝 **[AI Alignment Forum](https://www.alignmentforum.org/)** - Advanced AI safety discussions
- ⚙️ **[MLOps Community](https://mlops.community/)** - Production ML best practices
- ✍️ **[Towards Data Science](https://towardsdatascience.com/)** - Medium publication for ML articles
- 📚 **[Machine Learning Mastery](https://machinelearningmastery.com/)** - Practical tutorials

---

## 🚀 **Next Steps: Your Journey to ML Mastery**

1. **Week 1-2:** 🔧 Set up your environment (Python, Jupyter, Git) and complete Python basics
2. **Week 3-4:** 📊 Master NumPy and Pandas through Kaggle micro-courses
3. **Week 5-8:** 🎓 Complete Andrew Ng's ML course on Coursera
4. **Week 9-12:** 🏗️ Build 3 projects: regression, classification, and clustering
5. **Week 13-16:** 🧠 Learn deep learning with Fast.ai or TensorFlow tutorials
6. **Week 17-20:** 🎯 Specialize in Computer Vision OR NLP
7. **Week 21-24:** 🚀 Deploy a full ML application and contribute to open source
8. **Ongoing:** 📈 Participate in Kaggle competitions and read ML papers weekly

---

## 📚 **Recommended Books**

- 📖 **"Hands-On Machine Learning" by Aurélien Géron** - Best practical ML book
- 🧠 **"Deep Learning" by Ian Goodfellow** - Comprehensive theory
- 📊 **"Pattern Recognition and Machine Learning" by Christopher Bishop** - Mathematical foundations
- 📝 **"The Hundred-Page Machine Learning Book" by Andriy Burkov** - Quick overview

---

## 🎯 **Career Resources**

- 💼 **[ML Interview Prep](https://github.com/khangich/machine-learning-interview)** - Interview questions and answers
- 📘 **[Chip Huyen's ML Interviews Book](https://huyenchip.com/ml-interviews-book/)** - Comprehensive interview guide
- 🎓 **[LinkedIn Learning ML Paths](https://www.linkedin.com/learning/)** - Professional development courses

---

**✨ Remember:** Machine Learning is a marathon, not a sprint. Focus on understanding fundamentals, build projects consistently, and engage with the community. Good luck on your ML journey! 🚀
"""

def generate_data_analyst_fallback(goal):
    return f"""
# 🚀 Your Personalized Curriculum: {goal}

> 💡 **AI Assistant Note:** Our AI is currently at capacity, but we've prepared a comprehensive, curated learning path just for you!

---

## 📚 **Essential Data Analysis Resources**

| 🎓 **Platform / Course** | 🔗 **Link** | 💡 **Why This Matters** |
| :--- | :--- | :--- |
| **📊 Google Data Analytics Certificate** | [Coursera Google DA](https://www.coursera.org/professional-certificates/google-data-analytics) | Industry-recognized certification from Google |
| **🎯 DataCamp Data Analyst Track** | [DataCamp](https://www.datacamp.com/tracks/data-analyst-with-python) | Interactive learning with real datasets |
| **📈 Kaggle Learn** | [kaggle.com/learn](https://www.kaggle.com/learn) | Free micro-courses on data analysis |
| **🐍 Python for Data Analysis** | [Python Data Science Handbook](https://jakevdp.github.io/PythonDataScienceHandbook/) | Free online book by Jake VanderPlas |
| **📊 Excel Skills** | [Excel Exposure](https://excelexposure.com/) | Master Excel from basics to advanced |
| **💾 SQL Tutorial** | [Mode Analytics SQL Tutorial](https://mode.com/sql-tutorial/) | Learn SQL with real business data |
| **📉 Tableau Public** | [Tableau Learning](https://public.tableau.com/en-us/s/resources) | Free data visualization training |
| **⭐ Awesome Data Science** | [GitHub Awesome DS](https://github.com/academic/awesome-datascience) | Curated list of data science resources |

---

## 🗂️ **Detailed Learning Modules**

### 📘 **Phase 1: Foundations & Tools** (Weeks 1-8)

**🎯 Focus:** Excel, SQL, Python Basics, Statistics

**📖 Key Resources:**
- 📊 **[Excel Skills for Business](https://www.coursera.org/specializations/excel)** - Master Excel for data analysis
- 💾 **[SQL for Data Analysis](https://www.udacity.com/course/sql-for-data-analysis--ud198)** - Free Udacity course
- 🐍 **[Python for Data Science](https://www.kaggle.com/learn/python)** - Interactive Python tutorials
- 📈 **[Statistics Fundamentals](https://www.khanacademy.org/math/statistics-probability)** - Khan Academy stats
- 📊 **[Pandas Tutorial](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html)** - Data manipulation with Pandas
- 📉 **[Data Cleaning Guide](https://realpython.com/python-data-cleaning-numpy-pandas/)** - Clean messy data

**🏁 Milestone Project:** Analyze a real dataset and create an Excel dashboard

---

### 📗 **Phase 2: Advanced Analysis & Visualization** (Weeks 9-16)

**🎯 Focus:** Advanced SQL, Data Visualization, Business Intelligence

**📖 Key Resources:**
- 🎨 **[Tableau Training](https://www.tableau.com/learn/training)** - Official Tableau courses
- 📊 **[Power BI Learning](https://docs.microsoft.com/en-us/power-bi/guided-learning/)** - Microsoft Power BI tutorials
- 💾 **[Advanced SQL](https://www.windowfunctions.com/)** - Master window functions
- 📈 **[Matplotlib & Seaborn](https://seaborn.pydata.org/tutorial.html)** - Python visualization libraries
- 📊 **[Storytelling with Data](https://www.storytellingwithdata.com/)** - Data visualization best practices
- 🔍 **[Exploratory Data Analysis](https://www.kaggle.com/learn/data-visualization)** - Kaggle EDA course

**🏁 Milestone Project:** Build an interactive Tableau/Power BI dashboard

---

### 📙 **Phase 3: Business Analytics & Advanced Topics** (Weeks 17-24)

**🎯 Focus:** Predictive Analytics, A/B Testing, Business Metrics

**📖 Key Resources:**
- 📊 **[Google Analytics Academy](https://analytics.google.com/analytics/academy/)** - Free GA certification
- 🧪 **[A/B Testing Course](https://www.udacity.com/course/ab-testing--ud257)** - Udacity free course
- 📈 **[Predictive Analytics](https://www.coursera.org/learn/predictive-analytics)** - Forecasting techniques
- 💼 **[Business Metrics](https://www.klipfolio.com/resources/kpi-examples)** - KPI examples and guides
- 🔍 **[Data Mining](https://www.youtube.com/playlist?list=PLLssT5z_DsK9JDLcT8T62VtzwyW9LNepV)** - Stanford data mining course
- 📊 **[R for Data Science](https://r4ds.had.co.nz/)** - Free online R book

**🏁 Capstone Project:** Complete end-to-end business analysis with recommendations

---

## 🛠️ **Essential Tools & Software**

| 🔧 **Tool** | 🔗 **Link** | 💡 **Purpose** |
| :--- | :--- | :--- |
| **📊 Microsoft Excel** | [Excel Online](https://www.microsoft.com/en-us/microsoft-365/excel) | Spreadsheet analysis and dashboards |
| **📈 Tableau Public** | [Tableau Public](https://public.tableau.com/) | Free data visualization tool |
| **📊 Power BI Desktop** | [Power BI](https://powerbi.microsoft.com/) | Microsoft's BI platform |
| **🐍 Python + Jupyter** | [Anaconda](https://www.anaconda.com/) | Python data science distribution |
| **💾 PostgreSQL** | [PostgreSQL](https://www.postgresql.org/) | Open-source database for SQL practice |
| **📂 Git & GitHub** | [GitHub](https://github.com/) | Version control for projects |

---

## 📊 **Practice Platforms & Datasets**

- 🏆 **[Kaggle Datasets](https://www.kaggle.com/datasets)** - Thousands of real datasets
- 📚 **[UCI ML Repository](https://archive.ics.uci.edu/ml/index.php)** - Classic datasets
- 🔍 **[Google Dataset Search](https://datasetsearch.research.google.com/)** - Find any dataset
- 📊 **[Data.gov](https://www.data.gov/)** - US government open data
- 🌍 **[World Bank Data](https://data.worldbank.org/)** - Global development data
- 💼 **[HackerRank SQL](https://www.hackerrank.com/domains/sql)** - SQL practice problems

---

## 🎓 **Free Certifications & Courses**

- 🏆 **[Google Data Analytics Certificate](https://www.coursera.org/professional-certificates/google-data-analytics)** - Industry-recognized
- 📊 **[IBM Data Analyst Certificate](https://www.coursera.org/professional-certificates/ibm-data-analyst)** - Comprehensive program
- 💾 **[Microsoft Power BI Certification](https://docs.microsoft.com/en-us/learn/certifications/data-analyst-associate/)** - Official Microsoft cert
- 📈 **[Tableau Desktop Specialist](https://www.tableau.com/learn/certification/desktop-specialist)** - Tableau certification

---

## 📱 **Communities & Networking**

- 💬 **[r/DataAnalysis](https://www.reddit.com/r/DataAnalysis/)** - Data analysis community
- 📊 **[Tableau Community](https://community.tableau.com/)** - Tableau forums and tips
- 💼 **[Data Science Central](https://www.datasciencecentral.com/)** - Articles and discussions
- 🤝 **[Analytics Vidhya](https://www.analyticsvidhya.com/)** - Learning community

---

## 🚀 **Next Steps: Your Journey to Data Analyst Mastery**

1. **Week 1-2:** 📊 Master Excel basics and create your first pivot table
2. **Week 3-4:** 💾 Learn SQL fundamentals and query real databases
3. **Week 5-8:** 🐍 Start Python with Pandas for data manipulation
4. **Week 9-12:** 📈 Build your first Tableau/Power BI dashboard
5. **Week 13-16:** 📊 Complete Google Data Analytics Certificate
6. **Week 17-20:** 🧪 Learn A/B testing and statistical analysis
7. **Week 21-24:** 💼 Build a portfolio with 3-5 complete projects
8. **Ongoing:** 📈 Participate in Kaggle competitions and network

---

## 📚 **Recommended Books**

- 📖 **"Storytelling with Data" by Cole Nussbaumer Knaflic** - Visualization masterclass
- 📊 **"Python for Data Analysis" by Wes McKinney** - Pandas creator's guide
- 📈 **"The Data Warehouse Toolkit" by Ralph Kimball** - Data modeling bible
- 💼 **"Lean Analytics" by Alistair Croll** - Business metrics guide

---

## 🎯 **Career Resources**

- 💼 **[Data Analyst Interview Prep](https://www.interviewquery.com/)** - Practice interview questions
- 📊 **[Glassdoor Salary Data](https://www.glassdoor.com/Salaries/data-analyst-salary-SRCH_KO0,12.htm)** - Salary expectations
- 🎓 **[LinkedIn Learning](https://www.linkedin.com/learning/)** - Professional development

---

**✨ Remember:** Data Analysis is about telling stories with data. Focus on business impact, communicate clearly, and always validate your insights. Good luck on your journey! 🚀
"""

def generate_webdev_fallback(goal):
    return f"""
# 🚀 Your Personalized Curriculum: {goal}

> 💡 **AI Assistant Note:** Our AI is currently at capacity, but we've prepared a comprehensive, curated learning path just for you!

---

## 📚 **Essential Web Development Resources**

| 🎓 **Platform / Course** | 🔗 **Link** | 💡 **Why This Matters** |
| :--- | :--- | :--- |
| **🌐 MDN Web Docs** | [developer.mozilla.org](https://developer.mozilla.org/) | The ultimate web development reference |
| **🎯 FreeCodeCamp** | [freecodecamp.org](https://www.freecodecamp.org/) | Free, comprehensive web dev curriculum |
| **🛤️ The Odin Project** | [theodinproject.com](https://www.theodinproject.com/) | Full-stack development path |
| **⚛️ React Official Docs** | [react.dev](https://react.dev/) | Learn React from the source |
| **💚 Node.js Guides** | [nodejs.org/en/docs](https://nodejs.org/en/docs/guides/) | Official Node.js documentation |
| **🎨 CSS-Tricks** | [css-tricks.com](https://css-tricks.com/) | CSS tutorials and tips |
| **⭐ Awesome Web Dev** | [GitHub Awesome](https://github.com/sindresorhus/awesome) | Curated web dev resources |
| **🏗️ web.dev** | [web.dev](https://web.dev/) | Google's web development guidance |

---

## 🗂️ **Detailed Learning Modules**

### 📘 **Phase 1: Frontend Foundations** (Weeks 1-8)

**🎯 Focus:** HTML, CSS, JavaScript Fundamentals

**📖 Key Resources:**
- 🌐 **[HTML & CSS Tutorial](https://www.freecodecamp.org/learn/responsive-web-design/)** - FreeCodeCamp certification
- 🎨 **[CSS Grid & Flexbox](https://cssgrid.io/)** - Wes Bos free course
- ⚡ **[JavaScript30](https://javascript30.com/)** - 30 vanilla JS projects
- 📱 **[Responsive Web Design](https://web.dev/responsive-web-design-basics/)** - Google's guide
- 🎯 **[JavaScript.info](https://javascript.info/)** - Modern JavaScript tutorial
- 🔧 **[Git & GitHub](https://www.freecodecamp.org/news/git-and-github-for-beginners/)** - Version control basics

**🏁 Milestone Project:** Build a responsive portfolio website

---

### 📗 **Phase 2: Modern Frontend & Frameworks** (Weeks 9-16)

**🎯 Focus:** React, Vue, or Angular + Modern Tools

**📖 Key Resources:**
- ⚛️ **[React Tutorial](https://react.dev/learn)** - Official React docs
- 🎓 **[Full Stack Open](https://fullstackopen.com/)** - React + Node.js course
- 🎨 **[Tailwind CSS](https://tailwindcss.com/docs)** - Utility-first CSS framework
- 📦 **[npm & Package Management](https://docs.npmjs.com/)** - JavaScript packages
- ⚡ **[Vite Documentation](https://vitejs.dev/)** - Modern build tool
- 🔧 **[TypeScript Handbook](https://www.typescriptlang.org/docs/)** - Typed JavaScript

**🏁 Milestone Project:** Build a full-featured React application

---

### 📙 **Phase 3: Backend & Full Stack** (Weeks 17-24)

**🎯 Focus:** Node.js, Databases, APIs, Deployment

**📖 Key Resources:**
- 💚 **[Node.js Tutorial](https://nodejs.dev/learn)** - Official Node.js guide
- 🚀 **[Express.js Guide](https://expressjs.com/en/guide/routing.html)** - Web framework for Node
- 💾 **[MongoDB University](https://university.mongodb.com/)** - Free MongoDB courses
- 🐘 **[PostgreSQL Tutorial](https://www.postgresqltutorial.com/)** - SQL database guide
- 🔐 **[Authentication Guide](https://www.passportjs.org/)** - User authentication
- ☁️ **[Deploy on Vercel](https://vercel.com/docs)** - Free hosting and deployment

**🏁 Capstone Project:** Build and deploy a full-stack application

---

## 🛠️ **Essential Tools & Technologies**

| 🔧 **Tool** | 🔗 **Link** | 💡 **Purpose** |
| :--- | :--- | :--- |
| **💻 VS Code** | [code.visualstudio.com](https://code.visualstudio.com/) | Best code editor for web dev |
| **🌐 Chrome DevTools** | [Chrome DevTools](https://developer.chrome.com/docs/devtools/) | Browser debugging tools |
| **📦 npm** | [npmjs.com](https://www.npmjs.com/) | JavaScript package manager |
| **📂 Git & GitHub** | [github.com](https://github.com/) | Version control and collaboration |
| **🎨 Figma** | [figma.com](https://www.figma.com/) | UI/UX design tool |
| **📱 Postman** | [postman.com](https://www.postman.com/) | API testing tool |

---

## 📊 **Practice Platforms & Challenges**

- 💻 **[Frontend Mentor](https://www.frontendmentor.io/)** - Real-world frontend challenges
- 🏆 **[CodePen](https://codepen.io/)** - Frontend playground and inspiration
- 🧩 **[LeetCode](https://leetcode.com/)** - Algorithm practice
- 🎯 **[HackerRank](https://www.hackerrank.com/domains/tutorials/10-days-of-javascript)** - JavaScript challenges
- 🌐 **[DevChallenges](https://devchallenges.io/)** - Real-world projects

---

## 🎓 **Free Courses & Certifications**

- 🏆 **[FreeCodeCamp Certifications](https://www.freecodecamp.org/learn)** - 6 free certifications
- 🎓 **[The Odin Project](https://www.theodinproject.com/)** - Full curriculum
- 💚 **[Node.js Certification](https://nodejs.org/en/about/get-involved/certification)** - Official Node.js cert
- ⚛️ **[Meta React Certificate](https://www.coursera.org/professional-certificates/meta-react-native)** - Meta's React course

---

## 📱 **Communities & Networking**

- 💬 **[r/webdev](https://www.reddit.com/r/webdev/)** - Web development community
- 🐦 **[Dev.to](https://dev.to/)** - Developer community and articles
- 💼 **[Stack Overflow](https://stackoverflow.com/)** - Q&A for developers
- 🤝 **[Discord: The Programmer's Hangout](https://discord.gg/programming)** - Active dev community

---

## 🚀 **Next Steps: Your Journey to Web Dev Mastery**

1. **Week 1-2:** 🌐 Master HTML & CSS basics, build 3 simple pages
2. **Week 3-4:** 🎨 Learn CSS Grid, Flexbox, and responsive design
3. **Week 5-8:** ⚡ Complete JavaScript30 and build interactive projects
4. **Week 9-12:** ⚛️ Learn React and build 3 React applications
5. **Week 13-16:** 🎯 Master state management and API integration
6. **Week 17-20:** 💚 Learn Node.js, Express, and build a REST API
7. **Week 21-24:** 🚀 Build and deploy a full-stack application
8. **Ongoing:** 💼 Contribute to open source and build portfolio

---

## 📚 **Recommended Books**

- 📖 **"Eloquent JavaScript" by Marijn Haverbeke** - Free online JavaScript book
- 🎨 **"CSS Secrets" by Lea Verou** - Advanced CSS techniques
- ⚛️ **"React Up & Running" by Stoyan Stefanov** - React fundamentals
- 💚 **"Node.js Design Patterns" by Mario Casciaro** - Advanced Node.js

---

## 🎯 **Career Resources**

- 💼 **[Frontend Interview Handbook](https://www.frontendinterviewhandbook.com/)** - Interview prep
- 📊 **[Glassdoor Web Dev Salaries](https://www.glassdoor.com/Salaries/web-developer-salary-SRCH_KO0,13.htm)** - Salary data
- 🎓 **[LinkedIn Learning](https://www.linkedin.com/learning/)** - Professional courses

---

**✨ Remember:** Web development is constantly evolving. Focus on fundamentals, build projects, and never stop learning. Good luck on your journey! 🚀
"""

def generate_generic_fallback(goal):
    return f"""
# 🚀 Your Personalized Curriculum: {goal}

> 💡 **AI Assistant Note:** Our AI is currently at capacity, but we've prepared a comprehensive learning path to get you started!

---

## 📚 **Essential Learning Resources**

| 🎓 **Platform / Course** | 🔗 **Link** | 💡 **Why This Matters** |
| :--- | :--- | :--- |
| **🌐 Coursera** | [coursera.org](https://www.coursera.org/) | University-level courses from top institutions |
| **🎯 edX** | [edx.org](https://www.edx.org/) | Free courses from MIT, Harvard, and more |
| **📚 Udemy** | [udemy.com](https://www.udemy.com/) | Practical, project-based courses |
| **🎓 Khan Academy** | [khanacademy.org](https://www.khanacademy.org/) | Free education for all subjects |
| **💻 YouTube EDU** | [YouTube Learning](https://www.youtube.com/channel/UCSSlekSYRoyQo8uQGHvq4qQ) | Free video tutorials |
| **📖 MIT OpenCourseWare** | [ocw.mit.edu](https://ocw.mit.edu/) | Free MIT course materials |
| **⭐ GitHub Learning Lab** | [lab.github.com](https://lab.github.com/) | Learn by doing with GitHub |
| **🏆 LinkedIn Learning** | [linkedin.com/learning](https://www.linkedin.com/learning/) | Professional development courses |

---

## 🗂️ **Learning Path Structure**

### 📘 **Phase 1: Foundations** (Weeks 1-8)

**🎯 Focus:** Build strong fundamentals in {goal}

**📖 Recommended Actions:**
- 🔍 Research the core skills needed for {goal}
- 📚 Take introductory courses on Coursera or edX
- 💻 Set up your learning environment and tools
- 📝 Start a learning journal to track progress
- 🤝 Join online communities related to {goal}
- 🏗️ Build your first small project

**🏁 Milestone:** Complete foundational knowledge and create a simple project

---

### 📗 **Phase 2: Skill Development** (Weeks 9-16)

**🎯 Focus:** Develop practical skills and build projects

**📖 Recommended Actions:**
- 🎯 Take intermediate-level courses
- 🏗️ Build 3-5 progressively complex projects
- 📊 Learn industry-standard tools and frameworks
- 💼 Start building a portfolio
- 🤝 Network with professionals in the field
- 📚 Read industry blogs and documentation

**🏁 Milestone:** Complete a portfolio-worthy project

---

### 📙 **Phase 3: Mastery & Specialization** (Weeks 17-24)

**🎯 Focus:** Advanced topics and real-world application

**📖 Recommended Actions:**
- 🚀 Take advanced courses or specializations
- 💼 Work on real-world projects or freelance
- 🎓 Consider professional certifications
- 🤝 Contribute to open-source projects
- 📈 Build a strong online presence (GitHub, LinkedIn)
- 💡 Mentor others or teach what you've learned

**🏁 Capstone:** Complete a comprehensive project demonstrating mastery

---

## 🛠️ **Essential Learning Tools**

| 🔧 **Tool** | 🔗 **Link** | 💡 **Purpose** |
| :--- | :--- | :--- |
| **💻 VS Code** | [code.visualstudio.com](https://code.visualstudio.com/) | Universal code editor |
| **📂 GitHub** | [github.com](https://github.com/) | Version control and portfolio |
| **📝 Notion** | [notion.so](https://www.notion.so/) | Note-taking and organization |
| **🎨 Canva** | [canva.com](https://www.canva.com/) | Design and presentations |
| **💬 Discord** | [discord.com](https://discord.com/) | Join learning communities |

---

## 📊 **Practice & Community Platforms**

- 🏆 **[Reddit Communities](https://www.reddit.com/)** - Find subreddits for {goal}
- 💬 **[Stack Overflow](https://stackoverflow.com/)** - Q&A for technical questions
- 🤝 **[Discord Servers](https://discord.com/)** - Join learning communities
- 📚 **[Medium](https://medium.com/)** - Read articles and tutorials
- 🎓 **[Meetup](https://www.meetup.com/)** - Find local learning groups

---

## 🎓 **Recommended Learning Platforms**

- 🏆 **[Coursera](https://www.coursera.org/)** - University courses with certificates
- 🎯 **[edX](https://www.edx.org/)** - Free courses from top universities
- 📚 **[Udacity](https://www.udacity.com/)** - Nanodegree programs
- 💻 **[Pluralsight](https://www.pluralsight.com/)** - Technology skills platform
- 🎓 **[Skillshare](https://www.skillshare.com/)** - Creative and business skills

---

## 🚀 **Next Steps: Your Learning Journey**

1. **Week 1-2:** 🔍 Research {goal} and define your learning objectives
2. **Week 3-4:** 📚 Enroll in foundational courses
3. **Week 5-8:** 🏗️ Build your first project
4. **Week 9-12:** 🎯 Develop intermediate skills
5. **Week 13-16:** 💼 Create portfolio projects
6. **Week 17-20:** 🚀 Learn advanced topics
7. **Week 21-24:** 🏆 Complete capstone project
8. **Ongoing:** 📈 Continue learning and networking

---

## 📚 **General Learning Resources**

- 📖 **Search for books on {goal}** on Amazon or Goodreads
- 🎥 **YouTube channels** focused on {goal}
- 📝 **Medium articles** and blog posts
- 🎓 **Professional certifications** in {goal}

---

## 🎯 **Career Development**

- 💼 **[LinkedIn](https://www.linkedin.com/)** - Build your professional network
- 📊 **[Glassdoor](https://www.glassdoor.com/)** - Research salaries and companies
- 🎓 **[Indeed Career Guide](https://www.indeed.com/career-advice)** - Career resources
- 💡 **[AngelList](https://angel.co/)** - Startup jobs and opportunities

---

**✨ Remember:** Every expert was once a beginner. Stay consistent, build projects, and engage with the community. Good luck on your journey to becoming a {goal}! 🚀
"""
                

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
        Act as a Senior Software Architect and Coding Interviewer. 
        Create 3 CHALLENGING and REAL-WORLD coding tasks for a user learning: {request.goal}.
        
        CONTEXT:
        - Focus Area: {request.focus_area}
        - User Level: {request.experience_level}
        - Programming Language: {request.language}
        - Current Skills: {', '.join(request.skills)}

        CRITERIA FOR TASKS:
        1. "Real-world": Avoid generic academic problems. Tasks should be scenarios like "Process User Logs", "Validate API Payload", "Calculate Financial Ratios", or "Optimize Data Queries".
        2. Professional Starter Code: Include proper comments, type hints (if applicable for {request.language}), and a clear function signature.
        3. Testability: Ensure the tasks can be verified with input/output matching.
        
        Output a valid JSON array where each object has:
        - "title": A professional, descriptive title.
        - "description": A detailed problem statement following professional standards.
        - "starter_code": Professional boilerplate code.
        - "solution": The complete, optimized solution.
        - "language": "{request.language}"
        - "test_cases": An array of objects: [{"input": "function_call_or_input_code", "expected_output": "stringified_result"}]
        
        Example JSON format:
        [
            {{
                "title": "Data Pipeline: Email Validator",
                "description": "Implement a robust email validation logic for a user registration pipeline. The function should check for...",
                "starter_code": "def validate_email(email: str) -> bool:\n    # Implement logic to validate format\n    pass",
                "solution": "import re\n\ndef validate_email(email: str) -> bool:\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$'\n    return bool(re.match(pattern, email))",
                "language": "python",
                "test_cases": [
                    {{"input": "validate_email('test@example.com')", "expected_output": "True"}},
                    {{"input": "validate_email('invalid-email')", "expected_output": "False"}}
                ]
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
        # Return 3 distinct fallback tasks related to the goal
        return {
            "success": True, 
            "tasks": [
                {
                    "title": f"Foundation: {request.goal} Analysis", 
                    "description": f"Perform a basic analysis and architectural setup for a {request.goal} project.",
                    "starter_code": f"# Project: {request.goal}\n# Step 1: Initialize core components\n",
                    "solution": "print('Environment ready')",
                    "language": request.language,
                    "test_cases": [{"input": "", "expected_output": "Environment ready"}]
                },
                {
                    "title": f"Logic: {request.goal} Data Handler", 
                    "description": f"Create a function to handle incoming signals for the {request.goal} system.",
                    "starter_code": "def process_data(data):\n    # Your logic here\n    pass",
                    "solution": "def process_data(data): return data",
                    "language": request.language,
                    "test_cases": [{"input": "process_data('test')", "expected_output": "test"}]
                },
                {
                    "title": f"Production: {request.goal} API Mock", 
                    "description": f"Implement a mock interface for testing the {request.goal} integration.",
                    "starter_code": "class MockAPI:\n    def get_status(self):\n        return 'offline'",
                    "solution": "class MockAPI:\n    def get_status(self):\n        return 'online'",
                    "language": request.language,
                    "test_cases": [{"input": "MockAPI().get_status()", "expected_output": "online"}]
                }
            ]
        }

class EvaluationRequest(BaseModel):
    code: str
    language: str
    test_cases: List[Dict[str, str]]

@app.post("/evaluate-code")
async def evaluate_code(request: EvaluationRequest):
    """
    Evaluates code against test cases.
    """
    results = []
    all_passed = True
    lang = request.language.lower()

    for i, tc in enumerate(request.test_cases):
        input_code = tc.get("input", "")
        expected = tc.get("expected_output", "").strip()
        
        # Construct code to run: user code + the test case call (if any)
        # For Python, we'll try to execute and get the last expression result or stdout
        if lang == "python":
            full_code = request.code + "\n"
            if input_code:
                # If there's a call like add(5,3), we want its result
                full_code += f"\nprint({input_code})"
                
            try:
                import sys
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    exec_globals = {"__builtins__": __builtins__}
                    exec(full_code, exec_globals)
                
                actual_output = f.getvalue().strip()
                passed = actual_output == expected
                results.append({
                    "test_id": i + 1,
                    "input": input_code,
                    "expected": expected,
                    "actual": actual_output,
                    "passed": passed
                })
                if not passed: all_passed = False
            except Exception as e:
                all_passed = False
                results.append({
                    "test_id": i + 1,
                    "error": str(e),
                    "passed": False
                })
        
        elif lang == "javascript":
            # For JS, we'll append a console.log of the input code
            full_code = request.code + "\n"
            if input_code:
                full_code += f"\nconsole.log({input_code});"
            
            try:
                result = subprocess.run(
                    ["node", "-e", full_code], 
                    capture_output=True, 
                    text=True, 
                    timeout=3
                )
                actual_output = result.stdout.strip()
                if result.returncode != 0:
                    passed = False
                    error = result.stderr
                else:
                    passed = actual_output == expected
                    error = None
                
                results.append({
                    "test_id": i + 1,
                    "input": input_code,
                    "expected": expected,
                    "actual": actual_output,
                    "passed": passed,
                    "error": error
                })
                if not passed: all_passed = False
            except Exception as e:
                all_passed = False
                results.append({"test_id": i+1, "error": str(e), "passed": False})

        elif lang == "java" or lang == "cpp" or lang == "c++" or lang == "csharp" or lang == "c#":
            # For compiled languages, we'll run the full code and check output
            try:
                # Use the run_code function internally
                exec_request = CodeExecutionRequest(code=request.code, language=lang)
                exec_result = await run_code(exec_request)
                
                if exec_result["success"]:
                    actual_output = exec_result["output"].strip()
                    passed = actual_output == expected
                    results.append({
                        "test_id": i + 1,
                        "input": input_code,
                        "expected": expected,
                        "actual": actual_output,
                        "passed": passed
                    })
                    if not passed: all_passed = False
                else:
                    all_passed = False
                    results.append({
                        "test_id": i + 1,
                        "error": exec_result.get("error", "Execution failed"),
                        "passed": False
                    })
            except Exception as e:
                all_passed = False
                results.append({"test_id": i+1, "error": str(e), "passed": False})
        
        elif lang == "sql":
            # For SQL, execute and check results
            try:
                exec_request = CodeExecutionRequest(code=request.code, language="sql")
                exec_result = await run_code(exec_request)
                
                if exec_result["success"]:
                    actual_output = exec_result["output"].strip()
                    passed = expected.lower() in actual_output.lower() or actual_output == expected
                    results.append({
                        "test_id": i + 1,
                        "input": input_code,
                        "expected": expected,
                        "actual": actual_output,
                        "passed": passed
                    })
                    if not passed: all_passed = False
                else:
                    all_passed = False
                    results.append({
                        "test_id": i + 1,
                        "error": exec_result.get("error", "SQL execution failed"),
                        "passed": False
                    })
            except Exception as e:
                all_passed = False
                results.append({"test_id": i+1, "error": str(e), "passed": False})
        
        elif lang == "html" or lang == "css":
            # For HTML/CSS, validation is the test
            try:
                exec_request = CodeExecutionRequest(code=request.code, language=lang)
                exec_result = await run_code(exec_request)
                
                passed = exec_result["success"]
                results.append({
                    "test_id": i + 1,
                    "input": "Validation check",
                    "expected": "Valid code",
                    "actual": "Valid" if passed else exec_result.get("error", "Invalid"),
                    "passed": passed
                })
                if not passed: all_passed = False
            except Exception as e:
                all_passed = False
                results.append({"test_id": i+1, "error": str(e), "passed": False})
        
        else:
            all_passed = False
            results.append({
                "test_id": i + 1,
                "error": f"Language '{lang}' not supported for evaluation",
                "passed": False
            })

    return {"success": True, "all_passed": all_passed, "results": results}

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

    elif lang == "java":
        try:
            # Save code to a temporary file
            import tempfile
            import os
            
            # Extract class name from code
            class_name = "Main"
            for line in request.code.split('\n'):
                if 'public class' in line:
                    class_name = line.split('public class')[1].split('{')[0].strip()
                    break
            
            with tempfile.TemporaryDirectory() as tmpdir:
                java_file = os.path.join(tmpdir, f"{class_name}.java")
                with open(java_file, 'w') as f:
                    f.write(request.code)
                
                # Compile
                compile_result = subprocess.run(
                    ["javac", java_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if compile_result.returncode != 0:
                    return {"success": False, "error": f"Compilation Error:\n{compile_result.stderr}"}
                
                # Run
                run_result = subprocess.run(
                    ["java", "-cp", tmpdir, class_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if run_result.returncode == 0:
                    return {"success": True, "output": run_result.stdout if run_result.stdout else "Code executed successfully (no output)."}
                else:
                    return {"success": False, "error": run_result.stderr}
        except FileNotFoundError:
            return {"success": False, "error": "Java compiler (javac) not found. Please install JDK to run Java code."}
        except Exception as e:
            return {"success": False, "error": f"Java execution failed: {str(e)}"}
    
    elif lang == "cpp" or lang == "c++":
        try:
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                cpp_file = os.path.join(tmpdir, "main.cpp")
                exe_file = os.path.join(tmpdir, "main.exe" if os.name == 'nt' else "main")
                
                with open(cpp_file, 'w') as f:
                    f.write(request.code)
                
                # Compile with g++
                compile_result = subprocess.run(
                    ["g++", cpp_file, "-o", exe_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if compile_result.returncode != 0:
                    return {"success": False, "error": f"Compilation Error:\n{compile_result.stderr}"}
                
                # Run
                run_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if run_result.returncode == 0:
                    return {"success": True, "output": run_result.stdout if run_result.stdout else "Code executed successfully (no output)."}
                else:
                    return {"success": False, "error": run_result.stderr}
        except FileNotFoundError:
            return {"success": False, "error": "C++ compiler (g++) not found. Please install GCC/MinGW to run C++ code."}
        except Exception as e:
            return {"success": False, "error": f"C++ execution failed: {str(e)}"}
    
    elif lang == "csharp" or lang == "c#":
        try:
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                cs_file = os.path.join(tmpdir, "Program.cs")
                
                with open(cs_file, 'w') as f:
                    f.write(request.code)
                
                # Try to compile and run with dotnet
                compile_result = subprocess.run(
                    ["dotnet", "script", cs_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=tmpdir
                )
                
                if compile_result.returncode == 0:
                    return {"success": True, "output": compile_result.stdout if compile_result.stdout else "Code executed successfully (no output)."}
                else:
                    # If dotnet script fails, try csc (C# compiler)
                    try:
                        exe_file = os.path.join(tmpdir, "program.exe")
                        compile_csc = subprocess.run(
                            ["csc", f"/out:{exe_file}", cs_file],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if compile_csc.returncode != 0:
                            return {"success": False, "error": f"Compilation Error:\n{compile_csc.stderr}"}
                        
                        run_result = subprocess.run(
                            [exe_file],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if run_result.returncode == 0:
                            return {"success": True, "output": run_result.stdout if run_result.stdout else "Code executed successfully (no output)."}
                        else:
                            return {"success": False, "error": run_result.stderr}
                    except FileNotFoundError:
                        return {"success": False, "error": compile_result.stderr if compile_result.stderr else "C# compiler not found. Please install .NET SDK to run C# code."}
        except FileNotFoundError:
            return {"success": False, "error": ".NET SDK not found. Please install .NET SDK to run C# code."}
        except Exception as e:
            return {"success": False, "error": f"C# execution failed: {str(e)}"}
    
    elif lang == "html":
        # For HTML, we'll validate and return a preview message
        try:
            from html.parser import HTMLParser
            
            class HTMLValidator(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.errors = []
                
                def error(self, message):
                    self.errors.append(message)
            
            validator = HTMLValidator()
            validator.feed(request.code)
            
            if validator.errors:
                return {"success": False, "error": f"HTML Validation Errors:\n" + "\n".join(validator.errors)}
            
            # Count elements
            tag_count = request.code.count('<')
            
            return {
                "success": True, 
                "output": f"✓ HTML code validated successfully!\n\nStats:\n- Total tags: {tag_count}\n- Length: {len(request.code)} characters\n\nNote: To see the rendered output, save this as an .html file and open in a browser."
            }
        except Exception as e:
            return {"success": False, "error": f"HTML validation failed: {str(e)}"}
    
    elif lang == "css":
        # For CSS, we'll validate syntax
        try:
            import re
            
            # Basic CSS validation
            # Check for balanced braces
            open_braces = request.code.count('{')
            close_braces = request.code.count('}')
            
            if open_braces != close_braces:
                return {"success": False, "error": f"CSS Syntax Error: Unbalanced braces ({{ {open_braces}, }} {close_braces})"}
            
            # Count rules
            rules = request.code.count('{')
            
            # Count properties (approximate)
            properties = len(re.findall(r'[\w-]+\s*:', request.code))
            
            return {
                "success": True,
                "output": f"✓ CSS code validated successfully!\n\nStats:\n- CSS Rules: {rules}\n- Properties: {properties}\n- Length: {len(request.code)} characters\n\nNote: To see the styling in action, apply this CSS to an HTML file."
            }
        except Exception as e:
            return {"success": False, "error": f"CSS validation failed: {str(e)}"}
    
    else:
        return {"success": False, "error": f"Execution for '{lang}' is not supported in this environment yet. Supported languages: Python, JavaScript, Java, C++, C#, SQL, HTML, CSS."}

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


class VoiceCommandRequest(BaseModel):
    transcript: str
    current_context: Optional[str] = "navigation"

@app.post("/voice-command")
async def process_voice_command(request: VoiceCommandRequest):
    try:
        # Construct prompt for JARVIS NLP
        prompt = f"""
        Act as an Advanced Voice Operating System (JARVIS). Analyze the user's voice command and map it to a specific JSON action.
        
        USER COMMAND: "{request.transcript}"
        CURRENT CONTEXT: "{request.current_context}"

        YOUR GOAL: Return ONLY raw JSON (no markdown) mapping the intent to one of these structures:

        1. NAVIGATION {{ "type": "navigate", "target": "dashboard" | "ide" | "profile" | "resume" | "progress" | "path" | "landing" }}
           - "Go to dashboard", "Open IDE", "Show my stats", "Open my profile", "Go to resume builder", "Show learning path"
           - NOTE: "path" maps to the learning path view. "home" maps to "landing".
           - IF the user says "open this page" or "reload", return {{ "type": "system", "action": "reload" }} if they mean reload, otherwise treat as chat.

        2. CODING ACTION {{ "type": "code", "action": "insert" | "delete_line" | "undo" | "redo" | "clear" | "run", "code": "code_snippet_here" }}
           - If user asks for code (e.g. "Create a fibonacci function"), generate the ACTUAL python/js code in the 'code' field.
           - If user says "print hello", 'code' should be "print('hello')"
           - Keep code concise.

        3. SYSTEM CONTROL {{ "type": "system", "action": "scroll_up" | "scroll_down" | "scroll_top" | "scroll_bottom" | "logout" | "reload" }}

        4. TERMINAL {{ "type": "terminal", "action": "open" | "close" | "clear" }}

        5. CHAT / UNKNOWN {{ "type": "chat", "response": "Your short, witty, JARVIS-like response here." }}

        IMPORTANT - MULTI-LANGUAGE SUPPORT:
        - The user may speak in ANY language (Hindi, Spanish, French, Chinese, Tamil, etc.).
        - You MUST translate the INTENT into the English JSON actions above.
        - Example: "Mujhe dashboard jana hai" -> {{ "type": "navigate", "target": "dashboard" }}
        - Example: "Ek loop likho" -> {{ "type": "code", "action": "insert", "code": "for i in range(10):\\n    pass" }}
        - Example: "Open this page" (if ambiguous) -> {{ "type": "chat", "response": "Which page would you like me to open, sir? I can access the Dashboard, IDE, Profile, or Learning Path." }}
        """

        response = model.generate_content(prompt)
        text = response.text
        # Clean markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"Voice Command Error: {e}")
        return {"type": "chat", "response": "Processing error, sir. Please repeat."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)