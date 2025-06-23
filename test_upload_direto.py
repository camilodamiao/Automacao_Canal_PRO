#!/usr/bin/env python3
"""
TESTE DE UPLOAD DIRETO - Usa input[type="file"] diretamente
Faz upload do arquivo tests/test.jpg sem abrir modal
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
    print("🧪 TESTE DE UPLOAD DIRETO (SEM MODAL)")
    print("="*60)
    
    # Verificar se o arquivo de teste existe
    arquivo_teste = Path("tests/test.jpg")
    if not arquivo_teste.exists():
        print(f"❌ Arquivo de teste não encontrado: {arquivo_teste}")
        print("💡 Certifique-se de que existe um arquivo 'test.jpg' na pasta 'tests'")
        return False
    
    caminho_absoluto = arquivo_teste.absolute()
    print(f"📄 Arquivo de teste: {caminho_absoluto}")
    print(f"📊 Tamanho: {arquivo_teste.stat().st_size:,} bytes")
    
    email = os.getenv('ZAP_EMAIL')
    password = os.getenv('ZAP_PASSWORD')
    
    if not email or not password:
        print("❌ Configure ZAP_EMAIL e ZAP_PASSWORD no .env")
        return False
    
    print(f"\n📧 Email: {email}")
    print("🔑 Senha: ***")
    
    with sync_playwright() as p:
        print("\n🌐 Abrindo browser...")
        browser = p.chromium.launch(
            headless=False,
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
            
            try:
                page.click('button:has-text("Aceitar")', timeout=3000)
                print("✅ Cookies aceitos")
            except:
                print("ℹ️  Sem popup de cookies")
            
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
            page.goto(listings_url, wait_until='networkidle')
            
            print("🔍 Procurando botão 'Criar anúncio'...")
            create_btn = page.get_by_role("button", name="Criar anúncio")
            create_btn.click()
            
            print("⏳ Aguardando formulário...")
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # 3. FAZER UPLOAD DIRETO
            print("\n📸 FASE 3: UPLOAD DIRETO")
            print("-" * 40)
            
            # Rolar até o final para garantir que a seção de fotos esteja visível
            print("📜 Rolando até seção de fotos...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Procurar o input de arquivo usando os seletores do log
            print("🔍 Procurando input de upload...")
            
            # Seletores possíveis baseados no log de erro
            input_selectors = [
                'input[type="file"][name="images"]',
                'input[data-cy="zap-file-input"]',
                'input.zap-file-input__input',
                'input[type="file"][multiple]',
                'input[type="file"]'
            ]
            
            input_encontrado = False
            
            for selector in input_selectors:
                try:
                    input_element = page.locator(selector)
                    count = input_element.count()
                    
                    if count > 0:
                        print(f"✅ Input encontrado com: {selector}")
                        print(f"   Quantidade: {count}")
                        
                        # Fazer upload
                        print(f"\n📤 Fazendo upload de: {arquivo_teste.name}")
                        input_element.first.set_input_files(str(caminho_absoluto))
                        
                        print("⏳ Aguardando processamento...")
                        time.sleep(5)
                        
                        # Verificar se o upload funcionou
                        print("\n🔍 Verificando se upload funcionou...")
                        
                        # Procurar por evidências de sucesso
                        evidencias = [
                            'img[src*="blob"]',          # Preview em blob
                            'img[src*="test.jpg"]',      # Nome do arquivo
                            '.uploaded-image',           # Classe de imagem enviada
                            '.image-preview',            # Preview de imagem
                            'div[class*="preview"]',     # Div de preview
                            'div[class*="uploaded"]',    # Div de upload
                            '.gallery-item',             # Item da galeria
                            'button:has-text("Remover")', # Botão de remover (indica sucesso)
                            'button:has-text("Excluir")'  # Botão de excluir
                        ]
                        
                        upload_confirmado = False
                        for evidencia in evidencias:
                            if page.locator(evidencia).count() > 0:
                                print(f"✅ Upload confirmado! Encontrado: {evidencia}")
                                upload_confirmado = True
                                break
                        
                        if not upload_confirmado:
                            print("⚠️  Nenhuma evidência visual de upload encontrada")
                            print("   Mas o arquivo pode ter sido enviado mesmo assim")
                        
                        # Verificar se há mensagens de erro
                        error_selectors = [
                            '.error-message',
                            'div[class*="error"]',
                            'span[class*="error"]',
                            '.alert-danger'
                        ]
                        
                        for error_sel in error_selectors:
                            error_elements = page.locator(error_sel).all()
                            for error in error_elements:
                                if error.is_visible():
                                    print(f"❌ Possível erro encontrado: {error.inner_text()}")
                        
                        input_encontrado = True
                        break
                        
                except Exception as e:
                    print(f"❌ Erro com selector '{selector}': {e}")
            
            if not input_encontrado:
                print("\n❌ Nenhum input de arquivo encontrado!")
                print("\n📋 Listando todos os inputs da página:")
                all_inputs = page.locator("input").all()
                for i, inp in enumerate(all_inputs[-10:]):  # Últimos 10
                    try:
                        tipo = inp.get_attribute("type") or "text"
                        nome = inp.get_attribute("name") or "sem-nome"
                        print(f"   - type='{tipo}' name='{nome}'")
                    except:
                        pass
            else:
                print("\n✅ TESTE DE UPLOAD CONCLUÍDO!")
                print("🔍 Verifique visualmente se a imagem apareceu no formulário")
            
            # Manter browser aberto
            print("\n⏰ Browser permanecerá aberto por 30 segundos...")
            print("🔍 Verifique o estado da página")
            print("💡 Procure por:")
            print("   - Preview da imagem enviada")
            print("   - Contador de fotos")
            print("   - Mensagens de erro ou sucesso")
            time.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
            print("⏰ Browser aberto por 20 segundos para debug...")
            time.sleep(20)
        finally:
            browser.close()
            print("\n👋 Browser fechado")

if __name__ == "__main__":
    main()