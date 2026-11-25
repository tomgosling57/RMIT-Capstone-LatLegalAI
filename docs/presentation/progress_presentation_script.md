# LatLegal AI — Progress Presentation Script

**Project:** AA868 Latmatrix Legal Summariser (LatLegal AI)
**Team:** 4 members
**Date:** May 26, 2026

---

## Slide 1 — Title

> *(Everyone on stage)*

First, on behalf of the team, we want to say thank you to the LatMatrix team and RMIT for giving us this opportunity.

We're Team LatLegal AI, and today we're going to walk you through our progress on the LatMatrix Legal Summariser project.

---

## Slide 2 — Project Overview

> *(Speaker)*

So, what does LatLegal AI actually do?

At its core, it's a legal document summarisation platform. You upload a document — PDF, Word doc, scanned image, plain text — and it gives you back a structured, AI-generated summary with key entities, section breakdowns, and plain-English explanations.

**Why did we build this?**

Legal professionals deal with an enormous volume of documents. Contracts, trusts, deeds, court filings — often hundreds of pages. Reading through every page manually to find the important bits — parties, obligations, dates, financial figures — is incredibly time-consuming. It's error-prone. And it's expensive for clients.

A lawyer might spend hours reviewing a standard contract just to find the termination clause. For scanned documents — which many legacy legal files are — it's even worse because the text isn't machine-readable without OCR.

**Who's this for?**

Our client is LatMatrix, a legal technology company. But the end users are legal professionals — lawyers, paralegals, legal assistants — who need to review documents quickly and accurately.

**The purpose?**

To turn hours of manual document review into minutes of automated analysis.

---

## Slide 3 — Requirements & Goals

> *(Speaker)*

We gathered our requirements directly from LatMatrix in our first client meeting. We actually brought a working prototype to that meeting — a proof-of-concept summarisation script — which helped validate the technical approach and secure buy-in.

Here's what they needed:

- Accept any legal document format — PDF, Word, scanned images, plain text
- Automatically extract text whether it's born-digital or scanned
- Identify key legal entities — parties, dates, financial figures, obligations
- Summarise everything in plain English using AI
- Do all of this securely with proper file validation

**Team structure:**

- **Team Member** — Project lead, architecture, Chainlit, LLM integration, docs
- **Team Member** — Parsers, NLP, OCR, PDF detection, testing, Chainlit tools
- **Team Member** — Chat UI, authentication, file security, subscriptions
- **Team Member** — UI/UX design, branding, presentations

---

## Slide 4 — Sprint Progress

> *(Speaker)*

We've completed **8 sprints** over about 2.5 months, and we're currently in Sprint 9.

Let me walk you through the timeline:

**Sprint 1** — Before our first client meeting. We built a prototype command line script using pdfminer, spaCy, and OpenRouter just to prove the concept worked.

**Sprint 2** — Started building the actual parsers for PDF and Word documents. Created stub classes for the whole framework — parsers, NLP, LLM backends, OCR, summariser. Early OCR exploration began here.

**Sprint 3** — Completed all four parsers: TextParser, WordParser, PDFParser, and OCRPDFParser. Started NLP work, async refactoring, and initial entity extraction.

**Sprint 4** — Built the LLM backend framework with factory pattern. Integrated OpenAI, Anthropic, OpenRouter, and a Mock backend. Added OAuth authentication and branding.

**Sprint 5** — Built a document transformer for generating test documents. Integrated NLP results into the summarised output. Implemented secure file upload with magic number validation.

**Sprint 6** — Major API reorganisation. Consolidated all routes, built proper error handling with six custom exception types, created the test infrastructure, and wrote comparison reports for database and AI providers.

**Sprint 7** — A two-week sprint. Implemented SSE streaming, fixed truncation issues, added multilingual OCR support for 7 languages, and migrated from a monolith to a microservices architecture with Docker Compose.

**Sprint 8** — Document section extraction — preamble, definitions, clauses, signatures. Downloadable summaries. Started the big architecture migration to Chainlit.

**Sprint 9** — Currently in progress. UI polish, home navigation between website and chat, OAuth improvements.

