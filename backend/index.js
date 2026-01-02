const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const axios = require('axios');
const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8001';
const DATA_FILE = path.join(__dirname, 'data', 'users.json');

app.use(cors());
app.use(bodyParser.json());

// Serve static files from the 'public' folder
app.use(express.static(path.join(__dirname, 'public')));

// Helper functions for persistence
const loadUsers = () => {
    try {
        if (!fs.existsSync(DATA_FILE)) {
            // Ensure directory exists
            const dir = path.dirname(DATA_FILE);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(DATA_FILE, '{}');
            return {};
        }
        const data = fs.readFileSync(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error("Error loading users:", err);
        return {};
    }
};

const saveUsers = (users) => {
    try {
        const dir = path.dirname(DATA_FILE);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(DATA_FILE, JSON.stringify(users, null, 2));
    } catch (err) {
        console.error("Error saving users:", err);
    }
};

// --- Auth Routes ---
app.post('/api/register', (req, res) => {
    const { username, email, password } = req.body;
    const users = loadUsers();

    if (users[username]) return res.status(400).json({ message: "User already exists" });

    users[username] = {
        username,
        email,
        password,
        profile: {
            skills: [],
            experience_level: 'Beginner',
            bio: '',
            learning_goals: [],
            interests: [],
            time_commitment: '1-5 hours',
            learning_style: 'Visual',
            difficulty_preference: 'Beginner-friendly',
            onboarding_completed: false
        },
        learning_paths: [],
        tasks: [], // Store assigned tasks here
        progress: { streak: 0, completed_tasks: 0, last_active: null }
    };
    saveUsers(users);
    res.json({ message: "Registration successful" });
});

app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    const users = loadUsers();
    const user = users[username];

    if (user && user.password === password) {
        // Log Login
        if (!user.login_logs) user.login_logs = [];
        user.login_logs.push({
            timestamp: new Date().toISOString(),
            userAgent: req.headers['user-agent']
        });
        saveUsers(users);

        res.json({ success: true, user });
    } else {
        res.status(401).json({ message: "Invalid credentials" });
    }
});

app.post('/api/user/profile', (req, res) => {
    const { username, profile } = req.body;
    const users = loadUsers();

    if (!users[username]) return res.status(404).json({ message: "User not found" });

    users[username].profile = { ...users[username].profile, ...profile, onboarding_completed: true };
    saveUsers(users);
    res.json({ message: "Profile updated", user: users[username] });
});

app.post('/api/user/save-path', (req, res) => {
    const { username, path } = req.body;
    const users = loadUsers();
    if (!users[username]) return res.status(404).json({ message: "User not found" });

    // Handle existing paths array
    if (!users[username].learning_paths) users[username].learning_paths = [];

    users[username].learning_paths.push({
        id: Date.now(),
        content: path,
        created_at: new Date().toISOString()
    });
    saveUsers(users);
    res.json({ success: true, user: users[username] });
});

// --- Task & Streak Routes ---
app.post('/api/user/assign-tasks', (req, res) => {
    const { username, tasks } = req.body; // tasks array from AI
    const users = loadUsers();
    if (!users[username]) return res.status(404).json({ message: "User not found" });

    // Add unique IDs to tasks if missing
    const newTasks = tasks.map(t => ({
        ...t,
        id: t.id || Date.now() + Math.random().toString(36).substr(2, 9),
        status: 'pending',
        assigned_at: new Date().toISOString()
    }));

    if (!users[username].tasks) users[username].tasks = [];
    users[username].tasks = [...users[username].tasks, ...newTasks];
    saveUsers(users);
    res.json({ success: true, tasks: newTasks, user: users[username] });
});

app.post('/api/user/clear-tasks', (req, res) => {
    const { username } = req.body;
    const users = loadUsers();
    if (!users[username]) return res.status(404).json({ message: "User not found" });

    users[username].tasks = [];
    saveUsers(users);
    res.json({ success: true, user: users[username] });
});

