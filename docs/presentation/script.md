# LatLegal AI: Final Presentation Script

**Project:** AA868 Latmatrix Legal Summariser (LatLegal AI)
**Team:** 5 members


First, on behalf of our team, we want to say thank you to the LatMatrix team and RMIT for giving us this opportunity.


## Problem Solving

Before we talk about what we built, let's talk about *why* we built it.

Legal professionals deal with an enormous volume of documents: contracts, trusts, deeds, court filings, often hundreds of pages per document. Reading through every page manually to extract key information like parties, obligations, dates, and financial figures is time-consuming, error-prone, and expensive for clients.

The core problem is that legal document review is a **manual bottleneck**. A lawyer might spend hours reviewing a standard contract just to identify the termination clause, payment obligations, and signature requirements. For scanned documents, which many legacy legal files are, this process is even slower because the text is not machine-readable without OCR.

LatMatrix needed a tool that could:
1. Accept any legal document format: PDF, Word documents, scanned images, and plain text
2. Automatically extract the text, regardless of whether it was born-digital or scanned
3. Identify key legal entities: parties, dates, financial figures, and obligations
4. Summarise everything in plain English using AI
5. Do all of this securely, with proper file validation and access control

That's the gap we set out to fill with LatLegal AI.


## Project Goals

From the very beginning, we knew this project needed a structured approach. We gathered requirements directly from LatMatrix through an initial client meeting, where we presented a working prototype to validate the technical approach and secure buy-in.

Once the client signed off, we created a detailed plan:

- **Product backlog** in Jira, itemising every task and prioritising the most valuable items first
- **Weekly Sprints** mapped out across the semester, starting with a prototype and building up incrementally
- **Weekly stand-ups** with the client, team and mentor to demo progress, gather feedback, and adjust priorities
- **Story point estimation** to track velocity and predict delivery timelines

We began holding **regular client meetings** every week. These meetings were critical: they kept us aligned with LatMatrix's expectations, allowed us to pivot when requirements shifted, and ensured there were no surprises at the end of the project. We also attended weekly meetings without mentor, providing guidance on technical decisions and project management best practices.


## Technologies

The technologies we used were chosen deliberately to solve the problem at hand.

**Core stack:** Python was the language of choice; it has the best ecosystem for NLP, OCR, and AI integration.

**Document processing:** We built a parser framework with an abstract `BaseParser` class and factory pattern, supporting PDF (native and scanned via OCR), Word documents, and plain text. The `PDFTypeDetector` intelligently routes scanned PDFs to the OCR pipeline and digital PDFs to text extraction, with no manual intervention needed.

**NLP engine:** spaCy for named entity recognition, lemmatisation, and linguistic analysis. We tuned it specifically for legal text, filtering out boilerplate and generic terms.

**AI / LLM integration:** We started with six custom LLM backends (OpenAI, Anthropic, OpenRouter, Ollama, Mistral, Mock), but migrated to **LiteLLM**, a single unified interface supporting 100+ models. This was a key decision we discussed with the client, who agreed that provider flexibility was more valuable than custom integration.

**OCR pipeline:** Tesseract + pdf2image + OpenCV for scanned documents, supporting **7 languages**: English, Hindi, French, Spanish, German, Italian, and Portuguese.

**Frontend interfaces:** We built three user-facing interfaces: a **Flask website** for authentication and landing pages, a **Streamlit chat** as a prototype for the AI chat and document analysis which was superseded by **Chainlit** as our final unified conversational interface.

**Infrastructure:** Docker Compose orchestrating 6 services (Nginx, Flask, Streamlit, FastAPI, Chainlit, Redis), all behind an Nginx reverse proxy with WebSocket upgrades for real-time streaming.

**Database evaluation:** We compared Supabase against Firebase and recommended **Supabase (PostgreSQL)** for its scalability, structural integrity, and cost predictability when handling relational legal data. This recommendation was presented to and approved by the client however we decided to use SQLite with a database agnostic ORM during development for cost efficiency.


## Accountability & Team Participation

Accountability was built into our workflow from day one.

**Timesheets** were maintained throughout the project, tracking hours spent working on the project. This gave us visibility into individual contributions and helped the project lead allocate work fairly across the team.

**Regular meetings** were non-negotiable:
- **Weekly team stand-ups** every Wednesday: each member reported progress, blockers, and planned work. The project lead maintained a checklist of to-do's and developing items, delegated by priority.
- **Weekly mentor meetings** every Tuesday: we presented our progress to our academic mentor, who provided technical guidance, code review feedback, and project management advice.
- **Weekly client meetings** every Monday: we demoed working features to LatMatrix, gathered feedback, and adjusted the sprint backlog accordingly.

