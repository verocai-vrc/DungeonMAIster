import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Define os caminhos relativos à raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdf_modules")
DB_DIR = os.path.join(BASE_DIR, "data", "db")

def ingest_pdfs():
    print(f"A procurar PDFs na diretoria: {PDF_DIR}")
    
    # 1. Carregar PDFs da pasta
    loader = PyPDFDirectoryLoader(PDF_DIR)
    documents = loader.load()
    
    if not documents:
        print("Nenhum documento PDF encontrado. Adiciona alguns ficheiros à pasta data/pdf_modules/.")
        return

    print(f"Foram carregadas {len(documents)} páginas. A processar...")

    # 2. Dividir o texto em chunks (pedaços menores para a IA conseguir ler com facilidade)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"O texto foi dividido em {len(chunks)} chunks.")

    # 3. Inicializar o modelo de embeddings e guardar na BD
    print("A inicializar o modelo de embeddings local (pode demorar na 1ª vez para fazer o download)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"A guardar os embeddings na base de dados Chroma em: {DB_DIR}")
    vector_store = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=DB_DIR)
    
    print("Ingestão concluída com sucesso! O Mestre IA agora tem acesso a este conhecimento.")

if __name__ == "__main__":
    ingest_pdfs()