**Key numbers:** 250+ commits, 35+ merged PRs, 200+ Jira issues created, 90+ completed.

---

## Slide 5 — Technology Stack

> *(Speaker)*

We chose Python as our core language because it has the best ecosystem for NLP, OCR, and AI integration.

**The services:**

- **FastAPI** on port 8000 — our backend API, now transitioning to a storage-only service
- **Flask** on port 5000 — the website for auth, home, and pricing pages
- **Streamlit** on port 8501 — our original chat interface, being superseded by Chainlit
- **Chainlit** on port 8001 — our unified conversational AI interface
- **Redis** — shared cache for document context and rate limiting
- **Nginx** — reverse proxy routing everything with WebSocket upgrades

**Document processing stack:**

- **spaCy** for named entity recognition and linguistic analysis
- **LiteLLM** — a single unified interface to 100+ models, replacing six custom backends
- **Tesseract + pdf2image + OpenCV** for OCR on scanned documents
- **pdfplumber** for native PDF extraction
- **python-docx** for Word documents
- **LangChain** for section extraction prompts

**Infrastructure:** Docker Compose orchestrating all 6 services, with Black, Flake8, and mypy enforcing code quality.

---

## Slide 6 — System Architecture

> *(Speaker)*

Here's how everything fits together.

*(Point to diagram)*

A user enters through Nginx on port 80. Nginx looks at the URL path and routes accordingly:

- Forward slash goes to the Flask website — home page, pricing, login
- `/app` goes to Streamlit — the legacy chat interface
- `/chat` goes to Chainlit — our primary AI interface

Chainlit handles document processing locally using parser tools we've migrated from the backend. No round-trip to FastAPI needed for text extraction anymore.

FastAPI now serves as a storage service. When Chainlit finishes processing a document, it stashes the result in Redis, and FastAPI picks it up via a callback.

Redis bridges the gap between the two — database 0 for document context, database 2 for rate limiting.

All services communicate over an internal Docker network.

**The migration we're doing:**

Originally, FastAPI handled everything — parsing, NLP, LLM calls, storage. We're moving all the processing logic into Chainlit as native tools. FastAPI becomes just a storage layer. This simplifies the architecture and reduces the number of services that need to be maintained.

We've also extracted shared utilities — like magic number validation — into a common [`shared/`](shared/) directory that gets copied into Docker containers at build time. No more duplicated code.

---

## Slide 7 — Features Completed

> *(Speaker)*

Let me run through what we've actually built.

**Document processing — fully working:**
- PDF parsing for native digital PDFs
- OCR PDF parsing for scanned documents using Tesseract
- Word document parsing with heading and table extraction
- Plain text parsing with encoding detection
- PDF type detection that automatically classifies documents as native, scanned, or mixed
- A factory pattern that selects the right parser automatically
- Multilingual OCR supporting 7 languages — English, Hindi, French, Spanish, German, Italian, Portuguese

**AI and NLP:**
- Entity extraction using spaCy — finds parties, dates, financial figures, locations
- Clause classification using regex patterns
- Section extraction using LangChain — identifies preamble, definitions, clauses, signature blocks
- LiteLLM integration replacing six custom backend classes with one unified call
- Real-time streaming responses so users see results as they're generated
- Downloadable summaries as formatted Markdown files

**Security:**
- Magic number validation — we inspect the binary file headers to verify file types
- MIME type filtering against a whitelist
- Extension whitelisting — only PDF, DOCX, TXT, and MD allowed
- UUID-based file renaming to prevent path traversal attacks
- Path traversal protection on all file operations

**User interface:**
- Chainlit conversational interface with file upload and streaming responses
- Flask website with home, pricing, and auth pages
- OAuth login with Google and Facebook
- Bidirectional navigation between website and chat
- Custom branding with logo, theme, and background

---

## Slide 8 — Web Application Walkthrough

> *(Speaker)*

Let me show you what users actually see.

**First — the Flask website.** This is the landing page at the root URL. It gives users an overview of the product, links to pricing, and buttons to log in or go to the chat interface.

**Authentication** — users can log in with email and password, or use Google or Facebook OAuth. In development mode, we have a mock OAuth that bypasses real credentials so we can test quickly.