**Jira** was our single source of truth for accountability. Over **200 issues** were created across 9 sprints, with **90+ completed**. Each issue had an assignee, priority, story points, and status. We tracked personal velocity and team velocity sprint-by-sprint, using burndown charts to ensure we were on track.

**Pull request reviews** encouraged peer approval before merging. Our PR policy required at least one other team member or an AI agent to review the code before merge, catching issues early and distributing knowledge across the team. Agent skills and git actions were implemented to automate code reviews.


## Communication

Communication was the glue that held this project together.

**Microsoft Teams** was our primary communication platform. We used it for:
- **Team chat**: daily discussions, quick questions, sharing resources
- **Weekly mentor meetings**: screen sharing, code walkthroughs, technical guidance
- **File sharing**: design documents, meeting notes, reference materials

**Weekly meetings** followed a consistent structure:
1. **Monday (with client, 30 min to 1 hour):** Sprint planning, task assignment, blocker identification
2. **Tuesday (with mentor, 30 min):** Progress review, technical deep-dive, code review
3. **Wednesday (team only, 30 min):** Feature demo, feedback collection, requirement refinement

This cadence meant that no team member was ever more than a few days away from raising a concern or getting help. When conflicts arose, and they did, especially during the microservices migration where four team members were editing overlapping files, we resolved them in these meetings rather than letting them fester.


## GitHub

**GitHub** was central to our version control and collaboration strategy.

**Why GitHub?** We needed a platform that supported feature branching, pull requests, code review, and release management. GitHub provided all of this with a workflow that our team and client was already familiar with.

**Our branching strategy:**
- `main`: production releases, tagged by version (e.g., `v1.0.0`)
- `develop`: integration branch where features were merged and tested
- `feature/*`: individual features branched from `develop`
- `hotfix/*`: urgent fixes branched from `main`

**Pull request workflow:**
1. A developer created a feature branch from `develop`
2. Once complete, they opened a PR targeting `develop`
3. The PR triggered automated code reviews via our **GitHub PR code review skill**, which checked for security anti-patterns, duplicate code, path traversal vulnerabilities, and formatting drift
4. At least one other team member reviewed the code before merge
5. After testing on `develop`, changes were merged to `main` for release

**Quality control: merge gates.**
We only allowed merges into `main` at **milestone boundaries**, the end of each sprint, when the `develop` branch had been tested and signed off. This prevented half-finished features from reaching production. Within `develop`, we used stacked PR chains for larger features, keeping individual PRs small and reviewable.

The results: **35+ merged PRs** with over **250 commits** across five team members. Our largest PR, the Sprint 7 merge, was **+28,456 lines across 239 files**, a testament to how much the team could achieve in parallel when properly coordinated.

The automated PR reviews caught real issues: a hardcoded `chmod 777` in our Docker entrypoint, a path traversal vulnerability in the file saver, and duplicate `pdf_type_detector` code between the backend and frontend. All were flagged before they ever reached production.


## The Final Product

### Project Overview

LatLegal AI is a legal document summarisation platform that takes a document in any common format and produces a structured, AI-generated summary with key entities, section breakdowns, and plain-English explanations.

### What the System Actually Does

The document processing pipeline works like this:

```
Upload → ParserFactory.select_parser() → BaseParser subclass
       → PDFTypeDetector (native vs scanned) → OCR if needed
       → Text extraction → spaCy NLP (NER, lemmatisation)
       → LiteLLM summarisation → Summary + Entities + Sections
```

1. **Upload**: A user uploads a PDF, Word document, or text file through the Chainlit interface
2. **File validation**: Magic number verification, MIME type checking, extension whitelist, and UUID-based renaming, all before any processing begins
3. **Parser selection**: The `PDFTypeDetector` classifies the document as native, scanned, or mixed, and routes it to the correct parser
4. **Text extraction**: Native PDFs use pdfplumber; scanned PDFs go through Tesseract OCR with multilingual support; Word documents use python-docx with heading and table extraction
5. **NLP analysis**: spaCy identifies parties, dates, financial figures, locations, and legal entities, filtering out boilerplate and generic terms
6. **Section extraction**: LangChain prompt chains identify preamble, definitions, clauses, and signature blocks
7. **Summarisation**: LiteLLM generates a tailored summary via LangChain map-reduce chains, with streaming progress displayed in real-time
8. **Download**: Users can save the summary as a formatted Markdown file

### How Users Interact with It

Users interact with LatLegal AI through **Chainlit**, our unified conversational interface. The workflow is:

