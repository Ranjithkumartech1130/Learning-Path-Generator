const API_BASE = '/api';
let currentUser = null;
let currentAuthTab = 'Login';
let codeEditor = null;
let currentTasks = [];
let activeTaskId = null;
let xterm = null;
let terminalSocket = null;
let fitAddon = null;
let currentTaskStartTime = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initParallax();
    initCustomCursor();

    const savedUser = localStorage.getItem('bugbuster_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateDashboardUI();
        // If we want to skip landing for logged in users:
        // showView(currentUser.profile?.onboarding_completed ? 'dashboard' : 'onboarding');
        // But for now, let's show the wonderful landing:
        showView('landing');
    } else {
        showView('landing');
    }
});

function initCustomCursor() {
    if (!window.gsap) return;
    const cursor = document.querySelector('.custom-cursor');
    const follower = document.querySelector('.cursor-follower');

    if (!cursor || !follower) return;

    // Set initial position out of view but ready
    gsap.set([cursor, follower], { xPercent: -50, yPercent: -50, opacity: 0 });
    gsap.set(cursor, { rotation: -10 });

    // Entrance pulse to show where the cursor is
    setTimeout(() => {
        gsap.to([cursor, follower], { opacity: 1, duration: 1 });
    }, 500);

    window.addEventListener('mousemove', (e) => {
        gsap.to(cursor, {
            x: e.clientX,
            y: e.clientY,
            duration: 0.1,
            ease: "power2.out"
        });
        gsap.to(follower, {
            x: e.clientX,
            y: e.clientY,
            duration: 0.4,
            ease: "power3.out"
        });
    });

    const interactives = 'button, a, input, select, textarea, .template-card, .task-item, .metric-card, .nav-tab, [onclick]';

    document.addEventListener('mouseover', (e) => {
        if (e.target.closest(interactives)) {
            document.body.classList.add('cursor-hover');
            gsap.to(cursor, { scale: 1.3, duration: 0.3 });
            gsap.to(follower, { scale: 1.8, duration: 0.3 });
        }
    });

    document.addEventListener('mouseout', (e) => {
        if (e.target.closest(interactives)) {
            document.body.classList.remove('cursor-hover');
            gsap.to(cursor, { scale: 1, duration: 0.3 });
            gsap.to(follower, { scale: 1, duration: 0.3 });
        }
    });
}

// --- Navigation ---
function showView(viewId) {
    const landingView = document.getElementById('landing-view');
    const stApp = document.querySelector('.stApp');
    const targetViewId = viewId.includes('-view') ? viewId : viewId + '-view';

    if (viewId === 'landing') {
        landingView.style.display = 'block';
        stApp.style.display = 'block';
        stApp.style.opacity = '1';

        const savedUser = localStorage.getItem('bugbuster_user');
        const defaultViewId = savedUser ? 'dashboard-view' : 'login-view';

        document.querySelectorAll('.stApp .view').forEach(v => v.style.display = 'none');
        const defaultView = document.getElementById(defaultViewId);
        if (defaultView) {
            defaultView.style.display = 'block';

            // GSAP Animation for landing entrance
            gsap.from(defaultView.querySelectorAll('.hero-card, .login-container'), {
                y: 50,
                opacity: 0,
                duration: 1,
                stagger: 0.2,
                ease: "power4.out"
            });
        }

        document.body.style.overflowY = 'auto';
        window.scrollTo(0, 0);
    } else {
        const currentViews = document.querySelectorAll('.stApp .view');
        const targetView = document.getElementById(targetViewId);

        if (targetView) {
            // Find current visible view
            let currentVisible = null;
            currentViews.forEach(v => {
                if (window.getComputedStyle(v).display !== 'none') {
                    currentVisible = v;
                }
            });

            if (currentVisible && currentVisible !== targetView) {
                gsap.to(currentVisible, {
                    opacity: 0,
                    duration: 0.4,
                    onComplete: () => {
                        currentVisible.style.display = 'none';
                        targetView.style.display = 'block';
                        gsap.fromTo(targetView, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6 });
                    }
                });
            } else {
                currentViews.forEach(v => v.style.display = 'none');
                targetView.style.display = 'block';
                targetView.style.opacity = '1';
            }
        }
    }

    if (viewId === 'onboarding' && currentUser) {
        document.getElementById('onboarding-title').innerText = `👋 Welcome, ${currentUser.username}!`;
    }

    // Refresh icons
    if (window.lucide) window.lucide.createIcons();
}