**Then the Chainlit interface at `/chat`** — this is where the magic happens.

The workflow is:

1. Log in — password auth or OAuth
2. Upload a document — drag-and-drop or file picker
3. The system immediately extracts the text and displays it in clean Markdown format
4. It automatically identifies document sections — preamble, definitions, clauses, signatures
5. Users can ask follow-up questions about the document using the AI chat
6. They can download the extracted text or summary as a file

We've added a home icon button that links back to the Flask website, so users can navigate between the two interfaces easily. Chat history is persisted in SQLite, so returning users pick up where they left off.

**The Streamlit interface at `/app`** is still there as our legacy chat interface, but Chainlit is now our primary frontend.

---

## Slide 9 — Challenges & Learnings

> *(Everyone shares)*

**Technical challenges we faced:**

OCR quality varied significantly across languages. Hindi Devanagari script required specific language packs and font setups that took dedicated effort to get right.

The SSE streaming implementation had chunk encoding mismatches that took days to debug. We eventually replaced the whole approach with Streamlit's `st.write_stream()`.

When we migrated to microservices, four team members were editing overlapping files. The merge conflicts were real. We resolved them in our weekly stand-ups rather than letting them fester.

spaCy's memory usage was about 1GB per 100,000 characters. We had to increase the max length from 1 million to 5 million characters and add truncation warnings.

The Chainlit migration means we're maintaining feature parity across two codebases simultaneously. We're doing it incrementally — migrating one piece at a time.

**What we learned:**

> *(Speaker)*: "The importance of this project was to set us up for the workforce. There are going to be people who go into projects and have new things to learn. The key is to embrace new challenges and show up every meeting a little bit better than the week before."

> *(Speaker)*: "Building the parser framework taught me the value of abstraction. The factory pattern meant adding a new parser type didn't require changing any existing code."

> *(Speaker)*: "Debugging the SSE streaming issue taught me that frontend state management and async lifecycle interactions can be just as complex as backend logic."

> *(Speaker)*: "Designing for a legal tech product required understanding the user's context. Legal professionals need clarity, not flashy UI."


**Key takeaways:**

Weekly client meetings kept us aligned and prevented surprises. Automated PR reviews caught real security issues — a hardcoded `chmod 777`, a path traversal vulnerability — before they reached production. Jira as our single source of truth gave us visibility into who was doing what and how fast we were moving.

---

## Slide 10 — Current Progress & What's Left

> *(Speaker)*

**What we've finished:**

The document parsing pipeline is complete — PDF, DOCX, TXT, OCR, all working. PDF type detection, multilingual OCR, entity extraction, clause classification, section extraction — all done. LiteLLM integration, downloadable summaries, secure file upload, the Flask website, the Chainlit interface, OAuth authentication, Docker Compose orchestration, Nginx reverse proxy, the test suite — all complete.

We've migrated the parsers to Chainlit tools. We've migrated the NLP and entity extraction to Chainlit. We've got bidirectional navigation between the website and chat.

**What's still in progress:**

The Chainlit migration isn't fully finished — FastAPI is still transitioning to a pure storage service. We're working on hybrid PDF handling for documents that contain both text and scanned pages. User authentication and multi-tenancy is being built out. There's a duplicate `pdf_type_detector` that needs consolidating. And we're still tuning OCR quality across languages.

**Future improvements we've identified:**

Hybrid PDF handling with page-level classification. Proper user accounts with document history and role-based access. More languages — East Asian and right-to-left scripts. Document comparison so users can see what changed between two versions of a contract. Batch processing for multiple documents at once. And an on-premise deployment option for firms with data sovereignty requirements.

**Final numbers:**

250-plus commits, 35-plus merged PRs, 200-plus Jira issues, 8 sprints completed, 4 contributors, 6 Docker services, 4 parser types, 7 OCR languages, 30-plus test files, and 6 LLM backends consolidated down to one with LiteLLM.

---

## Closing

> *(Everyone)*

We want to thank LatMatrix for showing up every week and giving us clear, actionable feedback. Thank you to our mentors for guiding us through difficult situations. And thank you to RMIT for giving us a platform to excel.

We're happy to take any questions.
