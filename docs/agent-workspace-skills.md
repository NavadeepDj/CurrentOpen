# Repository-Level AI Agent Skills

This document describes how the repository-level agent skills in the `skills/` directory guide future AI assistants (like Gemini and other agentic systems) to maintain the standards of the RailChart project.

---

## 🧭 What is a Workspace Agent Skill?

AI agents look for custom instructions, tools, and runbooks (known as "skills") to understand project-specific rules, schemas, and operational tasks.

In RailChart, we have created a dedicated repository skill:
- **Location:** [skills/train-data-management/SKILL.md](file:///C:/Users/navad/CurrentOpen/skills/train-data-management/SKILL.md)
- **Format:** Markdown file featuring YAML frontmatter (`name` and `description`) at the top of the file.

---

## 📐 Key Guidelines Contained in the Skill

The custom workspace skill codifies the core engineering rules of the project. Whenever a new AI agent works on this codebase, it will read `SKILL.md` and automatically follow these rules:

### 1. Dynamic Timetable Normalization
- Enforces the schema rules for `trains.json` (5-digit train numbers, UPPERCASE names/codes, Title Case names, and 24h `HH:MM` departure times).
- Explains how to invoke the automated scrapers/utilities.

### 2. Time-Boundary Logic Correctness
- Explains the three IRCTC charting prediction rules.
- **Rule of Boundary Check:** Enforces that time comparison boundary checks must always use **minutes-from-midnight** (e.g. `dep_hour * 60 + dep_minute`) rather than simple hour comparisons. This prevents off-by-minutes boundary condition bugs (e.g., matching a `14:05` departure to a `05:00-14:00` window).

### 3. Local Environment Upkeep (Windows-specific)
- Explains virtual environment activation and commands under `uv`.
- Resolves the missing timezone file issue (`ZoneInfoNotFoundError`) on Windows by specifying the `tzdata` requirement.
- Outlines how to identify and terminate blocking background processes on port `8000` to resolve socket access errors (`WinError 10013`).

### 4. UI Aesthetic & Performance Quality
- Preserves the default dark glassmorphism color palette and thin border guidelines.
- Preserves the countdown flip/tick character animations in `app.js`.
- Dictates that autocomplete dropdown inputs must be debounced by at least `280ms` to protect API endpoints against query flood.
