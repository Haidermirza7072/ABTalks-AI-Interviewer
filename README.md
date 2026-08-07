# 🤖 ABTalks AI Interview Agent

> **An Adaptive AI-Powered Technical Interviewer for the ABTalks 31-Day AI Cohort**

---

## 🚀 Overview

ABTalks AI Interview Agent is an intelligent technical interviewer designed to simulate a realistic software engineering interview.

Instead of asking static questions, the agent analyzes a candidate's learning journey, adapts to previous responses, generates contextual follow-up questions, maintains conversation memory, and provides structured feedback at the end of the interview.

The goal is to help learners evaluate their understanding of AI engineering concepts while preparing them for real-world technical interviews.

---

## ✨ Features

* 🧠 Adaptive AI Interview Experience
* 💬 Multi-turn Technical Conversations
* 🔄 Intelligent Follow-up Questions
* 📚 Curriculum-Aware Question Generation
* 👤 Candidate Profile Personalization
* 📝 Structured Interview Feedback
* 🧩 Context & Memory Management
* ⚡ Fast API Backend
* 🎨 Modern Next.js Frontend
* 📱 Clean & Responsive User Interface

---

## 🎯 Problem Statement

This project is built for the **ABTalks Vibe Code Hackathon – Problem Statement 2**.

The objective is to build an AI Interview Agent capable of:

* Conducting a conversational technical interview
* Asking adaptive questions
* Maintaining interview context
* Evaluating candidate responses
* Providing actionable interview feedback

---

# 🏗 Tech Stack

### Frontend

* Next.js
* React
* Tailwind CSS
* TypeScript

### Backend

* FastAPI
* Python

### AI

* Gemini API
* Prompt Engineering

### Data

* JSON Curriculum
* Candidate Profiles

### Optional

* ChromaDB
* Supabase
* LangChain
* RAG

---

# 📂 Project Structure

```text
abtalks-ai-interviewer/

├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── utils/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── prompts/
│   ├── agents/
│   └── models/
│
├── data/
│   ├── curriculum.json
│   └── candidates.json
│
├── PROMPTS.md
├── README.md
└── requirements.txt
```

---

# ⚙️ How It Works

```text
Candidate Profile
        │
        ▼
Curriculum Loader
        │
        ▼
Interview Planner
        │
        ▼
Gemini AI
        │
        ▼
Adaptive Questions
        │
        ▼
Follow-up Questions
        │
        ▼
Interview Memory
        │
        ▼
Final Evaluation Report
```

---

# 🧠 AI Capabilities

Our AI interviewer can:

* Understand candidate progress
* Select questions dynamically
* Generate intelligent follow-up questions
* Maintain interview context
* Evaluate responses
* Generate personalized feedback

---

# 📋 Interview Flow

1. Candidate Profile Loaded
2. Curriculum Analysis
3. Personalized Interview Starts
4. AI Generates Questions
5. Candidate Responds
6. AI Creates Follow-up Questions
7. Context is Preserved
8. Interview Ends
9. Feedback Report Generated

---

# 📦 API Endpoints

## Start Interview

```http
POST /api/interview/start
```

---

## Submit Response

```http
POST /api/interview/respond
```

---

## Generate Feedback

```http
GET /api/interview/report
```

---

# 📸 Screens

* Landing Page
* Candidate Dashboard
* Interview Screen
* AI Thinking State
* Interview Summary
* Final Feedback Report

---

# 🎨 Design Principles

* Clean Interface
* Mobile Friendly
* Modern Components
* Minimal Distractions
* Smooth Animations
* Interview-Focused Experience

---

# 🚀 Local Setup

Clone the repository

```bash
git clone https://github.com/your-username/abtalks-ai-interviewer.git
```

Frontend

```bash
cd frontend
npm install
npm run dev
```

Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

# 🔑 Environment Variables

```env
GEMINI_API_KEY=your_api_key
```

---

# 💡 Future Improvements

* Voice Interview
* Live Coding Support
* Resume Analysis
* AI Score Comparison
* Interview History
* PDF Reports
* Recruiter Dashboard

---

# 👥 Team

| Member | Responsibility                                          |
| ------ | ------------------------------------------------------- |
| Haider | Frontend Development (Next.js / React)                  |
| Shesh  | Backend Development, AI Integration, Prompt Engineering |
| Vishal | AI Architecture, RAG, ChromaDB, Agentic AI, MLOps       |

---

# 📜 AI Usage

This project was developed using AI-assisted development during the ABTalks Vibe Code Hackathon.

All prompts and AI-assisted workflows are documented in **PROMPTS.md**.

---

# 📄 License

This project is developed exclusively for the **ABTalks Vibe Code Hackathon**.

---

<div align="center">

### 🤖 Built with AI • Designed for Learning • Engineered for Interviews

**ABTalks AI Interview Agent**

</div>
