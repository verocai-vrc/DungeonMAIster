import os
import sys
import time
import webbrowser
import subprocess

def start():
    # Determina os diretórios com base na localização deste script
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    print("========================================")
    print("⚔️  Iniciando o DungeonMAIster... ⚔️")
    print("========================================")
    print("Subindo o servidor backend (FastAPI)...")
    
    # Inicia o Uvicorn usando o executável atual do Python (mantém compatibilidade com venv)
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
        cwd=base_dir
    )
    
    # Aguarda 2 segundos para dar tempo do servidor iniciar corretamente
    time.sleep(2)
    
    print("Abrindo a interface no navegador...")
    webbrowser.open("http://localhost:8000")
    
    try:
        print("\nO servidor está a rodar! Pressione Ctrl+C neste terminal para encerrar o jogo.")
        server_process.wait()
    except KeyboardInterrupt:
        print("\nEncerrando o motor do DungeonMAIster...")
        server_process.terminate()

if __name__ == "__main__":
    start()