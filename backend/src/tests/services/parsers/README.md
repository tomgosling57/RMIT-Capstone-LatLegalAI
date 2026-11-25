# Parser Tests

## Running Tests

All parser tests should be run from the `backend/src/` directory with the project's
virtual environment activated:

```bash
cd backend/src
. /path/to/project/.venv/bin/activate
```

### Unit tests (no external dependencies)

```bash
python -m pytest tests/services/parsers/ -v
```

### Integration tests (require Tesseract + Poppler + asset files)

```bash
python -m pytest tests/services/parsers/ -m integration -v
```

### Multilingual OCR tests

The multilingual OCR tests require **Tesseract language packs** to be installed
for the languages being tested. See the note below for details.

```bash
python -m pytest tests/services/parsers/test_ocr_pdf_parser.py -m integration -k "Multilingual" -v
```

## Python Path

The `pytest.ini` in `backend/src/` sets `pythonpath = .`, which means the
`backend/src/` directory is on `sys.path`. All imports in the test files (e.g.
`from tests.conftest import assert_text_accuracy`) resolve relative to
`backend/src/`. **Always run pytest from the `backend/src/` directory** so that
the `pythonpath` setting works correctly.

## Tesseract Language Packs

The multilingual OCR integration tests pass a `lang` parameter to
[`OCRPDFParser.parse()`](../services/parsers/ocr_pdf_parser.py) to select the
appropriate Tesseract language model. The following language codes are used:

| Test class                  | `lang` parameter | Tesseract package          |
|-----------------------------|------------------|----------------------------|
| `TestMultilingualScannedHindi`   | `"hin"`      | `tesseract-ocr-hin`        |
| `TestMultilingualScannedFrench`  | `"fra"`      | `tesseract-ocr-fra`        |
| `TestMultilingualScannedSpanish` | `"spa"`      | `tesseract-ocr-spa`        |
| `TestMultilingualScannedGerman`  | `"deu"`      | `tesseract-ocr-deu`        |
| `TestMultilingualScannedMixedEnHi` | `"eng+hin"` | `tesseract-ocr-eng` + `tesseract-ocr-hin` |

**Without the corresponding Tesseract language packs installed, the multilingual
tests will fail** because Tesseract cannot load the required language data.

### Installing language packs (Debian / Ubuntu)

```bash
sudo apt-get install tesseract-ocr-hin tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-deu
```

### Installing language packs (macOS with Homebrew)

```bash
brew install tesseract-lang
```

### Verifying installed languages

```bash
tesseract --list-langs
```
