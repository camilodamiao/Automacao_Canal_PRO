"""
Canal PRO ZAP – Login Real (sem Inspector)
Autor: Seu Mentor AI
Descrição: Fecha cookies, preenche e-mail/senha e faz login de verdade
"""

import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from colorama import init, Fore, Style
from playwright.sync_api import sync_playwright, Page

# Inicializar colorama para logs coloridos
init()

# Carregar variáveis de ambiente de config/.env
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
    """Identifica e clica no botão de cookies, se houver."""
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


def test_login():
    """Executa o fluxo completo de login no Canal PRO ZAP."""
    log("🚀 Iniciando teste de login verdadeiro...", 'INFO')

    # 1) Carregar credenciais
    email = os.getenv('ZAP_EMAIL')
    password = os.getenv('ZAP_PASSWORD')
    if not email or not password:
        log("❌ Defina ZAP_EMAIL e ZAP_PASSWORD em config/.env", 'ERROR')
        return

    # 2) Preparar pasta de screenshots
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
            # 4) Navegar e fechar cookies
            log("📍 Indo para https://canalpro.grupozap.com …", 'INFO')
            page.goto('https://canalpro.grupozap.com', wait_until='networkidle')
            handle_cookie_popup(page, screenshots)

            # 5) Preencher e-mail
            log("📧 Preenchendo e-mail…", 'INFO')
            email_box = page.get_by_role("textbox", name="Digite seu e-mail")
            email_box.wait_for(state="visible", timeout=10000)
            email_box.fill(email)
            page.screenshot(path=str(screenshots / "03_email_preenchido.png"))
            log("✅ E-mail preenchido", 'SUCCESS')

            # 6) Preencher senha
            log("🔑 Preenchendo senha…", 'INFO')
            pass_box = page.get_by_role("textbox", name="Digite sua senha")
            pass_box.wait_for(state="visible", timeout=10000)
            pass_box.fill(password)
            page.screenshot(path=str(screenshots / "04_senha_preenchida.png"))
            log("✅ Senha preenchida", 'SUCCESS')

            # 7) Clicar em Entrar
            log("🖱️ Clicando em Entrar…", 'INFO')
            login_btn = page.get_by_role("button", name="Entrar")
            login_btn.wait_for(state="visible", timeout=5000)
            login_btn.click()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(screenshots / "05_apos_login.png"))
            log("✅ Botão Entrar clicado", 'SUCCESS')

            
            # 8) Verificar sucesso de login
            final_url = page.url
            log(f"📍 URL final: {final_url}", 'INFO')
            # Se redirecionou para /ZAP_OLX/, considere login OK
            if '/ZAP_OLX/' in final_url:
                log("🎉 Login efetuado com sucesso!", 'SUCCESS')
            else:
                log("⚠️ O login não foi efetuado corretamente. Verifique seletores e credenciais.", 'WARNING')

            # 9) Pausa final para conferência
            input("🔴 Pressione ENTER para fechar o browser…")

        finally:
            browser.close()
            log("👋 Browser fechado", 'INFO')


if __name__ == "__main__":
    print("=" * 50)
    print("TESTE DE LOGIN REAL - CANAL PRO ZAP")
    print("=" * 50)
    test_login()
