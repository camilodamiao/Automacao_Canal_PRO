"""
Canal PRO ZAP – Pausa para Mapear Seletores via Inspector
Autor: Seu Mentor AI
Descrição: Faz login, navega até “Criar anúncio” e pausa para você mapear seletores no Inspector
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


def log(message: str, level: str = "INFO"):
    colors = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.MAGENTA,
    }
    color = colors.get(level, Fore.WHITE)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")


def handle_cookie_popup(page: Page):
    """Fecha o banner de cookies, se existir."""
    log("🍪 Verificando banner de cookies…", "INFO")
    selectors = [
        'button:has-text("Aceitar")',
        'button:has-text("Aceitar todos")',
        'button:has-text("Aceitar cookies")',
        'button:has-text("Concordar")',
    ]
    time.sleep(2)
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() and loc.first.is_visible():
            log(f"✅ Fechando cookies com: {sel}", "SUCCESS")
            loc.first.click()
            page.wait_for_timeout(500)
            return
    log("ℹ️ Nenhum popup de cookies detectado.", "INFO")


def main():
    log("🚀 Iniciando fluxo até Criar Anúncio…", "INFO")

    email = os.getenv("ZAP_EMAIL")
    password = os.getenv("ZAP_PASSWORD")
    if not email or not password:
        log("❌ ZAP_EMAIL ou ZAP_PASSWORD ausentes em config/.env", "ERROR")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            slow_mo=200,
            devtools=False  # não abrir o Inspector aqui
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        page = context.new_page()

        try:
            # 1) Acessar homepage e fechar cookies
            log("📍 Acessando https://canalpro.grupozap.com …", "INFO")
            page.goto("https://canalpro.grupozap.com", wait_until="networkidle")
            handle_cookie_popup(page)

            # 2) Login
            log("📧 Preenchendo e-mail…", "INFO")
            page.get_by_role("textbox", name="Digite seu e-mail").fill(email)
            log("🔑 Preenchendo senha…", "INFO")
            page.get_by_role("textbox", name="Digite sua senha").fill(password)
            log("🖱️ Clicando em Entrar…", "INFO")
            page.get_by_role("button", name="Entrar").click()

            # 3) Aguardar rota /ZAP_OLX/
            log("⏳ Aguardando confirmação de login…", "INFO")
            page.wait_for_url("**/ZAP_OLX/**", timeout=15000)
            log("✅ Login confirmado!", "SUCCESS")

            # 4) Navegar para listagens
            listings_url = "https://canalpro.grupozap.com/ZAP_OLX/0/listings?pageSize=10"
            log(f"📍 Abrindo listagens: {listings_url}", "INFO")
            page.goto(listings_url, wait_until="networkidle")

            # 5) Clicar em Criar anúncio
            log("🔍 Localizando botão 'Criar anúncio'…", "INFO")
            btn = page.get_by_role("button", name="Criar anúncio")
            btn.wait_for(state="visible", timeout=10000)
            btn.click()
            page.wait_for_load_state("networkidle")
            log("✅ Página de criação carregada", "SUCCESS")

            # 6) PAUSA para mapear seletores no Inspector
            log("⏸️ Pausando para Mapear Seletores via Inspector", "INFO")
            log("   - Abra o Playwright Inspector com CTRL+SHIFT+P > 'Debug: Open Playwright Inspector'", "INFO")
            log("   - No Inspector, use o seletor (🔍) para clicar em cada campo do formulário e anotar os seletores", "INFO")
            page.pause()  # aqui você inspeciona e copia os seletores

            input("🔴 Após mapear, pressione ENTER para encerrar…")

        finally:
            browser.close()
            log("👋 Browser fechado", "INFO")


if __name__ == "__main__":
    main()
