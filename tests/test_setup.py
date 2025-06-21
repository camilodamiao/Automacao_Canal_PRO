import sys
from pathlib import Path

print("=" * 50)
print("🔍 TESTE DE CONFIGURAÇÃO DO AMBIENTE")
print("=" * 50)

# Informações do Python
print(f"\n✅ Python versão: {sys.version}")
print(f"📁 Pasta atual: {Path.cwd()}")

# Testa bibliotecas
bibliotecas = {
    'playwright': '🎭 Playwright (automação)',
    'dotenv': '🔐 Python-dotenv (configurações)',
    'requests': '🌐 Requests (requisições HTTP)',
    'bs4': '🍜 BeautifulSoup (parser HTML)',
    'colorama': '🎨 Colorama (cores terminal)',
    'PIL': '🖼️ Pillow (manipulação imagens)'
}

print("\n📚 Verificando bibliotecas:")
for lib, desc in bibliotecas.items():
    try:
        __import__(lib)
        print(f"  ✅ {desc}")
    except ImportError:
        print(f"  ❌ {desc} - NÃO INSTALADO")

# Testa o navegador
print("\n🌐 Testando navegador...")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.google.com")
        print("  ✅ Navegador funcionando!")
        input("\n⏸️  Pressione ENTER para fechar o navegador...")
        browser.close()
except Exception as e:
    print(f"  ❌ Erro: {e}")

print("\n✨ Teste concluído!")