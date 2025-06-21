"""
Teste inicial - Apenas login no Canal PRO ZAP
Este script testa se conseguimos fazer login com sucesso
"""

import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Inicializar colorama
init()

# Carregar variáveis de ambiente
load_dotenv('config/.env')

def log(message, level='INFO'):
    """Log colorido simples"""
    colors = {
        'INFO': Fore.CYAN,
        'SUCCESS': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED
    }
    color = colors.get(level, Fore.WHITE)
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")

def test_login():
    """Testa apenas o login no Canal PRO"""
    log("🚀 Iniciando teste de login...", 'INFO')
    
    # Verificar credenciais
    email = os.getenv('ZAP_EMAIL')
    password = os.getenv('ZAP_PASSWORD')
    
    if not email or not password:
        log("❌ Configure o arquivo config/.env com suas credenciais!", 'ERROR')
        return
    
    log(f"📧 Email configurado: {email}", 'INFO')
    
    # Criar pasta para screenshots
    screenshot_dir = Path("screenshots") / datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log(f"📸 Screenshots serão salvas em: {screenshot_dir}", 'INFO')
    
    with sync_playwright() as p:
        # Iniciar browser (visível)
        log("🌐 Abrindo navegador...", 'INFO')
        browser = p.chromium.launch(
            headless=False,  # Ver o browser
            slow_mo=500      # Ações lentas para acompanhar
        )
        
        page = browser.new_page()
        
        try:
            # 1. Ir para página de login
            log("📍 Navegando para página de login...", 'INFO')
            page.goto('https://canalpro.grupozap.com/')
            
            # Screenshot da página de login
            page.screenshot(path=str(screenshot_dir / "01_pagina_login.png"))
            log("📸 Screenshot: página de login", 'INFO')
            
            # Aguardar página carregar
            time.sleep(2)
            
            # 2. Procurar e preencher email
            log("🔍 Procurando campo de email...", 'INFO')
            
            # Tentar diferentes seletores possíveis
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id="email"]',
                '#email',
                'input[placeholder*="email" i]',
                'input[placeholder*="e-mail" i]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        log(f"✅ Campo de email encontrado: {selector}", 'SUCCESS')
                        page.fill(selector, email)
                        email_filled = True
                        break
                except:
                    continue
            
            if not email_filled:
                log("❌ Campo de email não encontrado!", 'ERROR')
                page.screenshot(path=str(screenshot_dir / "erro_campo_email.png"))
                return
            
            # Screenshot após preencher email
            page.screenshot(path=str(screenshot_dir / "02_email_preenchido.png"))
            
            # 3. Procurar e preencher senha
            log("🔍 Procurando campo de senha...", 'INFO')
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                '#password',
                'input[placeholder*="senha" i]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        log(f"✅ Campo de senha encontrado: {selector}", 'SUCCESS')
                        page.fill(selector, password)
                        password_filled = True
                        break
                except:
                    continue
            
            if not password_filled:
                log("❌ Campo de senha não encontrado!", 'ERROR')
                page.screenshot(path=str(screenshot_dir / "erro_campo_senha.png"))
                return
            
            # Screenshot após preencher senha
            page.screenshot(path=str(screenshot_dir / "03_senha_preenchida.png"))
            
            # 4. Procurar botão de login
            log("🔍 Procurando botão de login...", 'INFO')
            
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Entrar")',
                'button:has-text("Login")',
                'button:has-text("Acessar")',
                'input[type="submit"]',
                '*[class*="btn"]:has-text("Entrar")'
            ]
            
            button_found = False
            for selector in button_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        log(f"✅ Botão de login encontrado: {selector}", 'SUCCESS')
                        # Screenshot antes de clicar
                        page.screenshot(path=str(screenshot_dir / "04_antes_clicar.png"))
                        
                        # Clicar no botão
                        page.click(selector)
                        button_found = True
                        break
                except:
                    continue
            
            if not button_found:
                log("❌ Botão de login não encontrado!", 'ERROR')
                page.screenshot(path=str(screenshot_dir / "erro_botao_login.png"))
                return
            
            # 5. Aguardar login processar
            log("⏳ Aguardando login...", 'INFO')
            time.sleep(5)
            
            # Screenshot após login
            page.screenshot(path=str(screenshot_dir / "05_apos_login.png"))
            
            # 6. Verificar se logou
            current_url = page.url
            log(f"📍 URL atual: {current_url}", 'INFO')
            
            if 'login' not in current_url.lower():
                log("✅ Login realizado com sucesso!", 'SUCCESS')
                log("🎉 Você está dentro do sistema!", 'SUCCESS')
                
                # Screenshot final
                page.screenshot(path=str(screenshot_dir / "06_sucesso_final.png"), full_page=True)
            else:
                log("⚠️ Ainda na página de login. Verifique as credenciais.", 'WARNING')
                
                # Procurar mensagens de erro
                error_selectors = [
                    '.error', '.alert', '.message',
                    '*[class*="error"]', '*[class*="alert"]'
                ]
                
                for selector in error_selectors:
                    try:
                        errors = page.locator(selector).all_text_contents()
                        if errors:
                            log(f"Mensagem de erro encontrada: {errors}", 'WARNING')
                    except:
                        pass
            
            # Pausar para você ver o resultado
            input("\n🔴 Pressione ENTER para fechar o navegador...")
            
        except Exception as e:
            log(f"❌ Erro durante o teste: {str(e)}", 'ERROR')
            page.screenshot(path=str(screenshot_dir / "erro_geral.png"))
        finally:
            browser.close()
            log("👋 Navegador fechado", 'INFO')
            log(f"\n📁 Screenshots salvas em: {screenshot_dir}", 'INFO')

if __name__ == "__main__":
    print("=" * 50)
    print("TESTE DE LOGIN - CANAL PRO ZAP")
    print("=" * 50)
    test_login()