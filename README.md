# project-helper

An AI-powered web app that clones, analyzes, and explains open-source codebases in plain language with real-time progress and interactive Q&A.

## Overview

`project-helper` is a source-code learning assistant for open-source projects.

Users paste a public GitHub repository URL, and the system will:

- clone or download the repository automatically
- analyze the codebase structure
- generate a beginner-friendly report
- cache analyzed projects to avoid duplicate work
- answer follow-up questions by searching the actual source code
- stream both analysis progress and chat output in real time

The goal is simple: help people understand unfamiliar codebases without feeling overwhelmed.

## Highlights

- Beginner-friendly project reports
  Explains project overview, tech stack, directory structure, core modules, data flow, design patterns, and reading tips in plain language.

- Real-time analysis progress
  Uses SSE to push cloning, scanning, and report-generation progress back to the frontend.

- Interactive code Q&A
  Lets the assistant inspect files, search code, and answer questions with concrete file references.

- Smart cache
  Reuses previously analyzed repositories instead of repeating expensive work.

- GitHub network fallback
  If `git clone` cannot reach `github.com`, the backend falls back to downloading source archives from `codeload.github.com`.

## Tech Stack

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- LangChain
- DeepSeek-compatible chat model integration

### Frontend

- Vue 3
- Vite
- Markdown-it
- highlight.js

## Architecture

```text
Vue Frontend
  |- Repository input
  |- Progress stream (SSE)
  |- Report viewer
  `- Interactive Q&A panel

FastAPI Backend
  |- Project analysis API
  |- SSE event streaming
  |- Repository manager
  |- Report builder
  |- LangChain-powered Q&A service
  `- SQLite persistence

Local Storage
  |- Cloned / downloaded repositories
  |- Cached analysis results
  `- Chat session history
```

## Main Features

### 1. Analyze a public GitHub repository

Submit a URL such as:

```text
https://github.com/owner/repo
```

The backend will normalize the URL, check cache, fetch the code, and generate a structured report.

### 2. Read a structured report

The generated report includes:

- project overview
- tech stack
- directory structure
- core modules
- data flow
- design patterns
- reading guide

### 3. Ask source-code questions

After analysis, users can continue asking things like:

- Where is the entry point?
- Which module loads the data?
- How does the request flow work?
- What should I read first?

The assistant searches the repository and responds with source-backed answers.

## UI Direction

The frontend uses a soft anime-inspired visual style:

- warm pastel colors
- rounded glassmorphism cards
- readable content spacing
- syntax-highlighted code blocks
- a split workspace for history, report reading, and chat

## Quick Start

### 1. Start the backend

```bash
cd backend
python -m pip install --default-timeout=1000 -e .[dev]
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

```text
http://127.0.0.1:5173
```

Backend default URL:

```text
http://127.0.0.1:8000
```

## Environment Variables

Create `backend/.env` based on `backend/.env.example`:

```env
PROJECT_HELPER_DEEPSEEK_API_KEY=your_api_key
PROJECT_HELPER_DEEPSEEK_BASE_URL=https://api.deepseek.com
PROJECT_HELPER_DEEPSEEK_MODEL=deepseek-v4-flash
PROJECT_HELPER_DATABASE_URL=sqlite+aiosqlite:///./project-helper.db
PROJECT_HELPER_WORKSPACE_ROOT=./workspace
```

If no DeepSeek key is configured, the app still works in local fallback mode for analysis and Q&A.

## Development

### Backend tests

```bash
python -m pytest backend/tests
```

### Frontend tests

```bash
cd frontend
npm test
```

### Frontend production build

```bash
cd frontend
npm run build
```

## Project Structure

```text
project-helper/
|- backend/
|  |- app/
|  |  |- analyzers/
|  |  |- api/
|  |  |- core/
|  |  `- services/
|  `- tests/
|- frontend/
|  |- src/
|  |  |- components/
|  |  `- utils/
|  `- tests/
`- README.md
```

## Current Status

Implemented:

- full-stack runnable app
- project analysis API
- cached project history
- real-time analysis progress
- structured report rendering
- source-code Q&A
- streaming chat output
- repository download fallback for restricted GitHub environments

## Roadmap

- richer report generation using stronger repository summarization prompts
- better code reference extraction and citation formatting
- re-run analysis for updated repositories
- side-by-side file viewer in chat answers
- export report to Markdown or PDF
- GitHub Actions CI

## Notes

- Only public GitHub repositories are supported right now.
- Runtime cache and cloned repositories are stored locally and ignored by Git.
- Sensitive keys are not committed; use `backend/.env` locally.