function switchAuthTab(tab, event) {
    currentAuthTab = tab;
    const btns = document.querySelectorAll('#login-view .nav-tab');
    btns.forEach(b => b.classList.remove('active'));

    // Find the button (target might be an icon)
    const target = event ? event.currentTarget : null;
    if (target) target.classList.add('active');

    const authContent = document.querySelector('.login-container .mt-6');
    if (!authContent) {
        // Fallback if content not found
        document.getElementById('auth-title').innerText = tab === 'Login' ? 'Welcome Back!' : 'Join BugBusters';
        document.getElementById('auth-btn').innerText = tab;
        document.getElementById('register-fields').style.display = tab === 'Register' ? 'block' : 'none';
        document.getElementById('confirm-fields').style.display = tab === 'Register' ? 'block' : 'none';
        return;
    }

    gsap.to(authContent, {
        opacity: 0,
        y: 10,
        duration: 0.3,
        onComplete: () => {
            document.getElementById('auth-title').innerText = tab === 'Login' ? 'Welcome Back!' : 'Join BugBusters';
            document.getElementById('auth-btn').innerText = tab;
            document.getElementById('register-fields').style.display = tab === 'Register' ? 'block' : 'none';
            document.getElementById('confirm-fields').style.display = tab === 'Register' ? 'block' : 'none';

            gsap.to(authContent, {
                opacity: 1,
                y: 0,
                duration: 0.5,
                ease: "back.out(1.7)"
            });
        }
    });
}

function switchTab(tabId, event) {
    const tabs = document.querySelectorAll('.tab-view');
    const targetTab = document.getElementById('tab-' + tabId);

    if (!targetTab) return;
    if (window.getComputedStyle(targetTab).display === 'block') return;

    let currentVisible = null;
    tabs.forEach(v => {
        if (window.getComputedStyle(v).display === 'block') {
            currentVisible = v;
        }
    });

    if (currentVisible) {
        gsap.to(currentVisible, {
            opacity: 0,
            x: -20,
            duration: 0.3,
            onComplete: () => {
                currentVisible.style.display = 'none';
                targetTab.style.display = 'block';
                gsap.fromTo(targetTab,
                    { opacity: 0, x: 20 },
                    { opacity: 1, x: 0, duration: 0.5, ease: "power2.out" }
                );

                // Stagger animate elements inside the tab
                gsap.from(targetTab.querySelectorAll('.glass-card, .metric-card, .form-group'), {
                    y: 20,
                    opacity: 0,
                    duration: 0.6,
                    stagger: 0.05,
                    ease: "power2.out"
                });
            }
        });
    } else {
        tabs.forEach(v => v.style.display = 'none');
        targetTab.style.display = 'block';
        targetTab.style.opacity = '1';

        // Stagger animate elements inside the tab
        gsap.from(targetTab.querySelectorAll('.glass-card, .metric-card, .form-group'), {
            y: 20,
            opacity: 0,
            duration: 0.6,
            stagger: 0.05,
            ease: "power2.out"
        });
    }

    const btns = document.querySelectorAll('#dashboard-view .nav-tab');
    btns.forEach(b => b.classList.remove('active'));

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
            span.style.background = 'rgba(120, 184, 184, 0.15)';
            span.style.borderColor = 'rgba(120, 184, 184, 0.3)';
            span.style.color = '#78B8B8';
            span.innerText = g;
            goalsList.appendChild(span);
        });
        if (currentUser.profile?.learning_goals?.length === 0) {
            goalsList.innerHTML = '<span style="color: grey; font-size: 0.8rem;">No goals set yet.</span>';
        }
    }

    // Metrics
    if (currentUser.progress) {
        const p = currentUser.progress;

        // Active Days
        const activeDaysText = `${p.active_days || 0} Days`;
        if (document.getElementById('active-days-val')) document.getElementById('active-days-val').innerText = activeDaysText;
        if (document.getElementById('prog-active-days-val')) document.getElementById('prog-active-days-val').innerText = activeDaysText;

        // Streak
        const streakText = `${p.streak || 0} Days 🔥`;
        if (document.getElementById('streak-val')) document.getElementById('streak-val').innerText = streakText;
        if (document.getElementById('prog-streak-val')) document.getElementById('prog-streak-val').innerText = streakText;

        // Total Time
        const timeText = formatTime(p.total_time || 0);
        if (document.getElementById('total-time-val')) document.getElementById('total-time-val').innerText = timeText;
        if (document.getElementById('prog-total-time-val')) document.getElementById('prog-total-time-val').innerText = timeText;
    }

    // Restore path if exists
    restorePath();
}