app.post('/api/user/complete-task', (req, res) => {
    const { username, taskId, duration } = req.body;
    const users = loadUsers();
    if (!users[username]) return res.status(404).json({ message: "User not found" });

    if (!users[username].tasks) users[username].tasks = [];
    const taskIndex = users[username].tasks.findIndex(t => t.id === taskId);

    if (taskIndex === -1) return res.status(404).json({ message: "Task not found" });

    // Allow updating time/stats even if already completed (if user improves solution)
    // But usually we only count streak once.
    // Let's assume we update status to completed if not already.
    const isFirstCompletion = users[username].tasks[taskIndex].status !== 'completed';
    users[username].tasks[taskIndex].status = 'completed';

    // Store time spent on this specific task
    const taskDuration = duration || 0; // in seconds
    users[username].tasks[taskIndex].time_spent = (users[username].tasks[taskIndex].time_spent || 0) + taskDuration;

    if (!users[username].progress) users[username].progress = { streak: 0, completed_tasks: 0, last_active: null, active_days: 0, total_time: 0 };

    // Update global total time
    users[username].progress.total_time = (users[username].progress.total_time || 0) + taskDuration;

    if (isFirstCompletion) {
        users[username].progress.completed_tasks += 1;
    }

    // Streak and Active Days Logic
    const today = new Date().toDateString();
    const lastActiveDate = users[username].progress.last_active ? new Date(users[username].progress.last_active) : null;
    const lastActive = lastActiveDate ? lastActiveDate.toDateString() : null;

    if (today !== lastActive) {
        // Increment Active Days (unique days)
        users[username].progress.active_days = (users[username].progress.active_days || 0) + 1;

        if (lastActive) {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            if (lastActive === yesterday.toDateString()) {
                users[username].progress.streak += 1;
            } else {
                // Streak broken, reset to 1 (since they are active today)
                users[username].progress.streak = 1;
            }
        } else {
            // First time ever active
            users[username].progress.streak = 1;
        }
        users[username].progress.last_active = new Date().toISOString();
    }

    saveUsers(users);
    res.json({ success: true, user: users[username] });
});

app.post('/api/run-code', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/run-code`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error("Exec Error:", error.response?.data || error.message);
        res.status(500).json({ success: false, error: "Execution server failed" });
    }
});

app.post('/api/evaluate-code', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/evaluate-code`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error("Eval Error:", error.response?.data || error.message);
        res.status(500).json({ success: false, error: "Evaluation server failed" });
    }
});

// --- AI Proxy Routes ---
app.post('/api/generate-path', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/generate-path`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error("AI Service Error:", error.response?.data || error.message);
        res.status(500).json({
            message: "AI Service connection failed",
            error: error.response?.data || error.message,
            details: error.toString()
        });
    }
});

app.post('/api/generate-tasks', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/generate-tasks`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error("AI Service Task Error:", error.response?.data || error.message);
        res.status(500).json({
            message: "AI Service connection failed",
            error: error.response?.data || error.message
        });
    }
});

app.post('/api/generate-resume', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/generate-resume`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error("AI Service Resume Error:", error.response?.data || error.message);
        res.status(500).json({
            message: "AI Service connection failed",
            error: error.response?.data || error.message
        });
    }
});

const http = require('http');
const { WebSocketServer } = require('ws');
const { spawn } = require('child_process');

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/terminal' });

wss.on('connection', (ws) => {
    console.log('Terminal connected');

    // Switch to cmd.exe on Windows for better stability with standard streams if powershell behaves oddly
    const shell = process.platform === 'win32' ? 'cmd.exe' : 'bash';
    const args = process.platform === 'win32' ? [] : ['-i'];

    const term = spawn(shell, args, {
        cwd: path.join(__dirname, '..'), // Parent dir of backend (project root)
        env: { ...process.env, TERM: 'xterm-256color' },
        shell: false
    });

    term.stdout.on('data', (data) => {
        ws.send(data.toString());
    });

    term.stderr.on('data', (data) => {
        ws.send(data.toString());
    });

    ws.on('message', (msg) => {
        // Log input for debugging
        // console.log('Term raw input:', msg);
        term.stdin.write(msg);
    });

    ws.on('close', () => {
        console.log('Terminal disconnected');
        term.kill();
    });

    term.on('close', () => {
        ws.close();
    });

    term.on('error', (err) => {
        console.error('Failed to start terminal process:', err);
        ws.send('\r\n\x1b[31m[ ERROR: Failed to start shell process ]\x1b[0m\r\n');
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
