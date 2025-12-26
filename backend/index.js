const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const axios = require('axios');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8001';

app.use(cors());
app.use(bodyParser.json());

// Serve static files from the 'public' folder
app.use(express.static(path.join(__dirname, 'public')));

// In-memory User Database
const users = {};

// --- Auth Routes ---
app.post('/api/register', (req, res) => {
    const { username, email, password } = req.body;
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
        progress: { streak: 0, completed_modules: 0, total_study_time: 0 }
    };
    res.json({ message: "Registration successful" });
});

app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    const user = users[username];
    if (user && user.password === password) {
        res.json({ success: true, user });
    } else {
        res.status(401).json({ message: "Invalid credentials" });
    }
});

app.post('/api/user/profile', (req, res) => {
    const { username, profile } = req.body;
    if (!users[username]) return res.status(404).json({ message: "User not found" });

    users[username].profile = { ...users[username].profile, ...profile, onboarding_completed: true };
    res.json({ message: "Profile updated", user: users[username] });
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

// app.get('*', (req, res) => {
//     res.sendFile(path.join(__dirname, 'public', 'index.html'));
// });

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
