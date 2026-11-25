# LatMatrix AI — Legal Document Assistant

Welcome to **LatMatrix AI**, an intelligent legal document analysis platform. Upload legal documents (PDF, DOCX, or TXT) and get AI-powered summaries, section breakdowns, and key insights — all within a conversational chat interface.

---

## Quick Start

1. **Log in** using your credentials or OAuth provider (Google, GitHub, etc.).
2. **Upload a document** by clicking the paperclip icon (📎) in the chat input area, then select a PDF, DOCX, or TXT file (max 5 MB).
3. **Wait for parsing** — the system extracts text locally, detects the document language, and sends it to the AI for analysis.
4. **Review the results** — extracted text, document statistics (pages, characters, language), and an AI-generated summary with key sections.
5. **Download the summary** as a **PDF** using the download buttons that appear after analysis.
6. **Ask follow-up questions** about the document in natural language.

---

## Features

### ✅ Implemented

| Feature | Description |
|---------|-------------|
| **Document Upload** | Upload PDF, DOCX, DOC, TXT, and MD files (up to 5 MB). |
| **PDF Parsing** | Native PDF text extraction + automatic detection of scanned PDFs with OCR fallback via Tesseract. |
| **Word Document Parsing** | Extract text from `.docx` and `.doc` files, including paragraphs and tables. |
| **Text File Parsing** | Parse plain text and Markdown files with automatic encoding detection. |
| **OCR Language Selection** | Set the OCR language for scanned documents from the settings panel (English, Hindi, French, Spanish, German, or auto-detect). |
| **Summary Language Selection** | Choose the language for AI-generated summaries: English, Hindi, French, Spanish, German, Chinese (Mandarin), Indonesian, Standard Arabic, Urdu, or Portuguese. |
| **AI-Powered Analysis** | Uses OpenRouter (DeepSeek model) to analyse extracted text, identify document sections, and explain their purpose. |
| **Section Summaries** | Ask for a section-by-section breakdown by typing "summarise sections" or clicking the **Summarise document sections** starter button. |
| **Download Extracted Text** | After analysis, click **Download Extracted Text** to save your document's raw text. |
| **Download Summary (PDF)** | After analysis, click **Download Summary** to save the AI-generated summary as a PDF document. |
| **Conversation Memory** | Chat history is preserved across the session. Resume previous conversations from the thread list. |
| **Authentication** | Password-based login (development) or OAuth (Google, GitHub, etc. in production). |
| **Multilingual OCR** | Tesseract-based OCR supporting English, Hindi, French, Spanish, and German. |

### 🔄 In Progress / Coming Soon

| Feature | Status |
|---------|--------|
| **Document Translation** | Translation support is on the roadmap. You can already ask the AI to explain sections in a different language using the **Summary Language** setting. |
| **Entity Extraction** | Named-entity recognition (people, organisations, dates, legal citations) is being integrated into the analysis pipeline. |
| **Clause Extraction** | Automatic identification and listing of key legal clauses is under development. |
| **Backend Storage Service** | Integration with the FastAPI storage backend for persistent document archiving. |
| **Advanced OCR Languages** | Additional language packs for Tesseract are being evaluated. |

---

## How to Use

### Uploading a Document

1. Click the paperclip icon (📎) next to the chat input.
2. Select a file from your computer (supported: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`).
3. Optionally, type a question about the document before sending (e.g., "What are the key clauses?").
4. Send the message. The system will:
   - Parse and extract the document text
   - Show document statistics (page count, character count, language)
   - Display the extracted text in the sidebar
   - Generate an AI summary with identified sections

### Changing Language Settings

Open the **settings panel** (⚙️ icon) in the top-right corner to adjust:

- **OCR Language** — The language used for text recognition in scanned PDFs. Set this if your scanned document is not in English.
- **Summary Language** — The language in which the AI will generate its responses and summaries.

### Requesting a Section Summary

You can either:
- Click the **Summarise document sections** starter button above the chat input
- Type a message like "summarise sections", "list sections", or "outline the document"

### Downloading Results

After a document has been analysed, click the action buttons that appear:
- **📄 Download Extracted Text** — saves the raw extracted text
- **📥 Download Summary** — saves the AI-generated summary as a **PDF**

### Asking General Questions

The AI assistant can answer general questions about legal concepts, document structure, and terminology — just type your question naturally. It is configured as a legal document assistant and will provide clear explanations while reminding you that it is not a substitute for professional legal advice.

---

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Native text extraction + automatic OCR fallback for scanned documents |
| Word | `.docx`, `.doc` | Paragraph and table extraction |
| Text | `.txt`, `.md` | Plain text and Markdown with encoding detection |

### File Size Limit

The maximum upload size is **5 MB**. Larger files will be rejected with a notification.

---

## Notes

- **Legal Disclaimer**: LatMatrix AI is an AI assistant and **not a substitute for professional legal advice**. Always consult a qualified legal professional for matters requiring legal expertise.
- **Privacy**: Document processing happens locally within the Chainlit service. Extracted text is sent to the LLM (via OpenRouter) for analysis. No documents are permanently stored on external servers.
- **OCR Accuracy**: Optical character recognition quality depends on the quality and clarity of scanned documents. For best results, upload digitally-native PDFs when available.

---

*LatMatrix AI — Built for LatMatrix*
