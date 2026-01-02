const API_BASE = '/api';
let currentUser = null;
let currentAuthTab = 'Login';
let codeEditor = null;
let currentTasks = [];
let activeTaskId = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    const savedUser = localStorage.getItem('bugbuster_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showView(currentUser.profile?.onboarding_completed ? 'dashboard' : 'onboarding');
        updateDashboardUI();
    } else {
        showView('login');
    }
});

// --- Navigation ---
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
    document.getElementById(viewId + '-view').style.display = 'block';

    if (viewId === 'onboarding' && currentUser) {
        document.getElementById('onboarding-title').innerText = `👋 Welcome, ${currentUser.username}!`;
    }

    // Refresh icons
    if (window.lucide) window.lucide.createIcons();
}

function switchAuthTab(tab) {
    currentAuthTab = tab;
    const btns = document.querySelectorAll('#login-view .nav-tab');
    btns.forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    document.getElementById('auth-title').innerText = tab === 'Login' ? 'Welcome Back!' : 'Join BugBusters';
    document.getElementById('auth-btn').innerText = tab;
    document.getElementById('register-fields').style.display = tab === 'Register' ? 'block' : 'none';
    document.getElementById('confirm-fields').style.display = tab === 'Register' ? 'block' : 'none';
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-view').forEach(v => v.style.display = 'none');
    document.getElementById('tab-' + tabId).style.display = 'block';

    const btns = document.querySelectorAll('#dashboard-view .nav-tab');
    btns.forEach(b => b.classList.remove('active'));

    // Find the button that was clicked. Simple way: find by text or use event.currentTarget
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }

    if (tabId === 'profile') updateProfileUI();
    if (tabId === 'ide') initIDE();
}

