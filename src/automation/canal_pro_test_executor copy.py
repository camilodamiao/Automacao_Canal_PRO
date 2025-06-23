#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script executor ROBUSTO para teste do Canal PRO
Independente de resolução de tela e com upload de fotos corrigido
"""

import sys
import json
import os
import time
import requests
import tempfile
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERRO: Playwright não instalado. Execute: pip install playwright")
    sys.exit(1)

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv('config/.env')
except ImportError:
    print("AVISO: python-dotenv não encontrado. Configure as variáveis manualmente.")

def log(message: str, level: str = "INFO"):
    """Log colorido com timestamp"""
    from colorama import init, Fore, Style
    init()
    
    colors = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.MAGENTA,
    }
    color = colors.get(level, Fore.WHITE)
    timestamp = time.strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")

def handle_cookie_popup(page):
    """Fecha o banner de cookies de forma robusta"""
    log("🍪 Verificando banner de cookies...", "INFO")
    
    selectors = [
        'button:has-text("Aceitar")',
        'button:has-text("Aceitar todos")',
        'button:has-text("Aceitar cookies")',
        'button:has-text("Concordar")',
        '[class*="cookie"] button',
        '[id*="cookie"] button',
        'button[class*="accept"]'
    ]
    
    # Aguardar um pouco para o popup aparecer
    page.wait_for_timeout(2000)
    
    for sel in selectors:
        try:
            elements = page.locator(sel).all()
            for element in elements:
                if element.is_visible():
                    log(f"✅ Fechando cookies com: {sel}", "SUCCESS")
                    element.click()
                    page.wait_for_timeout(500)
                    return True
        except:
            continue
    
    log("ℹ️ Nenhum popup de cookies detectado.", "INFO")
    return False

def fazer_login_robusto(page, email, password):
    """Faz login de forma mais robusta"""
    log("🔐 Fazendo login...", "INFO")
    
    try:
        # Método 1: Por role (mais robusto)
        try:
            log("📧 Tentando preencher email por role...", "DEBUG")
            email_input = page.get_by_role("textbox", name="Digite seu e-mail")
            email_input.fill(email)
            log("✅ Email preenchido", "SUCCESS")
        except:
            # Método 2: Por seletores alternativos
            log("📧 Tentando preencher email por seletor alternativo...", "DEBUG")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="e-mail" i]',
                'input[id="email"]'
            ]
            preenchido = False
            for selector in email_selectors:
                try:
                    page.fill(selector, email)
                    preenchido = True
                    log(f"✅ Email preenchido com: {selector}", "SUCCESS")
                    break
                except:
                    continue
            if not preenchido:
                raise Exception("Não foi possível preencher o email")
        
        # Senha
        try:
            log("🔑 Tentando preencher senha por role...", "DEBUG")
            password_input = page.get_by_role("textbox", name="Digite sua senha")
            password_input.fill(password)
            log("✅ Senha preenchida", "SUCCESS")
        except:
            log("🔑 Tentando preencher senha por seletor alternativo...", "DEBUG")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="senha" i]',
                'input[id="password"]'
            ]
            preenchido = False
            for selector in password_selectors:
                try:
                    page.fill(selector, password)
                    preenchido = True
                    log(f"✅ Senha preenchida com: {selector}", "SUCCESS")
                    break
                except:
                    continue
            if not preenchido:
                raise Exception("Não foi possível preencher a senha")
        
        # Botão de login
        try:
            log("🖱️ Clicando em Entrar por role...", "DEBUG")
            login_btn = page.get_by_role("button", name="Entrar")
            login_btn.click()
            log("✅ Botão clicado", "SUCCESS")
        except:
            log("🖱️ Tentando clicar por seletor alternativo...", "DEBUG")
            button_selectors = [
                'button:has-text("Entrar")',
                'button[type="submit"]',
                'button:has-text("Login")',
                'input[type="submit"]'
            ]
            clicado = False
            for selector in button_selectors:
                try:
                    page.click(selector)
                    clicado = True
                    log(f"✅ Botão clicado com: {selector}", "SUCCESS")
                    break
                except:
                    continue
            if not clicado:
                raise Exception("Não foi possível clicar no botão de login")
        
        return True
        
    except Exception as e:
        log(f"❌ Erro no login: {e}", "ERROR")
        return False

def navegar_para_criar_anuncio(page):
    """Navega até a página de criar anúncio de forma robusta"""
    try:
        # Ir para listagens
        listings_url = "https://canalpro.grupozap.com/ZAP_OLX/0/listings?pageSize=10"
        log(f"📍 Navegando para listagens...", "INFO")
        page.goto(listings_url, wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        # Procurar botão "Criar anúncio"
        log("🔍 Procurando botão 'Criar anúncio'...", "INFO")
        
        # Tentar diferentes métodos
        botao_selectors = [
            'button:has-text("Criar anúncio")',
            'button span:has-text("Criar anúncio")',
            'button.new-l-button:has-text("Criar")',
            'button[class*="primary"]:has-text("Criar")',
            'button:has(span:has-text("Criar anúncio"))'
        ]
        
        for selector in botao_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    log(f"✅ Botão 'Criar anúncio' clicado com: {selector}", "SUCCESS")
                    page.wait_for_load_state("networkidle")
                    return True
            except:
                continue
        
        # Se não encontrou, tentar por role
        try:
            btn = page.get_by_role("button", name="Criar anúncio")
            btn.click()
            log("✅ Botão 'Criar anúncio' clicado por role", "SUCCESS")
            page.wait_for_load_state("networkidle")
            return True
        except:
            pass
        
        log("❌ Não foi possível encontrar o botão 'Criar anúncio'", "ERROR")
        return False
        
    except Exception as e:
        log(f"❌ Erro ao navegar: {e}", "ERROR")
        return False

def fazer_upload_fotos_robusto(page, fotos_urls):
    """Upload de fotos robusto com download do Supabase"""
    if not fotos_urls or len(fotos_urls) == 0:
        log("📸 Nenhuma foto para upload", "WARNING")
        return True
    
    log(f"📸 Iniciando upload de {len(fotos_urls)} fotos", "INFO")
    
    fotos_temp = []
    
    try:
        # 1. BAIXAR FOTOS DO SUPABASE
        log("📥 Baixando fotos do Supabase...", "INFO")
        
        for i, url in enumerate(fotos_urls[:8], 1):  # Máximo 8 fotos
            try:
                log(f"   📥 Baixando foto {i}/{min(len(fotos_urls), 8)}...", "DEBUG")
                
                # Download da foto
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                if len(response.content) < 1000:
                    log(f"   ⚠️ Foto {i} muito pequena, pulando...", "WARNING")
                    continue
                
                # Salvar temporariamente
                with tempfile.NamedTemporaryFile(suffix=f'_foto_{i}.jpg', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                    fotos_temp.append(temp_path)
                
                log(f"   ✅ Foto {i} baixada: {len(response.content):,} bytes", "SUCCESS")
                
            except Exception as e:
                log(f"   ❌ Erro ao baixar foto {i}: {str(e)[:50]}", "ERROR")
                continue
        
        if not fotos_temp:
            log("❌ Nenhuma foto foi baixada com sucesso", "ERROR")
            return False
        
        log(f"✅ {len(fotos_temp)} fotos prontas para upload", "SUCCESS")
        
        # 2. NAVEGAR ATÉ SEÇÃO DE FOTOS
        log("📜 Procurando seção de fotos...", "INFO")
        
        # Tentar rolar até encontrar o botão
        for scroll in range(5):  # Tentar 5 vezes
            page.evaluate(f"window.scrollBy(0, window.innerHeight * 0.5)")
            page.wait_for_timeout(500)
            
            # Verificar se o botão está visível
            botao_fotos = page.locator('button:has-text("Adicionar fotos")').first
            if botao_fotos.count() > 0 and botao_fotos.is_visible():
                log("✅ Seção de fotos encontrada", "SUCCESS")
                break
        
        # 3. CLICAR NO BOTÃO "ADICIONAR FOTOS"
        log("🖱️ Clicando no botão 'Adicionar fotos'...", "INFO")
        
        botao_selectors = [
            'button:has-text("Adicionar fotos")',
            'button span:has-text("Adicionar fotos")',
            '.listing-detail-images__display-box-inner__button',
            'button:has(svg):has-text("Adicionar")',
            '#listing-detail-images button'
        ]
        
        botao_clicado = False
        for selector in botao_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    btn.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    btn.click()
                    botao_clicado = True
                    log(f"✅ Botão clicado com: {selector}", "SUCCESS")
                    break
            except:
                continue
        
        if not botao_clicado:
            log("❌ Não foi possível clicar no botão de fotos", "ERROR")
            return False
        
        # 4. AGUARDAR MODAL/INPUT
        log("⏳ Aguardando modal/input de fotos...", "INFO")
        page.wait_for_timeout(2000)
        
        # 5. FAZER UPLOAD
        log("📤 Fazendo upload das fotos...", "INFO")
        
        # Procurar input file
        input_selectors = [
            'input[type="file"][name="images"]',
            'input[type="file"][multiple]',
            'input[type="file"]'
        ]
        
        upload_ok = False
        for selector in input_selectors:
            try:
                inputs = page.locator(selector).all()
                if inputs:
                    # Usar o último input (mais recente)
                    input_element = inputs[-1]
                    input_element.set_input_files(fotos_temp)
                    upload_ok = True
                    log(f"✅ Upload realizado com: {selector}", "SUCCESS")
                    break
            except:
                continue
        
        if not upload_ok:
            # Tentar forçar visibilidade
            log("🔧 Forçando visibilidade do input...", "DEBUG")
            page.evaluate("""
                const inputs = document.querySelectorAll('input[type="file"]');
                inputs.forEach(input => {
                    input.style.display = 'block';
                    input.style.opacity = '1';
                });
            """)
            page.wait_for_timeout(500)
            
            # Tentar novamente
            try:
                input_final = page.locator('input[type="file"]').last
                input_final.set_input_files(fotos_temp)
                upload_ok = True
                log("✅ Upload realizado após forçar visibilidade", "SUCCESS")
            except:
                pass
        
        if upload_ok:
            log("⏳ Aguardando processamento das fotos...", "INFO")
            page.wait_for_timeout(5000)
            log("✅ Upload de fotos concluído!", "SUCCESS")
        else:
            log("❌ Não foi possível fazer upload das fotos", "ERROR")
        
        return upload_ok
        
    except Exception as e:
        log(f"❌ Erro no upload de fotos: {e}", "ERROR")
        return False
    finally:
        # Limpar arquivos temporários
        for foto in fotos_temp:
            try:
                os.unlink(foto)
            except:
                pass

def mapear_tipo_imovel(tipo):
    """Mapeia tipos do scraping para o Canal PRO"""
    mapeamento = {
        'Apartamento': 'APARTMENT',
        'Casa': 'HOME',
        'Terreno': 'ALLOTMENT_LAND',
        'Comercial': 'BUILDING'
    }
    return mapeamento.get(tipo, 'APARTMENT')

def mapear_iptu_periodo(periodo):
    """Mapeia período IPTU para o Canal PRO"""
    if not periodo:
        return 'YEARLY'
    if 'Mensal' in str(periodo):
        return 'MONTHLY'
    return 'YEARLY'

def preencher_campo_robusto(page, nome_campo, valor, seletores, tipo="input"):
    """Preenche campo tentando múltiplos seletores"""
    if not valor:
        return True
    
    log(f"📝 Preenchendo {nome_campo}: {valor}", "DEBUG")
    
    for selector in seletores:
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                element.wait_for(state="visible", timeout=5000)
                
                if tipo == "select":
                    element.select_option(str(valor))
                elif tipo == "click":
                    element.click()
                else:
                    element.clear()
                    element.fill(str(valor))
                
                log(f"   ✅ {nome_campo} preenchido", "SUCCESS")
                return True
        except:
            continue
    
    log(f"   ⚠️ Não foi possível preencher {nome_campo}", "WARNING")
    return False

def executar_teste(dados_completos):
    """Execução principal robusta"""
    log("=" * 60, "INFO")
    log("🚀 TESTE CANAL PRO - VERSÃO ROBUSTA", "INFO")
    log("=" * 60, "INFO")
    
    with sync_playwright() as p:
        log("🌐 Abrindo browser...", "INFO")
        
        # Browser com configurações robustas
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,
            args=['--start-maximized']
        )
        
        # Context sem viewport fixo (usa o tamanho da janela)
        context = browser.new_context(
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        page = context.new_page()
        
        try:
            # FASE 1: LOGIN
            log("\n🔐 FASE 1: LOGIN", "INFO")
            log("-" * 40, "INFO")
            
            page.goto('https://canalpro.grupozap.com', wait_until='networkidle')
            handle_cookie_popup(page)
            
            email = os.getenv('ZAP_EMAIL', '')
            password = os.getenv('ZAP_PASSWORD', '')
            
            if not email or not password:
                log("❌ Configure ZAP_EMAIL e ZAP_PASSWORD no .env", "ERROR")
                return False
            
            if not fazer_login_robusto(page, email, password):
                log("❌ Falha no login", "ERROR")
                return False
            
            log("⏳ Aguardando confirmação de login...", "INFO")
            page.wait_for_url("**/ZAP_OLX/**", timeout=15000)
            log("✅ Login confirmado!", "SUCCESS")
            
            # FASE 2: NAVEGAÇÃO
            log("\n📍 FASE 2: NAVEGAÇÃO", "INFO")
            log("-" * 40, "INFO")
            
            if not navegar_para_criar_anuncio(page):
                log("❌ Falha ao navegar para criar anúncio", "ERROR")
                return False
            
            page.wait_for_timeout(3000)
            
            # FASE 3: PREENCHIMENTO
            log("\n📝 FASE 3: PREENCHIMENTO DO FORMULÁRIO", "INFO")
            log("-" * 40, "INFO")
            
            # Tipo residencial
            preencher_campo_robusto(page, "Tipo Residencial", "RESIDENTIAL", 
                ['label[for="zap-switch-radio-755_RESIDENTIAL"]',
                 'input[value="RESIDENTIAL"]',
                 '#zap-switch-radio-755_RESIDENTIAL'], "click")
            
            # Tipo do imóvel
            tipo_mapeado = mapear_tipo_imovel(dados_completos.get('tipo', 'Apartamento'))
            preencher_campo_robusto(page, "Tipo do Imóvel", tipo_mapeado,
                ['select[name="unitType"]', '#unitType'], "select")
            
            # Categoria
            preencher_campo_robusto(page, "Categoria", "CategoryNONE",
                ['select[name="category"]', '#category'], "select")
            
            # Quartos
            if dados_completos.get('quartos'):
                preencher_campo_robusto(page, "Quartos", dados_completos['quartos'],
                    ['select[name="bedrooms"]', '#bedrooms'], "select")
            
            # Suítes
            if dados_completos.get('suites'):
                preencher_campo_robusto(page, "Suítes", dados_completos['suites'],
                    ['select[name="suites"]', '#suites'], "select")
            
            # Banheiros
            if dados_completos.get('banheiros'):
                preencher_campo_robusto(page, "Banheiros", dados_completos['banheiros'],
                    ['select[name="bathrooms"]', '#bathrooms'], "select")
            
            # Vagas
            if dados_completos.get('vagas'):
                preencher_campo_robusto(page, "Vagas", dados_completos['vagas'],
                    ['select[name="parkingSpaces"]', '#parkingSpaces'], "select")
            
            # Área
            if dados_completos.get('area'):
                preencher_campo_robusto(page, "Área Útil", dados_completos['area'],
                    ['input[name="usableAreas"]', '#usableAreas'])
            
            # Andar
            if dados_completos.get('tipo') == 'Apartamento':
                preencher_campo_robusto(page, "Andar", "0",
                    ['select[name="unitFloor"]', '#unitFloor'], "select")
            
            # CEP
            if dados_completos.get('cep'):
                preencher_campo_robusto(page, "CEP", dados_completos['cep'],
                    ['input[name="zipCode"]', '#zipCode'])
                log("⏳ Aguardando preenchimento automático do endereço...", "INFO")
                page.wait_for_timeout(3000)
            
            # Endereço
            if dados_completos.get('endereco'):
                preencher_campo_robusto(page, "Endereço", dados_completos['endereco'],
                    ['input[name="street"]', '#street'])
            
            # Número
            if dados_completos.get('numero'):
                preencher_campo_robusto(page, "Número", dados_completos['numero'],
                    ['input[data-label="número"]', 'input[name="streetNumber"]', '#streetNumber'])
            
            # Complemento
            if dados_completos.get('complemento'):
                preencher_campo_robusto(page, "Complemento", dados_completos['complemento'],
                    ['input[name="complement"]', '#complement'])
            
            # Modo de exibição do endereço
            preencher_campo_robusto(page, "Endereço Completo", "ALL",
                ['label[for="zap-switch-radio-688_ALL"]',
                 'input[value="ALL"]',
                 '#zap-switch-radio-688_ALL'], "click")
            
            # Tipo de operação
            preencher_campo_robusto(page, "Operação Venda", "SALE",
                ['label[for="zap-switch-radio-4070_SALE"]',
                 'input[value="SALE"]',
                 '#zap-switch-radio-4070_SALE'], "click")
            
            # Preço
            if dados_completos.get('preco'):
                preco_str = str(int(dados_completos['preco']))
                preencher_campo_robusto(page, "Preço de Venda", preco_str,
                    ['input[name="priceSale"]', '#priceSale'])
            
            # Condomínio
            if dados_completos.get('condominio'):
                cond_str = str(int(dados_completos['condominio']))
                preencher_campo_robusto(page, "Condomínio", cond_str,
                    ['input[name="monthlyCondoFeeMask"]', '#monthlyCondoFeeMask'])
            
            # IPTU
            if dados_completos.get('iptu'):
                iptu_str = str(int(dados_completos['iptu']))
                preencher_campo_robusto(page, "IPTU", iptu_str,
                    ['input[name="yearlyIptuMask"]', '#yearlyIptuMask'])
                
                periodo_mapeado = mapear_iptu_periodo(dados_completos.get('iptu_periodo'))
                preencher_campo_robusto(page, "Período IPTU", periodo_mapeado,
                    ['select[name="period"]', '#period'], "select")
            
            # Código do anúncio
            if dados_completos.get('codigo_anuncio_canalpro'):
                preencher_campo_robusto(page, "Código do Anúncio", dados_completos['codigo_anuncio_canalpro'],
                    ['input[name="externalId"]', '#externalId'])
            
            # Título
            if dados_completos.get('titulo'):
                titulo_truncado = dados_completos['titulo'][:100]
                preencher_campo_robusto(page, "Título", titulo_truncado,
                    ['input[name="title"]', '#title'])
            
            # Descrição
            if dados_completos.get('descricao'):
                desc_truncada = dados_completos['descricao'][:3000]
                preencher_campo_robusto(page, "Descrição", desc_truncada,
                    ['textarea[name="description"]', '#description'])
            
            # Links
            if dados_completos.get('link_video_youtube'):
                preencher_campo_robusto(page, "Vídeo YouTube", dados_completos['link_video_youtube'],
                    ['input[name="videos"]', '#videos'])
            
            if dados_completos.get('link_tour_virtual'):
                preencher_campo_robusto(page, "Tour Virtual", dados_completos['link_tour_virtual'],
                    ['input[name="videoTourLink"]', '#videoTourLink'])
            
            # FASE 4: UPLOAD DE FOTOS
            log("\n📸 FASE 4: UPLOAD DE FOTOS", "INFO")
            log("-" * 40, "INFO")
            
            if dados_completos.get('fotos'):
                fazer_upload_fotos_robusto(page, dados_completos['fotos'])
            else:
                log("📸 Nenhuma foto para upload", "WARNING")
            
            # FASE 5: FINALIZAÇÃO
            log("\n🎉 FASE 5: TESTE CONCLUÍDO", "INFO")
            log("-" * 40, "INFO")
            
            # Screenshot final
            screenshot_path = f"teste_completo_{int(time.time())}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            log(f"📸 Screenshot final: {screenshot_path}", "INFO")
            
            log("\n✅ FORMULÁRIO PREENCHIDO COM SUCESSO!", "SUCCESS")
            log("\n🔍 INSTRUÇÕES:", "INFO")
            log("1. Verifique todos os campos", "INFO")
            log("2. Verifique as fotos carregadas", "INFO")
            log("3. Role até o final para ver o botão 'Criar anúncio'", "INFO")
            log("4. NÃO CLIQUE EM PUBLICAR - Este é apenas um teste!", "WARNING")
            
            log("\n⏰ Browser ficará aberto por 5 minutos...", "INFO")
            page.wait_for_timeout(300000)  # 5 minutos
            
            return True
            
        except Exception as e:
            log(f"\n❌ ERRO DURANTE TESTE: {e}", "ERROR")
            
            # Screenshot de erro
            try:
                error_screenshot = f"erro_teste_{int(time.time())}.png"
                page.screenshot(path=error_screenshot, full_page=True)
                log(f"📸 Screenshot de erro: {error_screenshot}", "INFO")
            except:
                pass
            
            log("🔍 Mantendo browser aberto para debug (1 minuto)...", "INFO")
            page.wait_for_timeout(60000)
            return False
        finally:
            browser.close()
            log("\n🚪 Browser fechado", "INFO")

def main():
    if len(sys.argv) != 2:
        print("Uso: python canal_pro_test_executor.py <arquivo_dados.json>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            dados_completos = json.load(f)
        
        log(f"📄 Dados carregados: {len(dados_completos)} campos", "INFO")
        
        if dados_completos.get('fotos'):
            log(f"📸 {len(dados_completos['fotos'])} fotos encontradas", "INFO")
        
        sucesso = executar_teste(dados_completos)
        
        if sucesso:
            log("\n🎉 SCRIPT FINALIZADO COM SUCESSO!", "SUCCESS")
            sys.exit(0)
        else:
            log("\n💥 SCRIPT FINALIZADO COM ERROS", "ERROR")
            sys.exit(1)
            
    except Exception as e:
        log(f"❌ ERRO: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()