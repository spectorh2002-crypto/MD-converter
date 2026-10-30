"""Document-to-Markdown converter with batch conversion and merging."""

from __future__ import annotations

import io
import os
import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote

import streamlit as st
import requests
import gdown
import pymupdf
import pytesseract
from PIL import Image
from markitdown import MarkItDown

APP_TITLE = "Document to Markdown Converter"
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".html", ".htm",
    ".txt", ".json", ".xml", ".epub", ".md",
}


def is_document(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def normal_convert(path: str) -> str:
    """Convert a supported document to Markdown using MarkItDown."""
    return MarkItDown().convert(path).text_content or ""


def ocr_pdf(path: str) -> str:
    """Extract text from scanned PDF pages using Tesseract OCR."""
    pages = []
    with pymupdf.open(path) as pdf:
        for page in pdf:
            pix = page.get_pixmap(dpi=200, alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(pytesseract.image_to_string(image))
    return "\n\n".join(pages).strip()


def convert_file(path: str) -> tuple[str, bool]:
    """Return (markdown text, whether OCR was used)."""
    if not is_document(path):
        raise ValueError(f"Unsupported file type: {Path(path).suffix or '(no extension)'}")
    text = normal_convert(path)
    if Path(path).suffix.lower() == ".pdf" and len(text.strip()) < 50:
        return ocr_pdf(path), True
    return text, False


def output_name(filename: str) -> str:
    return f"{Path(filename).stem or 'converted_document'}.md"


def download_google_drive_file(url: str, workdir: str) -> str:
    """Download a shared Google Drive file or export a Google Workspace document."""
    match = re.search(
        r"docs\.google\.com/(document|spreadsheets|presentation)/d/([\w-]+)", url
    )
    if match:
        kind, file_id = match.groups()
        fmt = {
            "document": "docx",
            "spreadsheets": "xlsx",
            "presentation": "pptx",
        }[kind]
        response = requests.get(
            f"https://docs.google.com/{kind}/d/{file_id}/export?format={fmt}",
            timeout=120,
        )
        response.raise_for_status()
        if "text/html" in response.headers.get("Content-Type", ""):
            raise ValueError("Could not export this file. Check its link-sharing permissions.")
        disposition = response.headers.get("Content-Disposition", "")
        found = re.search(r"filename\*=UTF-8''([^;]+)", disposition) or re.search(
            r'filename="([^"]+)"', disposition
        )
        name = unquote(found.group(1)) if found else f"{file_id}.{fmt}"
        target = os.path.join(workdir, os.path.basename(name))
        with open(target, "wb") as file:
            file.write(response.content)
        return target

    downloaded = gdown.download(url, output=workdir + os.sep, fuzzy=True, quiet=True)
    if not downloaded:
        raise ValueError("Download failed. Check that the Drive file is shared with access.")
    return downloaded


def split_groups(items: list[dict], number: int) -> list[list[dict]]:
    if not items:
        return []
    number = max(1, min(number, len(items)))
    quotient, remainder = divmod(len(items), number)
    groups = []
    start = 0
    for index in range(number):
        size = quotient + (1 if index < remainder else 0)
        groups.append(items[start:start + size])
        start += size
    return groups


def make_zip(files: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files:
            archive.writestr(name, content)
    return buffer.getvalue()


def safe_markdown_bytes(text: str) -> bytes:
    return text.encode("utf-8")


st.set_page_config(page_title=APP_TITLE, page_icon="📝", layout="wide")
st.title("📝 Document to Markdown Converter")
st.write(
    "Convert supported documents into Markdown, process multiple files, "
    "and combine converted content into fewer Markdown files."
)
st.info(
    "Supported formats: PDF, DOCX, PPTX, XLSX, XLS, CSV, HTML, TXT, JSON, XML, EPUB, and MD."
)

with st.sidebar:
    st.header("Conversion options")
    enable_ocr = st.checkbox("Use OCR fallback for scanned PDFs", value=True)
    merge_enabled = st.checkbox("Create merged Markdown files", value=True)
    merged_count = st.number_input(
        "Number of merged output files", min_value=1, max_value=50, value=2, step=1,
        disabled=not merge_enabled,
    )
    st.caption("OCR requires Tesseract OCR to be installed on the machine running this app.")

uploaded_files = st.file_uploader(
    "Upload document(s)",
    type=[ext.lstrip(".") for ext in sorted(ALLOWED_EXTENSIONS)],
    accept_multiple_files=True,
    help="Only document formats are accepted.",
)

st.subheader("Optional: import from Google Drive")
drive_text = st.text_area(
    "Paste share links (one URL per line)",
    placeholder="https://drive.google.com/file/d/...\nhttps://docs.google.com/document/d/...",
)
st.caption("Google Drive links must be accessible to you and shared appropriately.")

st.subheader("Optional: add pasted notes")
notes_name = st.text_input("Notes filename", value="pasted_notes")
notes_text = st.text_area("Paste text to convert into a Markdown file", height=130)

if st.button("Convert documents", type="primary", use_container_width=True):
    with tempfile.TemporaryDirectory(prefix="md_converter_") as workdir:
        inputs: list[tuple[str, str]] = []

        for uploaded in uploaded_files or []:
            if not is_document(uploaded.name):
                st.warning(f"Skipped unsupported file: {uploaded.name}")
                continue
            target = os.path.join(workdir, os.path.basename(uploaded.name))
            with open(target, "wb") as file:
                file.write(uploaded.getvalue())
            inputs.append((uploaded.name, target))

        for url in [line.strip() for line in drive_text.splitlines() if line.strip()]:
            if not url.startswith(("https://", "http://")):
                st.warning(f"Skipped invalid URL: {url}")
                continue
            try:
                target = download_google_drive_file(url, workdir)
                if is_document(target):
                    inputs.append((os.path.basename(target), target))
                else:
                    st.warning(f"Skipped unsupported Drive file: {os.path.basename(target)}")
            except Exception as exc:
                st.error(f"Could not download {url}: {exc}")

        if notes_text.strip():
            clean_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", notes_name.strip()).strip("._")
            clean_stem = clean_stem or "pasted_notes"
            if not clean_stem.lower().endswith(".txt"):
                clean_stem += ".txt"
            notes_path = os.path.join(workdir, clean_stem)
            with open(notes_path, "w", encoding="utf-8") as file:
                file.write(notes_text.strip())
            inputs.append((clean_stem, notes_path))

        if not inputs:
            st.warning("Upload at least one supported document, paste a Google Drive link, or add notes.")
            st.stop()

        converted: list[dict] = []
        progress = st.progress(0, text="Starting conversion…")
        for index, (original_name, path) in enumerate(inputs, start=1):
            try:
                markdown, used_ocr = convert_file(path)
                if not enable_ocr and used_ocr:
                    # Re-run only the standard converter when OCR fallback is disabled.
                    markdown = normal_convert(path)
                    used_ocr = False
                name = output_name(original_name)
                converted.append({
                    "original": original_name,
                    "name": name,
                    "text": markdown,
                    "ocr": used_ocr,
                })
                st.success(f"Converted **{original_name}** → `{name}`" + (" (OCR)" if used_ocr else ""))
            except Exception as exc:
                st.error(f"Failed to convert **{original_name}**: {exc}")
            progress.progress(index / len(inputs), text=f"Processed {index} of {len(inputs)} input(s)")

        progress.empty()
        if not converted:
            st.error("No files could be converted.")
            st.stop()

        # Avoid overwriting entries when uploaded files have identical basenames.
        seen: dict[str, int] = {}
        for item in converted:
            seen[item["name"]] = seen.get(item["name"], 0) + 1
            if seen[item["name"]] > 1:
                stem = Path(item["name"]).stem
                item["name"] = f"{stem}_{seen[item['name']]}.md"

        st.subheader("Conversion results")
        st.write(f"Successfully converted **{len(converted)}** of **{len(inputs)}** input(s).")
        for item in converted:
            with st.expander(f"{item['name']} — source: {item['original']}"):
                st.text_area(
                    f"Preview: {item['name']}", item["text"][:12000],
                    height=220, key=f"preview_{item['name']}",
                )
                st.download_button(
                    "Download Markdown",
                    data=safe_markdown_bytes(item["text"]),
                    file_name=item["name"],
                    mime="text/markdown",
                    key=f"download_{item['name']}",
                )

        st.download_button(
            "Download all converted files (.zip)",
            data=make_zip([(item["name"], safe_markdown_bytes(item["text"])) for item in converted]),
            file_name="converted_markdown_files.zip",
            mime="application/zip",
            use_container_width=True,
        )

        if merge_enabled and converted:
            groups = split_groups(converted, int(merged_count))
            merged_files = []
            for index, group in enumerate(groups, start=1):
                body = "\n\n---\n\n".join(
                    f"## Source: {item['original']}\n\n{item['text']}" for item in group
                )
                filename = f"merged_{index}_of_{len(groups)}.md"
                merged_files.append((filename, safe_markdown_bytes(body)))
            st.subheader("Merged Markdown")
            st.write(f"Created {len(merged_files)} merged file(s).")
            st.download_button(
                "Download merged Markdown files (.zip)",
                data=make_zip(merged_files),
                file_name="merged_markdown_files.zip",
                mime="application/zip",
                use_container_width=True,
            )

st.divider()
st.caption("Files are processed in a temporary directory during the session. Avoid uploading confidential documents to services you do not control.")
