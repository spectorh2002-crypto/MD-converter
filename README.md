# Document to Markdown Converter

A Python app that converts supported document formats into Markdown (`.md`). It supports batch uploads, Google Drive links, pasted notes, OCR fallback for scanned PDFs, individual downloads, ZIP downloads, and merging content into a configurable number of Markdown files.

## Features

- **Document-only input:** PDF, DOCX, PPTX, XLSX, XLS, CSV, HTML/HTM, TXT, JSON, XML, EPUB, and MD.
- **Batch conversion:** Upload multiple documents at once.
- **Scanned PDF OCR:** Uses Tesseract OCR as a fallback when a PDF produces little or no extractable text.
- **Google Drive import:** Paste share links to supported files and Google Docs, Sheets, or Slides. Files must be accessible and appropriately shared.
- **Pasted notes:** Turn text pasted into the app into a Markdown file.
- **Preview and individual downloads:** Preview converted text and download each `.md` file.
- **ZIP export:** Download all converted Markdown files together.
- **Merge output:** Combine converted content into a chosen number of Markdown files, with source headings to separate documents.

## Tech stack

- Python
- Streamlit
- Microsoft MarkItDown
- PyMuPDF
- Tesseract OCR / `pytesseract`
- Pillow
- `gdown` and `requests`

## Project structure

```text
.
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer recommended.
- Tesseract OCR installed on your system for scanned-PDF OCR.
- An internet connection is needed to download files from Google Drive.

### Install Tesseract OCR

**Windows:** Install Tesseract OCR and ensure its installation directory is available on your system `PATH`. A common installer is available from the official UB Mannheim distribution: https://github.com/UB-Mannheim/tesseract/wiki

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS (Homebrew):**

```bash
brew install tesseract
```

## Run locally

1. Clone the repository:

   ```bash
   git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   cd YOUR-REPOSITORY
   ```

2. Create and activate a virtual environment (recommended):

   **Windows PowerShell**
   ```powershell
   python -m venv .venv
   .venv\\Scripts\\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL shown in the terminal (usually `http://localhost:8501`).

## How to use

1. Upload one or more supported documents, paste Google Drive links, and/or add notes.
2. Choose whether to enable scanned-PDF OCR fallback.
3. Optionally enable merging and select how many merged Markdown files to create.
4. Click **Convert documents**.
5. Preview results and download individual files, a ZIP of all converted files, and/or a ZIP of merged files.

## Push to GitHub

Create an empty repository on GitHub, then run these commands from the project folder:

```bash
git init
git add app.py requirements.txt .gitignore README.md
git commit -m "Add document to Markdown converter"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub username and repository name.

## Supported formats and notes

| Format | Extension(s) |
|---|---|
| PDF | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx`, `.xls` |
| CSV | `.csv` |
| HTML | `.html`, `.htm` |
| Plain text | `.txt` |
| JSON / XML | `.json`, `.xml` |
| EPUB | `.epub` |
| Markdown | `.md` |

- Conversion quality depends on the source file, layout, tables, images, and the underlying MarkItDown support.
- OCR is intended for text in scanned PDFs. It may not preserve page layout or complex formatting.
- Google Drive imports can fail if the file is private, blocked from export, or has restricted sharing permissions.
- The app currently converts documents to Markdown and merges Markdown outputs. It does **not** convert Markdown back into DOCX/PDF/PPTX.
- The app processes files in a temporary directory during a conversion session. Do not upload sensitive or confidential material unless you understand the environment and its privacy implications.

## License

Choose a license before publishing if you want to specify how others may use, modify, or distribute this project.