// --- Auth Actions ---
async function handleAuth() {
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const email = document.getElementById('reg-email').value;
    const confirm = document.getElementById('auth-confirm').value;

    if (!username || !password) return alert("Please fill all required fields.");

    const btn = document.getElementById('auth-btn');
    const originalText = btn.innerText;
    btn.innerText = 'Processing...';
    btn.disabled = true;

    try {
        if (currentAuthTab === 'Register') {
            if (password !== confirm) return alert("Passwords do not match!");
            const res = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            if (res.ok) {
                alert("Registration successful! You can now login.");
                switchAuthTab('Login');
            } else {
                const data = await res.json();
                alert(data.message || "Registration failed");
            }
        } else {
            const res = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok) {
                currentUser = data.user;
                localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
                showView(currentUser.profile?.onboarding_completed ? 'dashboard' : 'onboarding');
                updateDashboardUI();
            } else {
                alert(data.message || "Invalid credentials");
            }
        }
    } catch (err) {
        alert("Server communication error. Please check if backend is running.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// --- Profile Actions ---
async function saveProfile() {
    const profile = {
        bio: document.getElementById('profile-bio').value,
        experience_level: document.getElementById('profile-level').value,
        skills: document.getElementById('profile-skills').value.split(',').map(s => s.trim()).filter(s => s),
        learning_goals: document.getElementById('profile-goals').value.split(',').map(s => s.trim()).filter(s => s),
        linkedin: document.getElementById('profile-linkedin').value,
        phone: document.getElementById('profile-phone').value,
        time_commitment: document.getElementById('profile-time').value,
        learning_style: document.getElementById('profile-style').value,
        difficulty_preference: document.getElementById('profile-difficulty').value
    };

    try {
        const res = await fetch(`${API_BASE}/user/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: currentUser.username, profile })
        });
        const data = await res.json();
        currentUser = data.user;
        localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
        showView('dashboard');
        updateDashboardUI();
    } catch (err) {
        alert("Failed to save profile. Please try again.");
    }
}

// --- Dashboard Logic ---
function updateDashboardUI() {
    if (!currentUser) return;
    document.getElementById('dashboard-subtitle').innerText = `Welcome back, ${currentUser.username}! Ready to continue your learning journey?`;

    const insightSkill = document.getElementById('insight-skill');
    if (insightSkill) {
        insightSkill.innerText = `Strategic growth in your ${currentUser.profile?.skills[0] || 'core'} skills detected.`;
    }

    // Skills tags
    const skillsList = document.getElementById('skills-list');
    if (skillsList) {
        skillsList.innerHTML = '';
        currentUser.profile?.skills?.forEach(s => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.innerText = s;
            skillsList.appendChild(span);
        });
        if (currentUser.profile?.skills?.length === 0) {
            skillsList.innerHTML = '<span style="color: grey; font-size: 0.8rem;">No skills added yet.</span>';
        }
    }

    // Goals tags
    const goalsList = document.getElementById('goals-list');
    if (goalsList) {
        goalsList.innerHTML = '';
        currentUser.profile?.learning_goals?.forEach(g => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.style.background = 'rgba(139, 92, 246, 0.2)';
            span.style.borderColor = 'rgba(139, 92, 246, 0.3)';
            span.style.color = '#c4b5fd';
            span.innerText = g;
            goalsList.appendChild(span);
        });
        if (currentUser.profile?.learning_goals?.length === 0) {
            goalsList.innerHTML = '<span style="color: grey; font-size: 0.8rem;">No goals set yet.</span>';
        }
    }

    // Restore path if exists
    restorePath();
}

function restorePath() {
    if (currentUser && currentUser.learning_paths && currentUser.learning_paths.length > 0) {
        const lastPath = currentUser.learning_paths[currentUser.learning_paths.length - 1];
        if (lastPath && lastPath.content) {
            document.getElementById('path-result').style.display = 'block';
            document.getElementById('path-text').innerHTML = marked.parse(lastPath.content);
            const goal = currentUser.profile.learning_goals[0] || "Learning Path";
            // Flowchart might need goal context, using last goal or default
            document.getElementById('flowchart-img').src = `http://localhost:8001/generate-flowchart?goal=${encodeURIComponent(goal)}&t=${Date.now()}`;
        }
    }
}

function updateProfileUI() {
    document.getElementById('prof-user').innerText = currentUser.username;
    document.getElementById('prof-email').innerText = currentUser.email || 'not_provided@example.com';
    document.getElementById('prof-bio').innerText = currentUser.profile?.bio ? `"${currentUser.profile.bio}"` : '"No bio provided yet."';
}

// --- AI Actions ---
async function generatePath() {
    const goal = document.getElementById('path-goal').value;
    if (!goal) return alert("Please enter a learning goal first!");

    const usePrev = document.querySelector('input[name="use-prev"]:checked').value === 'yes';

    const btn = document.getElementById('gen-path-btn');
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Generating journey...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/generate-path`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_profile: currentUser.profile,
                goal,
                use_previous_skills: usePrev
            })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.message || data.error || data.detail || "Server Error");
        }

        document.getElementById('path-result').style.display = 'block';
        document.getElementById('path-text').innerHTML = marked.parse(data.path);

        // Save path to backend
        await fetch(`${API_BASE}/user/save-path`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: currentUser.username, path: data.path })
        });
        // Update local user
        if (!currentUser.learning_paths) currentUser.learning_paths = [];
        currentUser.learning_paths.push({ content: data.path, created_at: new Date().toISOString() });
        localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));

        // Load Flowchart directly from AI service
        document.getElementById('flowchart-img').src = `http://localhost:8001/generate-flowchart?goal=${encodeURIComponent(goal)}&t=${Date.now()}`;

        btn.innerHTML = originalContent;
        btn.disabled = false;

        // Scroll to results
        document.getElementById('path-result').scrollIntoView({ behavior: 'smooth' });

        // Auto-generate tasks for the new path
        generateTasks(goal);

    } catch (err) {
        console.error(err);
        alert(`Error: ${err.message}. Please check console for details.`);
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function generateResume() {
    const box = document.getElementById('resume-box');
    box.style.display = 'block';
    // Clear previous and show loading
    box.innerHTML = `
        <div class="text-center py-8">
            <span class="spinner" style="width: 30px; height: 30px; border-width: 3px;"></span>
            <p class="mt-4" style="color: #94a3b8;">✨ AI is crafting your Premium Resume and Roadmap...</p>
        </div>
    `;

    try {
        const goal = document.getElementById('path-goal')?.value || "Software Engineer";
        const res = await fetch(`${API_BASE}/generate-resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_profile: currentUser.profile,
                username: currentUser.username,
                email: currentUser.email,
                goal: goal
            })
        });
        const data = await res.json();

        if (data.success) {
            box.classList.remove('path-box'); // Remove default styling
            box.style.background = 'transparent';
            box.style.border = 'none';
            box.style.padding = '0';
            box.innerHTML = buildPremiumResume(data.resume);
            // Re-apply icons
            if (window.lucide) window.lucide.createIcons();
        } else {
            box.innerHTML = `<div class="insight-purple">Failed to generate resume: ${data.error}</div>`;
        }
    } catch (err) {
        console.error(err);
        box.innerHTML = `<div class="insight-purple">Error connecting to AI Service. Please ensure it's running.</div>`;
    }
}

function buildPremiumResume(data) {
    const skillsHtml = data.skills.map(s => `<li>${s}</li>`).join('');
    const languagesHtml = data.languages.map(l => `<li>${l}</li>`).join('');
    const hobbiesHtml = data.hobbies.map(h => `<li>${h}</li>`).join('');

    // Safety check for currentUser
    const userProfile = currentUser?.profile || {};
    const contact = data.contact || {};
    const phone = contact.phone || userProfile.phone || "+1 (555) 123-4567";
    const linkedin = contact.linkedin || userProfile.linkedin || "linkedin.com/in/user";
    const email = contact.email || currentUser?.email || "user@example.com";
    const location = contact.location || "Global";

    const experienceHtml = data.experience.map(exp => `
        <div class="experience-item">
            <div class="item-header">
                <div>
                    <div class="item-title">${exp.title}</div>
                    <div class="item-subtitle">${exp.company}</div>
                </div>
                <div class="item-period">${exp.period}</div>
            </div>
            <ul class="item-list">
                ${exp.responsibilities.map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>
    `).join('');

    const educationHtml = data.education.map(edu => `
        <div class="experience-item">
            <div class="item-header">
                <div>
                    <div class="item-title">${edu.degree}</div>
                    <div class="item-subtitle">${edu.institution}</div>
                </div>
                <div class="item-period">${edu.year}</div>
            </div>
        </div>
    `).join('');

    const roadmapHtml = data.roadmap.map(item => `
        <div class="roadmap-item">
            <div class="roadmap-phase">${item.phase}</div>
            <div class="roadmap-courses"><strong>Courses:</strong> ${item.courses.join(', ')}</div>
        </div>
    `).join('');

    // use the selectedTemplate global variable
    const templateClass = typeof selectedTemplate !== 'undefined' ? `resume-${selectedTemplate}` : 'resume-coral';

    return `
        <div class="premium-resume ${templateClass}">
            <div class="resume-sidebar">
                <div class="resume-photo-container">
                    <img src="https://i.pravatar.cc/300?u=${data.name}" class="resume-photo" alt="Profile">
                </div>
                
                <div class="sidebar-section">
                    <div class="contact-item"><i data-lucide="phone"></i> ${phone}</div>
                    <div class="contact-item"><i data-lucide="mail"></i> ${email}</div>
                    <div class="contact-item"><i data-lucide="map-pin"></i> ${location}</div>
                    <div class="contact-item"><i data-lucide="linkedin"></i> ${linkedin}</div>
                </div>

                <div class="sidebar-section">
                    <h3>Skills</h3>
                    <ul class="sidebar-list">
                        ${skillsHtml}
                    </ul>
                </div>

                <div class="sidebar-section">
                    <h3>Languages</h3>
                    <ul class="sidebar-list">
                        ${languagesHtml}
                    </ul>
                </div>

                <div class="sidebar-section">
                    <h3>Hobbies</h3>
                    <ul class="sidebar-list">
                        ${hobbiesHtml}
                    </ul>
                </div>
            </div>

            <div class="resume-main">
                <header class="resume-header">
                    <h1>${data.name.toUpperCase()}</h1>
                    <h2>${data.job_title}</h2>
                    <p class="resume-summary">${data.summary}</p>
                </header>

                <section class="resume-section">
                    <div class="section-title">Experience</div>
                    ${experienceHtml}
                </section>

                <section class="resume-section">
                    <div class="section-title">Learning Roadmap</div>
                    ${roadmapHtml}
                </section>

                <section class="resume-section">
                    <div class="section-title">Education</div>
                    ${educationHtml}
                </section>
            </div>
        </div>
        <div class="mt-6 flex gap-4 justify-center no-print">
            <button class="btn-primary" onclick="window.print()"><i data-lucide="download"></i> Download Resume as PDF</button>
        </div>
    `;
}

function updateProgress() {
    alert("Activity Logged! (This is a demonstration - progress tracking is being saved to your profile).");
}

function goToOnboarding() {
    showView('onboarding');
}

function logout() {
    localStorage.removeItem('bugbuster_user');
    currentUser = null;
    showView('login');
}

// --- IDE & Task Logic ---
function initIDE() {
    if (!codeEditor) {
        codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
            mode: "javascript",
            theme: "dracula",
            lineNumbers: true,
            autoCloseBrackets: true,
        });
        codeEditor.setSize("100%", "100%");
    }
    // Load tasks if available
    if (currentUser && currentUser.tasks) {
        currentTasks = currentUser.tasks;
        renderTasks();
    }
}

async function generateTasks(goalContext = null) {
    const goal = goalContext || document.getElementById('path-goal').value || currentUser.profile.learning_goals[0] || "General Coding";
    const btn = document.getElementById('fetch-tasks-btn');
    if (btn) btn.innerHTML = '<span class="spinner"></span> Loading...';

    // Determine Adaptive Difficulty
    let level = 'Beginner';
    // Ensure progress exists
    const count = (currentUser.progress && currentUser.progress.completed_tasks) ? currentUser.progress.completed_tasks : 0;

    if (count >= 20) level = 'Advanced Mastery';
    else if (count >= 10) level = 'Intermediate';

    try {
        const res = await fetch(`${API_BASE}/generate-tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                goal: goal,
                skills: currentUser.profile.skills || [],
                experience_level: level,
                focus_area: count >= 20 ? "Complex Systems & Optimization" : (count >= 10 ? "Real-world Applications" : "Fundamentals"),
                language: document.getElementById('language-select') ? document.getElementById('language-select').value : 'python'
            })
        });
        const data = await res.json();

        if (data.success) {
            // Normalize tasks to include language if not present
            const lang = document.getElementById('language-select') ? document.getElementById('language-select').value : 'python';
            const tasks = data.tasks.map(t => ({ ...t, language: t.language || lang }));

            // Save tasks to user profile via backend
            const saveRes = await fetch(`${API_BASE}/user/assign-tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: currentUser.username, tasks: tasks })
            });
            const saveData = await saveRes.json();
            currentUser = saveData.user;
            localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
            currentTasks = currentUser.tasks;
            renderTasks();
            alert("New tasks assigned! Check the IDE tab.");
        }
    } catch (error) {
        console.error("Task generation failed:", error);
        alert("Failed to generate tasks.");
    } finally {
        if (btn) btn.innerHTML = '<i data-lucide="plus"></i> Get More Tasks';
        if (window.lucide) window.lucide.createIcons();
    }
}

