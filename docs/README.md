# document_transformer

Command-line tool for generating test document assets in multiple formats and layouts from plain-text input. Used to create the sample files required by the Chainlit and backend test suites.

**Location:** `backend/src/scripts/document_transformer/`

---

## What it does

`transform_docs.py` takes plain-text content and renders it into one or more of the following output formats:

| Format | Description |
|---|---|
| `pdf` | Digital PDF with proper Unicode support (via WeasyPrint) |
| `docx` | Microsoft Word document (via python-docx) |
| `scanned_pdf` | PDF rendered to look like a scanned document (via ReportLab + image processing) |
| `txt` | Plain text file |

Each format can be generated in one or more **layouts**:

| Layout | Description |
|---|---|
| `single` | Single-column layout |
| `double` | Two-column layout |
| `multi` | Multi-column layout |

---

## Dependencies

The script uses libraries already listed in the backend `requirements.txt`:

```
fpdf2>=2.8
weasyprint>=68.0
python-docx>=1.1
reportlab>=3.6
pillow>=10.0
opencv-python-headless>=4.8
```

Install them from the backend requirements file:

```bash
pip install -r backend/requirements.txt
```

### System dependencies

```bash
# Ubuntu / Debian
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0

# macOS (Homebrew)
brew install pango gdk-pixbuf
```

---

## Usage

Run the script from the project root or from within the `document_transformer` directory.

```bash
cd backend/src/scripts/document_transformer
```

### Process all `.txt` files in `./input` → `./output` (all formats, all layouts)

```bash
python transform_docs.py
```

### Custom input/output directories

```bash
python transform_docs.py --input-dir /data/raw --output-dir /data/docs
```

### Process a single file

```bash
python transform_docs.py --file my_contract.txt
```

### Provide inline text

```bash
python transform_docs.py --text "This agreement is entered into..." --stem my_contract
```

### Generate only specific formats

```bash
python transform_docs.py --formats pdf docx
```

### Generate only specific layouts

```bash
python transform_docs.py --layouts single double
```

### Combine filters

```bash
python transform_docs.py --file contract.txt --formats pdf scanned_pdf --layouts single
```

### List all available formats and layouts, then exit

```bash
python transform_docs.py --list
```

### Suppress progress output (machine-readable — prints one output path per line)

```bash
python transform_docs.py --quiet
```

---

## Environment Variables

These can be set to override the default input/output directories. CLI flags (`--input-dir`, `--output-dir`) take precedence over environment variables.

| Variable | Default | Description |
|---|---|---|
| `INPUT_DIR` | `./input` | Directory containing `*.txt` source files |
| `OUTPUT_DIR` | `./output` | Directory where generated documents are written |

---

## Generating Test Assets for the Chainlit / Backend Test Suite

The test suite in `tests/unit/` and `tests/e2e/` expects sample document files (PDF, DOCX, scanned PDF, etc.) to test upload and processing flows.

**Step 1:** Create source text files in the `input/` directory (relative to the script):

```bash
mkdir -p backend/src/scripts/document_transformer/input
echo "This agreement is made between Party A and Party B..." \
  > backend/src/scripts/document_transformer/input/contract.txt
```

**Step 2:** Run the transformer to generate all formats:

```bash
cd backend/src/scripts/document_transformer
python transform_docs.py --formats pdf docx scanned_pdf txt --layouts single
```

**Step 3:** Copy the generated files into the test assets directory:

```bash
cp output/* tests/frontend/
```

The `tests/frontend/` directory already contains pre-generated sample assets (`contract.pdf`, `contract.docx`, `contract.txt`, `sample.jpg`, `sample.png`) committed to the repository. Re-run this process if you need to regenerate or add new test documents.

---

## Full CLI Reference

```
usage: transform_docs [-h] [--file PATH | --text STRING] [--stem NAME]
                      [--input-dir DIR] [--output-dir DIR]
                      [--formats FMT [FMT ...]] [--layouts LAYOUT [LAYOUT ...]]
                      [--list] [--quiet]

options:
  -h, --help                  show this help message and exit
  -f, --file PATH             Path to a single .txt source file
  -t, --text STRING           Inline plain-text string
  -s, --stem NAME             Base name for output files when using --text (default: document)
  -i, --input-dir DIR         Directory containing *.txt source files
  -o, --output-dir DIR        Directory where generated files are written
  --formats FMT [FMT ...]     Formats to generate: pdf docx scanned_pdf txt
  --layouts LAYOUT [LAYOUT ...] Layouts to generate: single double multi
  --list                      Print available formats and layouts, then exit
  -q, --quiet                 Suppress progress output; print one output path per line
```