import requests

# URL de exemplo (substitua por qualquer uma que você queira testar)
IMAGE_URL = "https://cdn.uso.com.br/23964/2024/10/c5d55c9bc41f60473e9488ef7e1e8330.jpg"
OUTPUT_PATH = "test.jpg"

def download_image(url: str, path: str):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"✅ Imagem baixada e salva em: {path}")

if __name__ == "__main__":
    download_image(IMAGE_URL, OUTPUT_PATH)