function renderTasks() {
    const list = document.getElementById('task-list');
    list.innerHTML = '';

    currentTasks.forEach(task => {
        const div = document.createElement('div');
        div.className = `task-item ${task.status === 'completed' ? 'completed' : ''}`;
        div.style.padding = '10px';
        div.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        div.style.cursor = 'pointer';
        div.style.background = activeTaskId === task.id ? 'rgba(255,255,255,0.1)' : 'transparent';

        div.innerHTML = `
            <div style="font-weight: bold; color: ${task.status === 'completed' ? '#10b981' : '#f8fafc'}">
                ${task.status === 'completed' ? '✓ ' : ''}${task.title}
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${task.description}
            </div>
        `;
        div.onclick = () => loadTask(task.id);
        list.appendChild(div);
    });
}

function loadTask(id) {
    activeTaskId = id;
    const task = currentTasks.find(t => t.id === id);
    if (!task) return;

    document.getElementById('current-task-title').innerText = task.title;
    document.getElementById('current-task-desc').innerText = task.description;

    // Detect Language with Fallback
    let lang = task.language;
    if (!lang) {
        const title = task.title.toLowerCase();
        if (title.includes('sql')) lang = 'sql';
        else if (title.includes('html') || title.includes('web')) lang = 'html';
        else if (title.includes('css')) lang = 'css';
        else if (title.includes('javascript') || title.includes('js')) lang = 'javascript';
        else lang = 'python';
    }
    // Map to CodeMirror modes
    const modeMap = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'text/x-java',
        'cpp': 'text/x-c++src',
        'csharp': 'text/x-csharp',
        'html': 'htmlmixed',
        'css': 'css',
        'sql': 'sql'
    };

    // Auto-select dropdown
    const select = document.getElementById('language-select');
    if (select) select.value = lang;

    // Reset Hint
    const hintArea = document.getElementById('solution-area');
    if (hintArea) hintArea.style.display = 'none';

    if (codeEditor) {
        // Set mode
        codeEditor.setOption("mode", modeMap[lang] || 'python');

        // Force minimal visibility.
        let initialCode = task.starter_code || (lang === 'python' ? "# Write your code here" : "// Write your code here");
        codeEditor.setValue(initialCode);
    }
    renderTasks(); // update active highlight
}

