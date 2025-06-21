# test_upload_image.py

import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    # 1) carregar .env
    load_dotenv('config/.env')

    SUPA_URL    = os.getenv("SUPABASE_URL")
    SUPA_KEY    = os.getenv("SUPABASE_KEY")
    SUPA_BUCKET = os.getenv("SUPABASE_BUCKET")

    # 2) checar variáveis
    if not SUPA_URL or not SUPA_KEY or not SUPA_BUCKET:
        print("❌ Defina SUPABASE_URL, SUPABASE_KEY e SUPABASE_BUCKET em seu .env")
        return

    # 3) instanciar client
    supabase = create_client(SUPA_URL, SUPA_KEY)

    # 4) caminho local e destino no bucket
    local_path  = "test.jpg"
    remote_path = f"images/{os.path.basename(local_path)}"

    # 5) ler o arquivo
    try:
        with open(local_path, "rb") as img:
            data = img.read()
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {local_path}")
        return

    # 6) fazer upload
    print(f"⏳ Enviando {local_path} para o bucket `{SUPA_BUCKET}` em `{remote_path}`…")
    res = supabase.storage.from_(SUPA_BUCKET).upload(remote_path, data)

    # 7) checar resposta
    if isinstance(res, dict) and res.get("error"):
        print("❌ Falha no upload:", res["error"])
    else:
        print("✅ Upload realizado com sucesso!")
        print("→ URL público (se seu bucket for público):")
        print(f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{remote_path}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    main()
