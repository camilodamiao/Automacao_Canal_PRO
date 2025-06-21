# test_supabase.py

# >>> Carrega o config/.env
from dotenv import load_dotenv
load_dotenv("config/.env")
# <<<


import os
from supabase import create_client

# Carrega variáveis de ambiente
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("SUPABASE_URL:", url or "<não definida>")
print("SUPABASE_KEY:", "OK" if key else "<não definida>")

# Tenta conectar
try:
    supabase = create_client(url, key)
    # faz uma chamada simples (lista tabelas do esquema público)
    resultado = supabase.table("imoveis").select("*").limit(1).execute()
    print("Conexão com Supabase OK:", resultado.data is not None)
except Exception as e:
    print("Erro ao conectar ao Supabase:", e)