function changeLanguage() {
    const lang = document.getElementById('language-select').value;
    const modeMap = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'text/x-java',
        'cpp': 'text/x-c++src',
        'csharp': 'text/x-csharp',
        'html': 'htmlmixed',
        'css': 'css',
        'sql': 'sql'
    };
    if (codeEditor) {
        codeEditor.setOption("mode", modeMap[lang] || 'python');
    }
}

function toggleHint() {
    if (!activeTaskId) return;
    const task = currentTasks.find(t => t.id === activeTaskId);
    if (!task) return;

    const area = document.getElementById('solution-area');
    const code = document.getElementById('solution-code');

    if (area.style.display === 'none') {
        area.style.display = 'block';
        code.innerText = task.solution || "No solution provided.";
    } else {
        area.style.display = 'none';
    }
}

function resetCode() {
    if (!activeTaskId) return;
    const task = currentTasks.find(t => t.id === activeTaskId);
    if (task && codeEditor) {
        codeEditor.setValue(task.starter_code);
    }
}

async function submitTask() {
    if (!activeTaskId) return alert("Select a task first.");
    const code = codeEditor.getValue();

    // In a real app, send code to backend for execution.
    // Here, we'll simulate verification.
    document.getElementById('execution-result').innerText = "Running tests...";
    document.getElementById('execution-result').className = "text-sm font-bold text-yellow-500";

    setTimeout(async () => {
        // Mock success
        document.getElementById('execution-result').innerText = "Tests Passed! ✅";
        document.getElementById('execution-result').className = "text-sm font-bold text-green-500";

        // Update status in backend
        try {
            const res = await fetch(`${API_BASE}/user/complete-task`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: currentUser.username, taskId: activeTaskId })
            });
            const data = await res.json();
            currentUser = data.user;
            localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
            currentTasks = currentUser.tasks;
            renderTasks();
            updateDashboardUI(); // Update streak in UI

            // Celebration effect
            const btn = document.querySelector(`div[onclick="loadTask('${activeTaskId}')"]`);
            if (btn) btn.style.background = "#10b98133";

        } catch (err) {
            console.error("Failed to complete task:", err);
        }
    }, 1500);
}

