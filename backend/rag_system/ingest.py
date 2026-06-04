import os
import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from markitdown import MarkItDown
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from backend.rag_system.build_rules_md import build_all_rules_md, RULES_MD_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "DATA", "pdf_modules")
DB_DIR  = os.path.join(BASE_DIR, "DATA", "db")

_HEADER_SPLITS = [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]


def _split_markdown(markdown_text: str, source: str, doc_type: str) -> list:
    """
    Splits Markdown first by headers (preserving the context of each section),
    then breaks up overly large sections so they don't exceed the embedding window.
    """
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADER_SPLITS,
        strip_headers=False,
    )
    header_chunks = header_splitter.split_text(markdown_text)

    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = size_splitter.split_documents(header_chunks)

    for chunk in chunks:
        chunk.metadata["source"] = source
        chunk.metadata["doc_type"] = doc_type
    return chunks


# ---------------------------------------------------------------------------
# Campaign modules (PDF → Markdown → chunks)
# ---------------------------------------------------------------------------
def pdf_to_markdown(pdf_path: str) -> str:
    """Converts a PDF to clean Markdown using MarkItDown."""
    return MarkItDown().convert(pdf_path).text_content


def ingest_single_pdf(pdf_path: str, vector_store: Chroma) -> int:
    """Converts a PDF and adds its chunks to ChromaDB. Returns the number of chunks."""
    print(f"  [MarkItDown] Converting '{os.path.basename(pdf_path)}' to Markdown...")
    markdown_text = pdf_to_markdown(pdf_path)

    print("  [Splitter]   Splitting by headers and size...")
    chunks = _split_markdown(markdown_text, source=os.path.basename(pdf_path), doc_type="module")

    print(f"  [Chroma]     Storing {len(chunks)} chunks in the database...")
    vector_store.add_documents(chunks)
    return len(chunks)


# ---------------------------------------------------------------------------
# Hardcoded rules (JSON → Markdown → chunks), idempotent across startups
# ---------------------------------------------------------------------------
def _rules_hash(md_files: list[Path]) -> str:
    h = hashlib.sha256()
    for p in md_files:
        h.update(p.read_bytes())
    return h.hexdigest()


def ingest_rules_md(vector_store: Chroma, force: bool = False) -> int:
    """
    Generates the rules Markdown from the JSON and ingests it into the RAG.
    Replaces (does not duplicate) the previous rules chunks and skips the work
    if nothing changed since the last startup.
    """
    build_all_rules_md()

    md_files = sorted(Path(RULES_MD_DIR).glob("*.md"))
    if not md_files:
        print("  [Rules] No rules Markdown found.")
        return 0

    digest = _rules_hash(md_files)
    hash_file = os.path.join(DB_DIR, ".rules_hash")
    if not force and os.path.exists(hash_file):
        with open(hash_file, "r", encoding="utf-8") as f:
            if f.read().strip() == digest:
                print("  [Rules] Unchanged since last ingestion — skipping.")
                return 0

    # Remove the old rules chunks before reinserting (avoids duplicates)
    try:
        vector_store._collection.delete(where={"doc_type": "rules"})
    except Exception as e:
        print(f"  [Rules] Warning while clearing old rules: {e}")

    total = 0
    for path in md_files:
        chunks = _split_markdown(path.read_text(encoding="utf-8"), source=path.name, doc_type="rules")
        if chunks:
            vector_store.add_documents(chunks)
            total += len(chunks)

    os.makedirs(DB_DIR, exist_ok=True)
    with open(hash_file, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"  [Rules] {total} rules chunks ingested.")
    return total


# ---------------------------------------------------------------------------
# Persistent PDF modules (manifest-based, idempotent across startups)
# ---------------------------------------------------------------------------
_MANIFEST_FILE = os.path.join(DB_DIR, ".modules_manifest")


def _pdf_hash(pdf_path: str) -> str:
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _load_manifest() -> dict:
    if os.path.exists(_MANIFEST_FILE):
        with open(_MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest: dict) -> None:
    os.makedirs(DB_DIR, exist_ok=True)
    with open(_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def register_pdf_in_manifest(pdf_path: str) -> None:
    """Registers a PDF in the manifest after successful ingestion."""
    manifest = _load_manifest()
    manifest[os.path.basename(pdf_path)] = _pdf_hash(pdf_path)
    _save_manifest(manifest)


def ingest_pending_pdfs(vector_store: Chroma) -> int:
    """
    Automatically ingests any PDF in PDF_DIR that is not yet in the manifest
    (or whose hash has changed). Called at startup to ensure persistence.
    """
    manifest = _load_manifest()
    pdf_files = sorted(Path(PDF_DIR).glob("*.pdf"))
    if not pdf_files:
        return 0

    total = 0
    for pdf_path in pdf_files:
        name = pdf_path.name
        digest = _pdf_hash(str(pdf_path))
        if manifest.get(name) == digest:
            print(f"  [Modules] '{name}' already ingested — skipping.")
            continue
        print(f"  [Modules] Ingesting '{name}'...")
        total += ingest_single_pdf(str(pdf_path), vector_store)
        manifest[name] = digest

    if total:
        _save_manifest(manifest)
        print(f"  [Modules] {total} module chunks added.")
    return total


# ---------------------------------------------------------------------------
# Batch ingestion (standalone use)
# ---------------------------------------------------------------------------
def ingest_pdfs():
    """Ingests every PDF in PDF_DIR + the hardcoded rules. For script use."""
    print("Initializing the local embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    print("\n=== Hardcoded rules (JSON → Markdown) ===")
    ingest_rules_md(vector_store, force=True)

    print("\n=== Campaign modules (PDF) ===")
    pdf_files = list(Path(PDF_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF found in: {PDF_DIR}")
    else:
        total = 0
        for pdf_path in pdf_files:
            print(f"\nProcessing: {pdf_path.name}")
            total += ingest_single_pdf(str(pdf_path), vector_store)
        print(f"\n{total} module chunks stored.")

    print(f"\nIngestion complete! Database at {DB_DIR}")


if __name__ == "__main__":
    ingest_pdfs()