function formatTime(seconds) {
    if (!seconds) return "0m";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
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

        // Typing effect for the path
        typeMarkedContent('path-text', data.path);

        // Also display in terminal if connected
        if (xterm && terminalSocket && terminalSocket.readyState === WebSocket.OPEN) {
            xterm.write('\r\n\x1b[36m[ AI: Generating Learning Path... ]\x1b[0m\r\n');
            const cleanText = data.path.replace(/\n/g, '\r\n');
            // Write to terminal with a slight delay imitation if desired, or just dump it
            xterm.write(cleanText + '\r\n');
        }

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

function typeMarkedContent(elementId, fullText) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.innerHTML = '';
    let currentText = '';
    let index = 0;
    const speed = 2; // Fast typing speed

    function type() {
        if (index < fullText.length) {
            currentText += fullText[index];
            element.innerHTML = marked.parse(currentText);
            index++;

            // Auto-scroll to bottom of the content
            const container = element.parentElement;
            if (container) container.scrollTop = container.scrollHeight;

            setTimeout(type, speed);
        } else {
            element.innerHTML = marked.parse(fullText);
            if (window.lucide) window.lucide.createIcons();
        }
    }
    type();
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
            mode: "python",
            theme: "dracula",
            lineNumbers: true,
            autoCloseBrackets: true,
            scrollbarStyle: "native",
            tabSize: 4,
            indentUnit: 4,
            lineWrapping: true
        });
        codeEditor.setSize("100%", "100%");
    }

    // Refresh editor to fix display issues after showing hidden tab
    setTimeout(() => {
        codeEditor.refresh();
    }, 100);

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