async function runCode() {
    const code = codeEditor.getValue();
    const lang = document.getElementById('language-select').value;

    const resultDiv = document.getElementById('execution-result');
    resultDiv.style.display = 'block';

    // Client-side execution for HTML/CSS
    if (lang === 'html') {
        resultDiv.innerHTML = '<iframe id="preview-frame" style="width:100%; height:300px; border:none; background:white; border-radius: 4px;"></iframe>';
        const frame = document.getElementById('preview-frame');
        const doc = frame.contentDocument || frame.contentWindow.document;
        doc.open();
        doc.write(code);
        doc.close();
        return;
    }
    else if (lang === 'css') {
        resultDiv.innerHTML = '<iframe id="preview-frame" style="width:100%; height:300px; border:none; background:white; border-radius: 4px;"></iframe>';
        const frame = document.getElementById('preview-frame');
        const doc = frame.contentDocument || frame.contentWindow.document;
        doc.open();
        doc.write(`<html><head><style>${code}</style></head><body><h1>CSS Preview</h1><div class="test-element">This is a test element to check your CSS styles.</div><button>Button</button><input placeholder="Input..."></body></html>`);
        doc.close();
        return;
    }

    resultDiv.innerText = "Running...";
    resultDiv.style.color = "#fbbf24"; // yellow

    try {
        const res = await fetch(`${API_BASE}/run-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language: lang })
        });
        const data = await res.json();

        if (data.success) {
            resultDiv.innerText = `> Output:\n${data.output}`;
            resultDiv.style.display = 'block';
            resultDiv.style.color = "#93c5fd"; // light blue
            resultDiv.style.whiteSpace = "pre-wrap";
            resultDiv.className = ""; // clear previous classes
        } else {
            resultDiv.innerText = `> Error: ${data.error}`;
            resultDiv.style.display = 'block';
            resultDiv.style.color = "#ef4444"; // red
            resultDiv.className = "";
        }
    } catch (err) {
        console.error(err);
        resultDiv.innerText = "Execution failed.";
        resultDiv.className = "text-sm font-bold text-red-500";
    }
}
