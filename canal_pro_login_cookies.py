"""
Canal PRO ZAP – Login e Navegação Segura para Listagens
Autor: Seu Mentor AI
Descrição: Faz login, aguarda confirmação e então vai para as listagens
"""

import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from colorama import init, Fore, Style
from playwright.sync_api import sync_playwright, Page

# Inicializar colorama
init()

# Carregar variáveis de ambiente
load_dotenv('config/.env')


def log(message: str, level: str = 'INFO'):
    """Log colorido com timestamp."""
    colors = {
        'INFO': Fore.CYAN,
        'SUCCESS': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'DEBUG': Fore.MAGENTA
    }
    color = colors.get(level, Fore.WHITE)
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")


def handle_cookie_popup(page: Page, screenshot_dir: Path) -> None:
    """Fecha o banner de cookies, se existir."""
    log("🍪 Procurando popup de cookies...", 'INFO')
    selectors = [
        'button:has-text("Aceitar")',
        'button:has-text("Aceitar todos")',
        'button:has-text("Aceitar cookies")',
        'button:has-text("Concordar")',
    ]
    time.sleep(2)
    page.screenshot(path=str(screenshot_dir / "01_cookie_popup.png"))
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() and loc.first.is_visible():
            log(f"✅ Fechando cookies com: {sel}", 'SUCCESS')
            loc.first.click()
            page.wait_for_timeout(500)
            page.screenshot(path=str(screenshot_dir / "02_cookie_closed.png"))
            return
    log("ℹ️ Nenhum popup de cookies detectado.", 'INFO')


def test_login_and_open_listings():
    """Fluxo: login + confirmação + navegação até as listagens."""
    log("🚀 Iniciando automação de login e listagens...", 'INFO')

    # 1) Carregar credenciais
    email = os.getenv('ZAP_EMAIL')
    password = os.getenv('ZAP_PASSWORD')
    if not email or not password:
        log("❌ Defina ZAP_EMAIL e ZAP_PASSWORD em config/.env", 'ERROR')
        return

    # 2) Pasta de screenshots
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshots = Path("screenshots") / ts
    screenshots.mkdir(parents=True, exist_ok=True)
    log(f"📸 Screenshots em: {screenshots}", 'INFO')

    # 3) Iniciar Playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        page = context.new_page()

        try:
            # 4) Acessa homepage e fecha cookies
            log("📍 Acessando Canal PRO ZAP...", 'INFO')
            page.goto('https://canalpro.grupozap.com', wait_until='networkidle')
            handle_cookie_popup(page, screenshots)

            # 5) Preenche e-mail
            log("📧 Preenchendo e-mail…", 'INFO')
            page.get_by_role("textbox", name="Digite seu e-mail").fill(email)
            page.screenshot(path=str(screenshots / "03_email.png"))
            log("✅ E-mail preenchido", 'SUCCESS')

            # 6) Preenche senha
            log("🔑 Preenchendo senha…", 'INFO')
            page.get_by_role("textbox", name="Digite sua senha").fill(password)
            page.screenshot(path=str(screenshots / "04_senha.png"))
            log("✅ Senha preenchida", 'SUCCESS')

            # 7) Clica em Entrar
            log("🖱️ Clicando em Entrar…", 'INFO')
            page.get_by_role("button", name="Entrar").click()

            # --- NOVO BLOCO: aguardar confirmação de login ---
            log("⏳ Aguardando confirmação de login na rota /ZAP_OLX/ …", 'INFO')
            try:
                page.wait_for_url("**/ZAP_OLX/**", timeout=15000)
                page.screenshot(path=str(screenshots / "05_login_confirmado.png"))
                log("🎉 Login confirmado com sucesso!", 'SUCCESS')
            except:
                page.screenshot(path=str(screenshots / "05_login_falhou.png"))
                log("❌ Login não confirmado – abortando navegação.", 'ERROR')
                return

            # 8) Navega para página de listagens
            listings_url = (
                "https://canalpro.grupozap.com/ZAP_OLX/0/"
                "listings?pageSize=10"
            )
            log(f"📍 Indo para listagens: {listings_url}", 'INFO')
            page.goto(listings_url, wait_until='networkidle')
            page.screenshot(path=str(screenshots / "06_listings.png"))

            # 9) Encontrar botão "Criar anúncio"
            log("🔍 Procurando botão 'Criar anúncio'…", 'INFO')
            create_btn = page.get_by_role("button", name="Criar anúncio")
            create_btn.wait_for(state="visible", timeout=10000)
            create_btn.screenshot(path=str(screenshots / "07_btn_create.png"))
            log("✅ Botão 'Criar anúncio' encontrado!", 'SUCCESS')

            input("🔴 Pressione ENTER para fechar…")

        finally:
            browser.close()
            log("👋 Browser fechado", 'INFO')


if __name__ == "__main__":
    print("=" * 50)
    print("AUTOMAÇÃO: LOGIN + ABRIR LISTAGENS + CRIAR ANÚNCIO")
    print("=" * 50)
    test_login_and_open_listings()
