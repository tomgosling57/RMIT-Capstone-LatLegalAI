# Skill: Meta-Skill Writing & Governance

## Context
This skill provides the heuristic framework for generating, maintaining, and modularizing agentic skills. It ensures the system remains scalable without instruction bloat.

## Guidelines for Skill Creation
Create a new skill in `.agents/` only when one of the following criteria is met:
1. **Redundancy:** A specific setup or multi-step command sequence is performed more than twice.
2. **Complexity:** A task requires more than five unique constraints to be executed correctly.
3. **Domain Isolation:** A new tool, language, or specific project logic is introduced that differs from existing workflows.

## Structural Principles
* **Atomicity:** One skill = One logical domain. Avoid "Swiss Army Knife" skills.
* **Non-Redundancy:** Check existing files in `.agents/` before generating a new one to prevent conflicting instructions.
* **Portability:** Use relative paths and environment-agnostic commands where possible.
