# The Agentic Workflow Standard (2026)
A Guide to AGENTS.md and .agents/skills

In the past, we gave AI agents instructions via long chat messages or "Custom Instructions" that lived inside a specific app (like Cursor or Claude). The new standard moves these instructions into your codebase, making them portable, version-controlled, and context-efficient.

## 1. The Two-Layer Architecture

Modern agents use a "Progressive Disclosure" model to save tokens and stay sharp.

### Layer 1: AGENTS.md (The Signpost)
- **What it is**: A single file at the root of your project.
- **When it's used**: It is loaded every time you start a chat.
- **Purpose**: High-level project context. It tells the agent "where they are" and "what the house rules are."
- **Best for**: Tech stack (Python, Streamlit, spaCy, FastAPI, redis, pytest), build/test commands, and naming conventions.

### Layer 2: .agents/skills/ (The Toolbox)
- **What it is**: A directory containing sub-folders for specific tasks.
- **When it's used**: It is Lazy Loaded. The agent only reads the full instructions when it decides the task is relevant to your request.
- **Purpose**: Deep-dive "How-To" guides for complex workflows.
- **Best for**: Standardized processes like "Calibrate LiDAR," "Summarize Legal PDF," or "Deploy to Production."

## 2. Setting Up Your AGENTS.md

Create this file at your project root. Keep it under 150 lines to avoid "context bloat."

### Example Agents.md
    # Project: LatMatrix Legal AI 

    ## Tech Stack
    - Backend: FastAPI (Python 3.12)
    - Frontend: Streamlit
    - Database: Supabase (PostgreSQL)

    ## Critical Rules
    - Always use Type Hints in Python.
    - Never commit `.env` files.
    - For legal summarization tasks, use the `legal-summarizer` skill.

    ## Commands
    - Build: `docker-compose up --build`
    - Test: `pytest`
    - Lint: `ruff check .`


## 3. Creating Your First Skill

Skills live in .agents/skills/[skill-name]/. Each skill folder must have a SKILL.md file with YAML frontmatter.

### Example: .agents/skills/legal-summarizer/SKILL.md
    ---
    name: legal-summarizer
    description: Use this to simplify complex legal PDFs into plain-English summaries.
    ---

    # Legal Summarization Workflow
    When the user provides a legal document:
    1. Extract text using the `pdf_tool`.
    2. Categorize the document (Contract, Litigation, or Compliance).
    3. Use the "Executive Summary" template located in `./references/template.md`.
    4. Flag any "High Risk" clauses (indemnity, liability caps).

    ## Quality Checks
    - Ensure the summary is at a 10th-grade reading level.
    - Do not provide legal advice; only summarize.

## 4. Why This Matters (The Benefits)
- **Portability**: You can switch between Cursor, Claude Code, GitHub Copilot, or Windsurf, and they will all read the same files.
- **Efficiency**: Instead of the agent reading 5,000 lines of documentation every message, it only reads the name/description of your skills until it actually needs them.
- **Team Alignment**: When a teammate clones your repo, their AI agent instantly knows exactly how to write code that matches your style.

## 5. Pro-Tips
- **The "Closest Wins" Rule**: If you have a monorepo, you can put a second AGENTS.md inside a sub-folder (e.g., /frontend/AGENTS.md). The agent will prioritize the instructions closest to the file it is editing.
- **Executable Skills**: You can put a scripts/ folder inside a skill directory. The agent can then run those scripts automatically to perform the task described in the SKILL.md.
- **Symlinks**: If you are transitioning from an older tool (like .cursor/rules), you can simply symbolically link those folders into .agents/skills to keep them compatible with the new standard.