# test_insert_imovel.py

# >>> Carrega o config/.env
from dotenv import load_dotenv
load_dotenv("config/.env")
# <<<

import os
from supabase import create_client, Client
from datetime import datetime

# Conecta ao Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Dados de exemplo
imovel_exemplo = {
    "codigo":    "TESTE123",
    "titulo":    "Apartamento de teste",
    "tipo":      "Apartamento",
    "preco":     350000.0,
    "area":      75.5,
    "quartos":   2,
    "banheiros": 2,
    "vagas":     1,
    "endereco":  "Rua Exemplo, 100",
    "cidade":    "São Paulo",
    "estado":    "SP",
    "cep":       "01234-567",
    "descricao": "Este é um imóvel de teste inserido via script.",
    "fotos":     []  # lista vazia por enquanto
}

def main():
    print("🔍 Inserindo (ou atualizando) imóvel de teste no Supabase...")
    try:
        # Usamos upsert para inserir ou atualizar se já existir
        response = (
            supabase
            .table("imoveis")
            .upsert(imovel_exemplo, on_conflict="codigo")
            .execute()
        )
        print("✅ Operação bem-sucedida! Registro:")
        print(response.data)
    except Exception as e:
        print("❌ Erro ao inserir/atualizar imóvel:", e)

    print("✔️ Feito em", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
