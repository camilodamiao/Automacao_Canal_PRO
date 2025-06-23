#!/usr/bin/env python3
"""
TESTE ISOLADO - Apenas testar clique no botão de upload
Usa o seletor exato do código original
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('config/.env')

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright não instalado!")
    sys.exit(1)

def main():
    print("="*60)
    print("🧪 TESTE DE CLIQUE NO BOTÃO DE UPLOAD")
    print("="*60)
    
    email = os.getenv('ZAP_EMAIL')
    password = os.getenv('ZAP_PASSWORD')
    
    if not email or not password:
        print("❌ Configure ZAP_EMAIL e ZAP_PASSWORD no .env")
        return False
    
    print(f"📧 Email: {email}")
    print("🔑 Senha: ***")
    
    with sync_playwright() as p:
        print("\n🌐 Abrindo browser em modo visível...")
        browser = p.chromium.launch(
            headless=False,  # Modo headed como solicitado
            slow_mo=800,
            args=['--start-maximized']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        page = context.new_page()
        
        try:
            # 1. LOGIN
            print("\n🔐 FASE 1: LOGIN")
            print("-" * 40)
            
            page.goto('https://canalpro.grupozap.com', wait_until='networkidle')
            
            # Fechar cookies
            try:
                page.click('button:has-text("Aceitar")', timeout=3000)
                print("✅ Cookies aceitos")
            except:
                print("ℹ️  Sem popup de cookies")
            
            # Preencher login
            print("📝 Preenchendo credenciais...")
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            
            print("⏳ Aguardando login...")
            page.wait_for_url("**/ZAP_OLX/**", timeout=15000)
            print("✅ Login confirmado!")
            
            # 2. NAVEGAR PARA CRIAR ANÚNCIO
            print("\n📍 FASE 2: NAVEGAÇÃO")
            print("-" * 40)
            
            listings_url = "https://canalpro.grupozap.com/ZAP_OLX/0/listings?pageSize=10"
            print(f"📍 Indo para: {listings_url}")
            page.goto(listings_url, wait_until='networkidle')
            
            print("🔍 Procurando botão 'Criar anúncio'...")
            create_btn = page.get_by_role("button", name="Criar anúncio")
            create_btn.wait_for(state="visible", timeout=10000)
            create_btn.click()
            
            print("⏳ Aguardando formulário carregar...")
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # Aguardar formulário carregar completamente
            
            # 3. PROCURAR E CLICAR NO BOTÃO DE FOTOS
            print("\n📸 FASE 3: BOTÃO DE UPLOAD DE FOTOS")
            print("-" * 40)
            
            # Rolar até o final da página
            print("📜 Rolando até o final da página...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Usar os seletores EXATOS do código original
            print("🔍 Procurando botão de adicionar fotos...")
            
            # Primeiro tentar com o seletor principal do código
            seletor_principal = 'button:has-text("Adicionar fotos")'
            
            try:
                botao = page.locator(seletor_principal)
                count = botao.count()
                
                if count > 0:
                    print(f"✅ Botão encontrado: '{seletor_principal}'")
                    print(f"   Quantidade: {count}")
                    
                    # Verificar se está visível
                    if botao.first.is_visible():
                        print("✅ Botão está visível")
                    else:
                        print("⚠️  Botão existe mas não está visível")
                    
                    print("\n🖱️  Clicando no botão...")
                    botao.first.click()
                    
                    print("⏳ Aguardando modal abrir...")
                    time.sleep(3)
                    
                    # Verificar se algo mudou na página
                    print("\n🔍 Verificando se modal abriu...")
                    
                    # Procurar por elementos que indicam que o modal está aberto
                    modal_selectors = [
                        '.modal',
                        'div[role="dialog"]',
                        '.overlay',
                        'input[type="file"]'
                    ]
                    
                    modal_encontrado = False
                    for selector in modal_selectors:
                        if page.locator(selector).count() > 0:
                            print(f"✅ Possível modal encontrado: {selector}")
                            modal_encontrado = True
                            break
                    
                    if not modal_encontrado:
                        print("⚠️  Nenhum modal óbvio detectado")
                        print("   O modal pode ter aberto de forma diferente")
                    
                    print("\n✅ TESTE CONCLUÍDO!")
                    print("🔍 Verifique visualmente se o modal de fotos abriu")
                    
                else:
                    print(f"❌ Botão '{seletor_principal}' não encontrado!")
                    
                    # Tentar seletor alternativo do código original
                    seletor_alternativo = '.zap-gallery-upload__button'
                    print(f"\n🔍 Tentando seletor alternativo: {seletor_alternativo}")
                    
                    botao_alt = page.locator(seletor_alternativo)
                    if botao_alt.count() > 0:
                        print(f"✅ Encontrado com seletor alternativo!")
                        botao_alt.first.click()
                        time.sleep(3)
                    else:
                        print("❌ Seletor alternativo também não encontrou")
                        
                        # Listar botões disponíveis para debug
                        print("\n📋 Listando botões disponíveis na página:")
                        all_buttons = page.locator("button").all()
                        for i, btn in enumerate(all_buttons[-10:]):  # Últimos 10 botões
                            try:
                                texto = btn.inner_text()
                                if texto:
                                    print(f"   - '{texto}'")
                            except:
                                pass
                
            except Exception as e:
                print(f"❌ Erro ao procurar/clicar botão: {e}")
            
            # Manter browser aberto para inspeção
            print("\n⏰ Browser permanecerá aberto por 30 segundos...")
            print("🔍 Verifique o estado da página")
            time.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
            print("⏰ Mantendo browser aberto por 20 segundos para debug...")
            time.sleep(20)
        finally:
            browser.close()
            print("\n👋 Browser fechado")

if __name__ == "__main__":
    main()