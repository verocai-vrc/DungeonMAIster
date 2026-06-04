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
    Divide Markdown primeiro por cabeçalhos (preserva o contexto de cada secção),
    depois quebra secções demasiado grandes para não exceder a janela de embedding.
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
# Módulos de campanha (PDF → Markdown → chunks)
# ---------------------------------------------------------------------------
def pdf_to_markdown(pdf_path: str) -> str:
    """Converte um PDF para Markdown limpo usando MarkItDown."""
    return MarkItDown().convert(pdf_path).text_content


def ingest_single_pdf(pdf_path: str, vector_store: Chroma) -> int:
    """Converte um PDF e adiciona os seus chunks ao ChromaDB. Retorna o nº de chunks."""
    print(f"  [MarkItDown] A converter '{os.path.basename(pdf_path)}' para Markdown...")
    markdown_text = pdf_to_markdown(pdf_path)

    print("  [Splitter]   A dividir por cabeçalhos e tamanho...")
    chunks = _split_markdown(markdown_text, source=os.path.basename(pdf_path), doc_type="module")

    print(f"  [Chroma]     A guardar {len(chunks)} chunks na base de dados...")
    vector_store.add_documents(chunks)
    return len(chunks)


# ---------------------------------------------------------------------------
# Regras hardcoded (JSON → Markdown → chunks), idempotente entre arranques
# ---------------------------------------------------------------------------
def _rules_hash(md_files: list[Path]) -> str:
    h = hashlib.sha256()
    for p in md_files:
        h.update(p.read_bytes())
    return h.hexdigest()


def ingest_rules_md(vector_store: Chroma, force: bool = False) -> int:
    """
    Gera o Markdown das regras a partir do JSON e ingere-o no RAG.
    Substitui (não duplica) os chunks de regras anteriores e salta o trabalho
    se nada mudou desde o último arranque.
    """
    build_all_rules_md()

    md_files = sorted(Path(RULES_MD_DIR).glob("*.md"))
    if not md_files:
        print("  [Regras] Nenhum Markdown de regras encontrado.")
        return 0

    digest = _rules_hash(md_files)
    hash_file = os.path.join(DB_DIR, ".rules_hash")
    if not force and os.path.exists(hash_file):
        with open(hash_file, "r", encoding="utf-8") as f:
            if f.read().strip() == digest:
                print("  [Regras] Inalteradas desde a última ingestão — a saltar.")
                return 0

    # Remove os chunks de regras antigos antes de reinserir (evita duplicados)
    try:
        vector_store._collection.delete(where={"doc_type": "rules"})
    except Exception as e:
        print(f"  [Regras] Aviso ao limpar regras antigas: {e}")

    total = 0
    for path in md_files:
        chunks = _split_markdown(path.read_text(encoding="utf-8"), source=path.name, doc_type="rules")
        if chunks:
            vector_store.add_documents(chunks)
            total += len(chunks)

    os.makedirs(DB_DIR, exist_ok=True)
    with open(hash_file, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"  [Regras] {total} chunks de regras ingeridos.")
    return total


# ---------------------------------------------------------------------------
# Módulos PDF com persistência (manifest-based, idempotente entre arranques)
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
    """Regista um PDF no manifesto após ingestão bem-sucedida."""
    manifest = _load_manifest()
    manifest[os.path.basename(pdf_path)] = _pdf_hash(pdf_path)
    _save_manifest(manifest)


def ingest_pending_pdfs(vector_store: Chroma) -> int:
    """
    Ingere automaticamente qualquer PDF em PDF_DIR que ainda não esteja no manifesto
    (ou cujo hash tenha mudado). Chamado no arranque para garantir persistência.
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
            print(f"  [Módulos] '{name}' já ingerido — a saltar.")
            continue
        print(f"  [Módulos] A ingerir '{name}'...")
        total += ingest_single_pdf(str(pdf_path), vector_store)
        manifest[name] = digest

    if total:
        _save_manifest(manifest)
        print(f"  [Módulos] {total} chunks de módulos adicionados.")
    return total


# ---------------------------------------------------------------------------
# Ingestão em lote (uso standalone)
# ---------------------------------------------------------------------------
def ingest_pdfs():
    """Ingere todos os PDFs em PDF_DIR + as regras hardcoded. Para uso por script."""
    print("A inicializar o modelo de embeddings local...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    print("\n=== Regras hardcoded (JSON → Markdown) ===")
    ingest_rules_md(vector_store, force=True)

    print("\n=== Módulos de campanha (PDF) ===")
    pdf_files = list(Path(PDF_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"Nenhum PDF encontrado em: {PDF_DIR}")
    else:
        total = 0
        for pdf_path in pdf_files:
            print(f"\nA processar: {pdf_path.name}")
            total += ingest_single_pdf(str(pdf_path), vector_store)
        print(f"\n{total} chunks de módulos guardados.")

    print(f"\nIngestão concluída! Base de dados em {DB_DIR}")


if __name__ == "__main__":
    ingest_pdfs()
