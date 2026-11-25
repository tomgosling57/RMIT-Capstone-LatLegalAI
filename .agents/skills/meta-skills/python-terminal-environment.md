---
name: python-terminal-env
description: Instructions for using the agentic shell terminal correctly when running Python code. Use this skill whenever you are about to run Python scripts, install packages, execute agentic tasks in a terminal, or work with any project that has a requirements.txt or Python dependencies. Trigger before any bash_tool or terminal invocation that involves Python.
---

# Python Terminal Environment

The agentic terminal is a **shell terminal** (bash). Before running any Python code, you must activate the project's virtual environment. Do not assume Python packages are globally available.

---

## Step 1 — Activate the Virtual Environment

Always activate the virtual environment before running Python or installing packages:

```bash
. .venv/bin/activate
```

> Note: this uses `. ` (dot space), which is the POSIX-portable form of `source`. Both work in bash; prefer `. ` for compatibility.

Run this in the **project root** (the directory that contains `.venv/`). After activation, `python` and `pip` will resolve to the virtualenv's binaries.

---

## Step 2 — Locate the Requirements File

Before installing any dependency, find the `requirements.txt`:

### Check the root first
```bash
ls requirements.txt 2>/dev/null && echo "Found at root" || echo "Not at root"
```

### If not at root, search subdirectories
```bash
find . -name "requirements.txt" -not -path "./.venv/*" | head -20
```

Use the first result. If multiple are found, show them to the user and ask which to use.

---

## Step 3 — Add Dependencies to requirements.txt

**Never install a package without also adding it to `requirements.txt`.**

When you need a new dependency:

1. Add it to `requirements.txt` (use the file path found in Step 2):
   ```bash
   echo "package-name" >> requirements.txt
   # Or with a version pin:
   echo "package-name>=1.2.0" >> requirements.txt
   ```

2. Install from the file to keep the environment consistent:
   ```bash
   pip install -r requirements.txt
   ```

If you only need one package urgently, install it first then immediately add it:
```bash
pip install package-name
echo "package-name" >> requirements.txt
```

---

## Step 4 — Run Python Code

With the venv active and dependencies installed:

```bash
python script.py
# or
python -m module_name
```

---

## Full Setup Sequence (copy-paste ready)

```bash
# 1. Activate venv
. .venv/bin/activate

# 2. Find requirements.txt
REQS=$(find . -name "requirements.txt" -not -path "./.venv/*" | head -1)
echo "Using: $REQS"

# 3. Install dependencies
pip install -r "$REQS"

# 4. Run your script
python your_script.py
```

---

## Rules Summary

| Rule | Detail |
|------|--------|
| Always activate venv first | `. .venv/bin/activate` |
| Find requirements.txt before installing | Check root, then subdirs |
| Always record new deps | Add to `requirements.txt` before or immediately after installing |
| Never use global pip | All installs happen inside the activated venv |
| Prefer `pip install -r requirements.txt` | Keeps the environment reproducible |

---

## Common Issues

**`.venv` not found**
The project may not have a venv yet. Create one:
```bash
python3 -m venv .venv
. .venv/bin/activate
```

**`requirements.txt` not found anywhere**
Create it at the project root:
```bash
touch requirements.txt
```
Then add dependencies as you identify them.

**Wrong Python version**
Check which Python the venv uses:
```bash
python --version
```
If it's wrong, recreate the venv with the correct interpreter:
```bash
python3.11 -m venv .venv
```

**Package not found after install**
Make sure the venv is activated (your prompt should show `(.venv)`). If not, re-run `. .venv/bin/activate`.