1. Open the Chainlit web interface at `/chat`
2. Upload a legal document (drag-and-drop or file picker)
3. The system immediately extracts the text and displays it in a clean Markdown format
4. Chainlit asks 2-3 clarifying questions to tailor the summary: *"Are you a party to this contract?"*, *"Are you focusing on obligations, risks, or both?"*
5. Based on the user's answers, LiteLLM generates a personalised summary
6. The summary is displayed with streaming progress, showing intermediate steps
7. Users can download the summary, ask follow-up questions, or upload a new document

### Best Technical Features

What makes this project technically impressive:

1. **PDF Type Detection**: The `PDFTypeDetector` analyses PDF structure to classify documents as native, scanned, or mixed, routing each page to the appropriate parser. This means a single document with both text and scanned pages is handled seamlessly.

2. **Multilingual OCR**: The OCR pipeline supports 7 languages with language-specific Tesseract configurations and font handling. Hindi Devanagari script, for example, required specific language packs and font setups that took dedicated effort to get right.

3. **Architecture Migration to Chainlit**: We are migrating all backend parsers, NLP processing, and entity extraction into Chainlit as native tools. This transforms FastAPI into a pure storage service, reducing the architecture from 6 services to a simpler model where document processing happens entirely within Chainlit. Shared utilities like magic number validation are extracted to a common directory and copied into Docker containers at build time, reducing code duplication without creating a whole new service.

4. **LiteLLM Integration**: We replaced six custom LLM backend classes (OpenAI, Anthropic, OpenRouter, Ollama, Mistral, Mock) with a single `litellm.acompletion()` call supporting 100+ models. This gives the client complete provider flexibility: they can switch models without changing a single line of application code.

5. **Real-Time Streaming**: SSE (Server-Sent Events) streaming displays summary generation in real-time, with chunk encoding fixes that required deep debugging of the Streamlit lifecycle.

6. **Comprehensive Error Handling**: Six custom exception types with global handlers, structured JSON error responses, and graceful degradation so that a failure in one pipeline stage (for example, LLM timeout) does not crash the entire request.

7. **Security-First Design**: Magic number validation (inspecting binary file headers), MIME type filtering, extension whitelisting, UUID-based file renaming, path traversal protection, and OAuth authentication with Google and Facebook.


## Conclusion

Working on LatLegal AI, we all had our sets of challenges. OCR quality varied significantly across different languages and fonts. The SSE streaming implementation had chunk encoding mismatches that took days to debug. The microservices migration introduced merge conflicts across four team members working in parallel. The Chainlit architecture migration required maintaining feature parity across two codebases simultaneously.

But we learned that the importance of this project was to set us up for the workforce in the future. There are going to be people, like us, who go into projects and frankly have new things to learn. The importance of this project is to embrace new challenges and show up every meeting a little bit better than the week before.

We weren't afraid to speak up and ask our mentors for help when necessary. We turned conflicts into opportunities to learn. Some days, we went out of our way to share resources and teach each other through one-on-one sessions. We understood that negligence would only hurt the integrity of the group; however, embracing each other's differences and sharing reinforced our existing knowledge and gave opportunity for someone to learn.

**Key metrics:**
- **250+ commits** across 5 contributors
- **35+ merged PRs**, largest at +28,456 lines
- **8 sprints** completed across 2.5 months
- **200+ Jira issues** created, 30+ completed
- **6 LLM backends** integrated, now consolidated to LiteLLM
- **4 parser types** plus PDF type detector
- **7 OCR languages** supported
- **30+ test files** spanning unit, integration, and E2E testing
- **6 Docker services** orchestrated behind Nginx


## Future Improvements

While we're proud of what we've built, there's always room to grow:

1. **Hybrid PDF handling**: Currently, documents that contain both text and scanned pages (hybrid PDFs) can be challenging. We would like to improve page-level classification so each page is routed to the optimal parser independently.

2. **User authentication and multi-tenancy**: Adding proper user accounts with document history, saved summaries, and role-based access control would make the product production-ready for law firms with multiple users.

3. **Expanded language support**: Our OCR pipeline supports 7 languages, but legal documents exist in many more. Adding support for East Asian languages (Chinese, Japanese, Korean) and right-to-left scripts (Arabic, Hebrew) would broaden the product's reach.

4. **Document comparison**: A feature that allows users to compare two versions of a contract and see what changed between them, a common workflow in legal practice.

5. **Batch processing**: Allowing users to upload multiple documents at once and receive a consolidated report, rather than processing one document at a time.

6. **On-premise deployment**: For law firms with strict data sovereignty requirements, providing a fully self-contained deployment option that does not rely on external LLM APIs would be valuable.


Again, we appreciate the LatMatrix team for supporting us and showing up each week, our mentors for guiding us through difficult situations, and RMIT for giving us a platform to excel.

Thank you so much.
