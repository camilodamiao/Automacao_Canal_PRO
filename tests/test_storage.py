import os
from supabase import create_client
from dotenv import load_dotenv

# 1) Carrega o .env no caminho config/.env
load_dotenv('config/.env')

# 2) Lê as variáveis
url    = os.getenv("SUPABASE_URL")
key    = os.getenv("SUPABASE_KEY")
bucket = os.getenv("SUPABASE_BUCKET")

# 3) Valida
if not (url and key and bucket):
    print("❌ Defina SUPABASE_URL, SUPABASE_KEY e SUPABASE_BUCKET no .env")
    exit(1)

# 4) Conecta
supabase = create_client(url, key)

# 5) Lista o conteúdo do bucket
try:
    files = supabase.storage.from_(bucket).list()
    print("Arquivos no bucket:", files)
except Exception as e:
    print("❌ Erro ao listar bucket:", e)
    exit(1)