async function clearTasks() {
    if (!confirm("Are you sure you want to clear all tasks? This cannot be undone.")) return;

    try {
        const res = await fetch(`${API_BASE}/user/clear-tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: currentUser.username })
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
            currentTasks = [];
            activeTaskId = null;
            renderTasks();

            // Clear editor
            if (codeEditor) codeEditor.setValue("");
            document.getElementById('current-task-title').innerText = "Select a Task";
            document.getElementById('current-task-desc').innerText = "Code your solution below.";

            alert("Tasks cleared successfully.");
        }
    } catch (error) {
        console.error("Failed to clear tasks:", error);
        alert("Failed to clear tasks.");
    }
}

function renderTasks() {
    const list = document.getElementById('task-list');
    list.innerHTML = '';

    currentTasks.forEach(task => {
        const div = document.createElement('div');
        const isActive = activeTaskId === task.id;
        div.className = `task-item ${task.status === 'completed' ? 'completed' : ''} ${isActive ? 'active-task' : ''}`;

        div.innerHTML = `
            <div style="font-weight: bold; color: ${task.status === 'completed' ? '#10b981' : (isActive ? '#78B8B8' : '#e2e8f0')}">
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

        // Refresh to ensure correct rendering
        setTimeout(() => {
            codeEditor.refresh();
        }, 50);
    }
    renderTasks(); // update active highlight

    // Start Timer
    currentTaskStartTime = Date.now();
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

    // Update Tab Filename
    const extMap = {
        'python': 'py', 'javascript': 'js', 'java': 'java', 'cpp': 'cpp',
        'csharp': 'cs', 'html': 'html', 'css': 'css', 'sql': 'sql'
    };
    const tabLabel = document.getElementById('tab-filename');
    if (tabLabel) tabLabel.innerText = `solution.${extMap[lang] || 'txt'}`;
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
    const task = currentTasks.find(t => t.id === activeTaskId);
    if (!task) return;

    const code = codeEditor.getValue();
    const resultDiv = document.getElementById('execution-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<span class="spinner" style="width: 14px; height: 14px;"></span> Running evaluation tests...';
    resultDiv.style.color = "#fbbf24";

    try {
        const res = await fetch(`${API_BASE}/evaluate-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: task.language || document.getElementById('language-select').value,
                test_cases: task.test_cases || []
            })
        });
        const data = await res.json();

        if (data.success) {
            if (data.all_passed) {
                resultDiv.innerHTML = '<div style="color: #10b981; font-weight: bold;">All Tests Passed! ✅</div>';

                // Show breakdown if multiple tests
                if (data.results && data.results.length > 0) {
                    let breakdown = '<div style="font-size: 0.8rem; margin-top: 5px; color: #94a3b8;">' +
                        data.results.map(r => `Test ${r.test_id}: Passed`).join(' | ') +
                        '</div>';
                    resultDiv.innerHTML += breakdown;
                }

                // Update status in backend
                const duration = currentTaskStartTime ? Math.round((Date.now() - currentTaskStartTime) / 1000) : 0;
                currentTaskStartTime = Date.now();

                const completeRes = await fetch(`${API_BASE}/user/complete-task`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: currentUser.username, taskId: activeTaskId, duration: duration })
                });
                const completeData = await completeRes.json();
                currentUser = completeData.user;
                localStorage.setItem('bugbuster_user', JSON.stringify(currentUser));
                currentTasks = currentUser.tasks;
                renderTasks();
                updateDashboardUI();
            } else {
                resultDiv.innerHTML = '<div style="color: #ef4444; font-weight: bold;">Some Tests Failed. ❌</div>';
                let list = '<ul style="font-size: 0.85rem; margin-top: 5px; list-style: none; padding: 0;">';
                data.results.forEach(r => {
                    if (!r.passed) {
                        list += `<li style="margin-bottom: 5px; color: #f87171;">Test ${r.test_id} Failed: ${r.error || `Expected "${r.expected}", Got "${r.actual}"`}</li>`;
                    }
                });
                list += '</ul>';
                resultDiv.innerHTML += list;
            }
        } else {
            resultDiv.innerText = `Evaluation Error: ${data.error}`;
            resultDiv.style.color = "#ef4444";
        }
    } catch (err) {
        console.error(err);
        resultDiv.innerText = "Connection failed during evaluation.";
        resultDiv.style.color = "#ef4444";
    }
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

// --- Terminal Logic ---
function toggleTerminal() {
    const panel = document.getElementById('terminal-panel');
    const btn = document.getElementById('terminal-toggle-btn');
    const isHidden = panel.style.display === 'none';

    if (isHidden) {
        panel.style.display = 'block';
        btn.classList.add('active');
        initTerminal();
    } else {
        panel.style.display = 'none';
        btn.classList.remove('active');
        if (terminalSocket) {
            terminalSocket.close();
            terminalSocket = null;
        }
    }
}

function initTerminal() {
    if (xterm) {
        connectTerminalSocket();
        setTimeout(() => fitAddon.fit(), 100);
        return;
    }

    // Initialize xterm
    xterm = new Terminal({
        cursorBlink: true,
        fontSize: 13,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        theme: {
            background: '#0a0a0a',
            foreground: '#f8fafc',
            cursor: '#60a5fa',
            selection: 'rgba(96, 165, 250, 0.3)',
            black: '#000000',
            red: '#ef4444',
            green: '#22c55e',
            yellow: '#eab308',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#f8fafc'
        }
    });

    try {
        fitAddon = new (window.FitAddon?.FitAddon || window.fitAddon?.FitAddon)();
        xterm.loadAddon(fitAddon);
    } catch (e) {
        console.error("FitAddon load failed:", e);
    }

    xterm.open(document.getElementById('terminal-container'));
    if (fitAddon) fitAddon.fit();

    // Resize listener
    window.addEventListener('resize', () => {
        const p = document.getElementById('terminal-panel');
        if (p && p.style.display !== 'none' && fitAddon) {
            fitAddon.fit();
            if (terminalSocket && terminalSocket.readyState === WebSocket.OPEN) {
                terminalSocket.send(JSON.stringify({
                    type: 'resize',
                    cols: xterm.cols,
                    rows: xterm.rows
                }));
            }
        }
    });

    xterm.onData(data => {
        if (terminalSocket && terminalSocket.readyState === WebSocket.OPEN) {
            terminalSocket.send(data);
        }
    });

    // Also trigger initial resize send after connection
    xterm.onResize(size => {
        if (terminalSocket && terminalSocket.readyState === WebSocket.OPEN) {
            terminalSocket.send(JSON.stringify({
                type: 'resize',
                cols: size.cols,
                rows: size.rows
            }));
        }
    });

    connectTerminalSocket();
}

function connectTerminalSocket() {
    if (terminalSocket && terminalSocket.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/terminal`;

    terminalSocket = new WebSocket(wsUrl);

    terminalSocket.onopen = () => {
        xterm.write('\r\n\x1b[32m[ SYSTEM: Terminal Connected ]\x1b[0m\r\n');
        // Clear anything and show prompt
        terminalSocket.send('\r');
    };

    terminalSocket.onmessage = (event) => {
        xterm.write(event.data);
    };

    terminalSocket.onclose = () => {
        xterm.write('\r\n\x1b[31m[ SYSTEM: Terminal Disconnected ]\x1b[0m\r\n');
    };

    terminalSocket.onerror = (err) => {
        console.error('Terminal WebSocket Error:', err);
        xterm.write('\r\n\x1b[31m[ SYSTEM: Error connecting to terminal backend ]\x1b[0m\r\n');
    };
}
// --- Parallax Logic ---
function initParallax() {
    if (!window.gsap || !window.ScrollTrigger) return;

    gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

    const tl = gsap.timeline({
        scrollTrigger: {
            trigger: '.scrollDist',
            start: '0 0',
            end: '100% 100%',
            scrub: 1
        }
    });

    tl.fromTo('.sky', { y: 0 }, { y: -200 }, 0)
        .fromTo('.cloud1', { y: 100 }, { y: -800 }, 0)
        .fromTo('.cloud2', { y: -150 }, { y: -500 }, 0)
        .fromTo('.cloud3', { y: -50 }, { y: -650 }, 0)
        .fromTo('.mountBg', { y: -10 }, { y: -100 }, 0)
        .fromTo('.mountMg', { y: -30 }, { y: -250 }, 0)
        .fromTo('.mountFg', { y: -50 }, { y: -600 }, 0);

    // Fade out landing as we reach the app content (bidirectional)
    gsap.to('.parallax-main', {
        scrollTrigger: {
            trigger: '.stApp',
            start: 'top 95%',
            end: 'top 30%',
            scrub: true
        },
        autoAlpha: 0 // Handles opacity and visibility (pointer-events) automatically
    });

    // Show/hide back to top button based on scroll position
    const backToTopBtn = document.getElementById('back-to-top-btn');
    if (backToTopBtn) {
        ScrollTrigger.create({
            trigger: '.stApp',
            start: 'top 80%',
            end: 'bottom bottom',
            onEnter: () => {
                backToTopBtn.style.display = 'flex';
                gsap.to(backToTopBtn, { opacity: 1, duration: 0.3 });
            },
            onLeaveBack: () => {
                gsap.to(backToTopBtn, {
                    opacity: 0,
                    duration: 0.3,
                    onComplete: () => { backToTopBtn.style.display = 'none'; }
                });
            }
        });
    }

    const arrowBtn = document.querySelector('#arrow-btn');
    if (arrowBtn) {
        arrowBtn.addEventListener('mouseenter', () => {
            gsap.to('.arrow', { y: 10, duration: 0.8, ease: 'back.inOut(3)', overwrite: 'auto' });
        });

        arrowBtn.addEventListener('mouseleave', () => {
            gsap.to('.arrow', { y: 0, duration: 0.5, ease: 'power3.out', overwrite: 'auto' });
        });

        arrowBtn.addEventListener('click', () => {
            scrollToLogin();
        });
    }
}

// Function to scroll back to top
function scrollToTop() {
    if (!window.gsap || !window.ScrollToPlugin) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
    }

    gsap.to(window, {
        scrollTo: { y: 0, autoKill: false },
        duration: 1.5,
        ease: 'power3.inOut'
    });
}

function scrollToLogin() {
    if (!window.gsap || !window.ScrollToPlugin) {
        // Fallback if GSAP is missing
        const stApp = document.querySelector('.stApp');
        if (stApp) stApp.scrollIntoView({ behavior: 'smooth' });
        return;
    }

    gsap.to(window, {
        scrollTo: { y: '.stApp', autoKill: false },
        duration: 1.2,
        ease: 'power3.inOut',
        onComplete: () => {
            const savedUser = localStorage.getItem('bugbuster_user');
            if (savedUser) {
                showView(currentUser?.profile?.onboarding_completed ? 'dashboard' : 'onboarding');
            } else {
                showView('login');
            }
            // Removed window.scrollTo(0,0) as it resets the parallax and hides the app
        }
    });
}
