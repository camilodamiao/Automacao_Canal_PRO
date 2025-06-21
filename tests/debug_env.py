"""
Debug - Verificar carregamento do arquivo .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 50)
print("DEBUG - VERIFICANDO ARQUIVO .ENV")
print("=" * 50)

# Mostrar diretório atual
current_dir = Path.cwd()
print(f"\n📁 Diretório atual: {current_dir}")

# Verificar se a pasta config existe
config_dir = current_dir / "config"
print(f"\n📂 Pasta config existe? {config_dir.exists()}")

if config_dir.exists():
    print("📄 Arquivos na pasta config:")
    for file in config_dir.iterdir():
        print(f"   - {file.name}")

# Verificar se o arquivo .env existe
env_file = config_dir / ".env"
print(f"\n📄 Arquivo .env existe? {env_file.exists()}")

if env_file.exists():
    print(f"📍 Caminho completo: {env_file.absolute()}")
    print(f"📏 Tamanho do arquivo: {env_file.stat().st_size} bytes")

# Tentar carregar de diferentes formas
print("\n🔧 Tentando carregar o .env...")

# Método 1: Caminho relativo
print("\n1️⃣ Método 1: Caminho relativo")
load_dotenv('config/.env')
email1 = os.getenv('ZAP_EMAIL')
print(f"   Email: {email1}")

# Método 2: Caminho absoluto
print("\n2️⃣ Método 2: Caminho absoluto")
load_dotenv(env_file)
email2 = os.getenv('ZAP_EMAIL')
print(f"   Email: {email2}")

# Método 3: Usando Path
print("\n3️⃣ Método 3: Usando Path")
env_path = Path("config") / ".env"
load_dotenv(env_path)
email3 = os.getenv('ZAP_EMAIL')
print(f"   Email: {email3}")

# Mostrar todas as variáveis de ambiente que começam com ZAP
print("\n🔍 Variáveis ZAP encontradas:")
for key, value in os.environ.items():
    if key.startswith('ZAP'):
        # Ocultar parte da senha por segurança
        if 'PASSWORD' in key:
            print(f"   {key}: ***{value[-3:]}")
        else:
            print(f"   {key}: {value}")

# Se ainda não funcionar, vamos ler o arquivo diretamente
if not email1 and not email2 and not email3:
    print("\n⚠️ Nenhum método funcionou. Verificando conteúdo do arquivo...")
    if env_file.exists():
        print("\n📖 Conteúdo do arquivo .env:")
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # Ocultar senhas
                if 'PASSWORD' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        print(f"   Linha {i}: {parts[0]}=***")
                else:
                    print(f"   Linha {i}: {line.strip()}")
        
        print("\n💡 Possíveis problemas:")
        print("   - Espaços extras nas linhas?")
        print("   - Arquivo salvo com encoding errado?")
        print("   - Aspas nas variáveis?")

print("\n" + "=" * 50)