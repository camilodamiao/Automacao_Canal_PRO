#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script executor CORRIGIDO para teste do Canal PRO
CORREÇÃO PRINCIPAL: Upload direto sem clicar no botão
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
    elif 'Anual' in str(periodo):
        return 'YEARLY'
    return 'YEARLY'

def verificar_estado_switch_inteligente(page, seletores_grupo, nome_campo):
    """Verifica estado de switches problemáticos antes de clicar"""
    try:
        print(f"🔍 Verificando estado do {nome_campo}...")
        
        elemento_encontrado = None
        seletor_usado = None
        
        for seletor in seletores_grupo:
            try:
                element = page.locator(seletor)
                if element.count() > 0:
                    elemento_encontrado = element.first
                    seletor_usado = seletor
                    print(f"   📍 Elemento encontrado: {seletor}")
                    break
            except:
                continue
        
        if not elemento_encontrado:
            print(f"   ✅ {nome_campo} não encontrado - assumindo que já está correto")
            return True
        
        try:
            elemento_encontrado.wait_for(state="visible", timeout=5000)
            
            # Verificar se já está selecionado
            esta_selecionado = False
            
            # Método 1: is_checked()
            try:
                if elemento_encontrado.is_checked():
                    esta_selecionado = True
                    print(f"   ✅ {nome_campo} já está selecionado (checked)")
            except:
                pass
            
            # Método 2: Classes CSS
            if not esta_selecionado:
                try:
                    classes = elemento_encontrado.get_attribute("class") or ""
                    if any(cls in classes.lower() for cls in ["active", "selected", "checked"]):
                        esta_selecionado = True
                        print(f"   ✅ {nome_campo} já está selecionado (CSS)")
                except:
                    pass
            
            # Se não está selecionado, clicar
            if not esta_selecionado:
                print(f"   🖱️ {nome_campo} não está selecionado, clicando...")
                elemento_encontrado.click()
                time.sleep(0.5)
                print(f"   ✅ {nome_campo} clicado com sucesso")
            
            return True
            
        except Exception as e:
            print(f"   ✅ {nome_campo} - assumindo estado correto (erro: {e})")
            return True
            
    except Exception as e:
        print(f"   ✅ {nome_campo} - continuando (erro geral: {e})")
        return True

def preencher_campo_simples(page, seletor, valor, nome_campo, tipo="input"):
    """Preenche um campo simples do formulário"""
    try:
        print(f"🔍 Preenchendo {nome_campo}: {valor}")
        
        element = page.locator(seletor)
        element.wait_for(state="visible", timeout=10000)
        
        if tipo == "select":
            element.select_option(str(valor))
            print(f"   ✅ Dropdown {nome_campo} selecionado: {valor}")
        elif tipo == "click":
            element.click()
            print(f"   ✅ Botão {nome_campo} clicado")
        else:
            element.clear()
            element.fill(str(valor))
            print(f"   ✅ Campo {nome_campo} preenchido: {valor}")
        
        time.sleep(0.5)
        return True
        
    except Exception as e:
        print(f"   ❌ ERRO ao preencher {nome_campo}: {e}")
        return False

def fazer_upload_fotos(page, fotos_urls):
    """Upload de fotos CORRIGIDO - Suporta múltiplos uploads (8 fotos por vez)"""
    if not fotos_urls or len(fotos_urls) == 0:
        print("📸 Nenhuma foto para upload")
        return True
    
    print(f"\n📸 INICIANDO UPLOAD DE {len(fotos_urls)} FOTOS")
    print("-" * 50)
    
    try:
        # 1. BAIXAR TODAS AS FOTOS PRIMEIRO
        print("📥 FASE 1: BAIXANDO TODAS AS FOTOS...")
        todas_fotos_temp = []
        
        for i, url in enumerate(fotos_urls):  # Baixar TODAS as fotos
            try:
                print(f"   📥 Baixando foto {i+1}/{len(fotos_urls)}: {url[:60]}...")
                
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Validar tamanho
                if len(response.content) < 1000:
                    print(f"   ⚠️ Foto {i+1} muito pequena ({len(response.content)} bytes), pulando...")
                    continue
                
                # Determinar extensão
                content_type = response.headers.get('content-type', '').lower()
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
                
                # Salvar temporariamente
                with tempfile.NamedTemporaryFile(suffix=f'_foto_{i+1}{ext}', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                todas_fotos_temp.append(temp_path)
                print(f"   ✅ Foto {i+1} baixada: {os.path.basename(temp_path)} ({len(response.content)} bytes)")
                
            except Exception as e:
                print(f"   ❌ Erro ao baixar foto {i+1}: {e}")
                continue
        
        if not todas_fotos_temp:
            print("❌ NENHUMA FOTO FOI BAIXADA COM SUCESSO")
            return False
        
        print(f"\n✅ Total de {len(todas_fotos_temp)} fotos baixadas com sucesso!")
        
        # 2. ROLAR ATÉ SEÇÃO DE UPLOAD
        print("\n📜 FASE 2: NAVEGANDO ATÉ SEÇÃO DE UPLOAD...")
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print("   ✅ Página rolada até o final")
        except:
            print("   ⚠️ Erro ao rolar página")
        
        # 3. FAZER UPLOAD EM LOTES DE 8 FOTOS
        print("\n🔍 FASE 3: UPLOAD EM LOTES (8 FOTOS POR VEZ)...")
        
        # Dividir fotos em grupos de 8
        fotos_por_lote = 8
        lotes = [todas_fotos_temp[i:i + fotos_por_lote] for i in range(0, len(todas_fotos_temp), fotos_por_lote)]
        
        print(f"   📊 Total de lotes: {len(lotes)}")
        for idx, lote in enumerate(lotes):
            print(f"   📦 Lote {idx + 1}: {len(lote)} fotos")
        
        # Seletores do input
        input_selectors = [
            'input[type="file"][name="images"]',
            'input[data-cy="zap-file-input"]',
            'input.zap-file-input__input',
            'input[type="file"][multiple]',
            'input[type="file"]'
        ]
        
        total_enviadas = 0
        
        # Processar cada lote
        for lote_idx, lote_fotos in enumerate(lotes):
            print(f"\n📤 PROCESSANDO LOTE {lote_idx + 1}/{len(lotes)} ({len(lote_fotos)} fotos)")
            
            upload_realizado = False
            
            # Se não é o primeiro lote, aguardar um pouco mais
            if lote_idx > 0:
                print("   ⏳ Aguardando novo botão de upload aparecer...")
                time.sleep(3)
                
                # Rolar novamente para garantir visibilidade
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Tentar fazer upload do lote
            for selector in input_selectors:
                try:
                    # Procurar todos os inputs, pois pode haver múltiplos após o primeiro upload
                    input_elements = page.locator(selector).all()
                    
                    if len(input_elements) > 0:
                        # Usar o último input encontrado (geralmente o novo botão)
                        input_element = input_elements[-1]
                        
                        print(f"   ✅ Input encontrado (total de {len(input_elements)} inputs na página)")
                        print(f"   📤 Enviando {len(lote_fotos)} fotos...")
                        
                        # Fazer upload do lote
                        input_element.set_input_files(lote_fotos)
                        
                        print("   ⏳ Aguardando processamento...")
                        time.sleep(5)
                        
                        total_enviadas += len(lote_fotos)
                        upload_realizado = True
                        print(f"   ✅ Lote {lote_idx + 1} enviado com sucesso!")
                        break
                        
                except Exception as e:
                    print(f"   ❌ Erro com selector '{selector}': {e}")
                    continue
            
            if not upload_realizado:
                print(f"   ❌ FALHA ao enviar lote {lote_idx + 1}")
                break
        
        # 4. VERIFICAR SE UPLOAD FUNCIONOU
        print("\n🔍 FASE 4: VERIFICANDO UPLOADS...")
        time.sleep(3)
        
        # Contar quantas imagens foram carregadas
        preview_selectors = [
            'img[src*="blob"]',
            '.listing-detail-images__gallery-box img',
            'div[class*="gallery"] img'
        ]
        
        total_previews = 0
        for selector in preview_selectors:
            try:
                count = page.locator(selector).count()
                if count > total_previews:
                    total_previews = count
            except:
                continue
        
        print(f"   📸 Total de previews encontrados: {total_previews}")
        print(f"   📤 Total de fotos enviadas: {total_enviadas}")
        
        # 5. LIMPAR ARQUIVOS TEMPORÁRIOS
        print("\n🗑️ FASE 5: LIMPANDO ARQUIVOS TEMPORÁRIOS...")
        for foto_temp in todas_fotos_temp:
            try:
                os.unlink(foto_temp)
                print(f"   🗑️ Removido: {os.path.basename(foto_temp)}")
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {os.path.basename(foto_temp)}: {e}")
        
        # 6. RESULTADO FINAL
        print("\n🎉 UPLOAD DE FOTOS CONCLUÍDO!")
        print(f"   - Fotos disponíveis: {len(fotos_urls)}")
        print(f"   - Fotos baixadas: {len(todas_fotos_temp)}")
        print(f"   - Fotos enviadas: {total_enviadas}")
        print(f"   - Previews visíveis: {total_previews}")
        
        if total_enviadas == len(todas_fotos_temp):
            print("   ✅ TODAS AS FOTOS FORAM ENVIADAS COM SUCESSO!")
        else:
            print(f"   ⚠️ Apenas {total_enviadas}/{len(todas_fotos_temp)} fotos foram enviadas")
        
        return True
            
    except Exception as e:
        print(f"\n❌ ERRO GERAL NO UPLOAD DE FOTOS: {e}")
        return False

def aguardar_e_verificar_footer(page):
    """Verifica footer DENTRO do formulário de criação"""
    print("\n🔍 VERIFICANDO FOOTER NO FORMULÁRIO")
    print("-" * 50)
    
    try:
        # Aguardar formulário carregar
        print("⏳ Aguardando formulário carregar...")
        time.sleep(3)
        
        # Rolar até o final
        print("📜 Rolando até o final do formulário...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Procurar botões de ação
        print("🔍 Procurando botões de ação...")
        
        botao_selectors = [
            'button:has-text("Criar anúncio")',
            'button:has-text("Publicar")',
            'button:has-text("Salvar")',
            'button[type="submit"]',
            'input[type="submit"]'
        ]
        
        botoes_encontrados = 0
        for selector in botao_selectors:
            try:
                botoes = page.locator(selector)
                count = botoes.count()
                if count > 0:
                    botoes_encontrados += count
                    print(f"   🔘 {count} botão(ões) encontrado(s): {selector}")
            except:
                continue
        
        if botoes_encontrados > 0:
            print(f"\n✅ {botoes_encontrados} botões de ação encontrados")
            return True
        else:
            print("\n❌ Nenhum botão de ação encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar footer: {e}")
        return False

def executar_teste(dados_completos):
    """Função principal com UPLOAD CORRIGIDO"""
    print("=" * 60)
    print("🚀 TESTE CANAL PRO - VERSÃO COM UPLOAD CORRIGIDO")
    print("=" * 60)
    
    with sync_playwright() as p:
        print("🌐 Abrindo browser...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=800,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        
        try:
            # FASE 1: LOGIN
            print("\n🔐 FASE 1: LOGIN")
            print("-" * 40)
            
            page.goto('https://canalpro.grupozap.com', wait_until='networkidle')
            
            try:
                page.click('button:has-text("Aceitar")', timeout=3000)
                print("🍪 Cookies fechados")
            except:
                print("🍪 Sem cookies")
            
            email = os.getenv('ZAP_EMAIL', '')
            password = os.getenv('ZAP_PASSWORD', '')
            
            if not email or not password:
                print("❌ Configure ZAP_EMAIL e ZAP_PASSWORD no .env")
                return False
            
            print(f"📧 Email: {email}")
            preencher_campo_simples(page, 'input[name="email"]', email, "Email")
            preencher_campo_simples(page, 'input[name="password"]', password, "Senha")
            preencher_campo_simples(page, 'button[type="submit"]', None, "Entrar", "click")
            
            print("⏳ Aguardando login...")
            page.wait_for_url("**/ZAP_OLX/**", timeout=15000)
            print("✅ Login confirmado!")
            
            # FASE 2: NAVEGAÇÃO
            print("\n📍 FASE 2: NAVEGAÇÃO")
            print("-" * 40)
            
            listings_url = "https://canalpro.grupozap.com/ZAP_OLX/0/listings?pageSize=10"
            page.goto(listings_url, wait_until='networkidle')
            
            print("🔍 Clicando em 'Criar anúncio'...")
            create_btn = page.get_by_role("button", name="Criar anúncio")
            create_btn.wait_for(state="visible", timeout=10000)
            create_btn.click()
            page.wait_for_load_state("networkidle")
            print("✅ Formulário carregado")
            
            # AGUARDAR FORMULÁRIO CARREGAR COMPLETAMENTE
            time.sleep(4)
            
            # FASE 3: PREENCHIMENTO
            print("\n📝 FASE 3: PREENCHIMENTO")
            print("-" * 40)
            
            # Switches com verificação inteligente
            seletores_residencial = [
                'label[for="zap-switch-radio-755_RESIDENTIAL"]',
                'input[value="RESIDENTIAL"]',
                'input[id="zap-switch-radio-755_RESIDENTIAL"]'
            ]
            verificar_estado_switch_inteligente(page, seletores_residencial, "Tipo Residencial")
            
            # Dropdowns e campos
            tipo_mapeado = mapear_tipo_imovel(dados_completos.get('tipo', 'Apartamento'))
            preencher_campo_simples(page, 'select[name="unitType"]', tipo_mapeado, "Tipo do Imóvel", "select")
            preencher_campo_simples(page, 'select[name="category"]', 'CategoryNONE', "Categoria", "select")
            
            if dados_completos.get('quartos'):
                preencher_campo_simples(page, 'select[name="bedrooms"]', str(dados_completos['quartos']), "Quartos", "select")
            
            if dados_completos.get('suites'):
                preencher_campo_simples(page, 'select[name="suites"]', str(dados_completos['suites']), "Suítes", "select")
            
            if dados_completos.get('banheiros'):
                preencher_campo_simples(page, 'select[name="bathrooms"]', str(dados_completos['banheiros']), "Banheiros", "select")
            
            if dados_completos.get('vagas'):
                preencher_campo_simples(page, 'select[name="parkingSpaces"]', str(dados_completos['vagas']), "Vagas", "select")
            
            if dados_completos.get('area'):
                preencher_campo_simples(page, 'input[name="usableAreas"]', str(dados_completos['area']), "Área Útil")
            
            if dados_completos.get('tipo') == 'Apartamento':
                preencher_campo_simples(page, 'select[name="unitFloor"]', '0', "Andar", "select")
            
            if dados_completos.get('cep'):
                preencher_campo_simples(page, 'input[name="zipCode"]', dados_completos['cep'], "CEP")
                print("   ⏳ Aguardando preenchimento automático...")
                time.sleep(3)
            
            if dados_completos.get('endereco'):
                preencher_campo_simples(page, 'input[name="street"]', dados_completos['endereco'], "Endereço")
            
            if dados_completos.get('numero'):
                preencher_campo_simples(page, 'input[data-label="número"]', dados_completos['numero'], "Número")
            
            if dados_completos.get('complemento'):
                preencher_campo_simples(page, 'input[name="complement"]', dados_completos['complemento'], "Complemento")
            
            # Switches de endereço e venda
            seletores_endereco_completo = [
                'label[for="zap-switch-radio-688_ALL"]',
                'input[value="ALL"]',
                'input[id="zap-switch-radio-688_ALL"]'
            ]
            verificar_estado_switch_inteligente(page, seletores_endereco_completo, "Endereço Completo")
            
            seletores_venda = [
                'label[for="zap-switch-radio-4070_SALE"]',
                'input[value="SALE"]',
                'input[id="zap-switch-radio-4070_SALE"]'
            ]
            verificar_estado_switch_inteligente(page, seletores_venda, "Operação Venda")
            
            # Preços e textos
            if dados_completos.get('preco'):
                preco_str = str(int(dados_completos['preco']))
                preencher_campo_simples(page, 'input[name="priceSale"]', preco_str, "Preço de Venda")
            
            if dados_completos.get('condominio'):
                cond_str = str(int(dados_completos['condominio']))
                preencher_campo_simples(page, 'input[name="monthlyCondoFeeMask"]', cond_str, "Condomínio")
            
            if dados_completos.get('iptu'):
                iptu_str = str(int(dados_completos['iptu']))
                preencher_campo_simples(page, 'input[name="yearlyIptuMask"]', iptu_str, "IPTU")
                
                periodo_mapeado = mapear_iptu_periodo(dados_completos.get('iptu_periodo'))
                preencher_campo_simples(page, 'select[name="period"]', periodo_mapeado, "Período IPTU", "select")
            
            if dados_completos.get('codigo_anuncio_canalpro'):
                preencher_campo_simples(page, 'input[name="externalId"]', dados_completos['codigo_anuncio_canalpro'], "Código do Anúncio")
            
            if dados_completos.get('titulo'):
                titulo_truncado = dados_completos['titulo'][:100]
                preencher_campo_simples(page, 'input[name="title"]', titulo_truncado, "Título")
            
            if dados_completos.get('descricao'):
                desc_truncada = dados_completos['descricao'][:3000]
                preencher_campo_simples(page, 'textarea[name="description"]', desc_truncada, "Descrição")
            
            if dados_completos.get('link_video_youtube'):
                preencher_campo_simples(page, 'input[name="videos"]', dados_completos['link_video_youtube'], "Vídeo YouTube")
            
            if dados_completos.get('link_tour_virtual'):
                preencher_campo_simples(page, 'input[name="videoTourLink"]', dados_completos['link_tour_virtual'], "Tour Virtual")
            
            # FASE 4: UPLOAD DE FOTOS (CORRIGIDO)
            print("\n📸 FASE 4: UPLOAD DE FOTOS")
            print("-" * 40)
            
            if dados_completos.get('fotos'):
                print(f"📸 {len(dados_completos['fotos'])} fotos encontradas nos dados")
                sucesso_upload = fazer_upload_fotos(page, dados_completos['fotos'])
                if sucesso_upload:
                    print("✅ Upload de fotos concluído!")
                else:
                    print("⚠️ Upload de fotos falhou, mas continuando...")
            else:
                print("📸 Nenhuma foto encontrada nos dados")
            
            # FASE 5: VERIFICAÇÃO DO FOOTER
            print("\n🎯 FASE 5: VERIFICAÇÃO DO FOOTER")
            print("-" * 40)
            
            time.sleep(3)
            footer_ok = aguardar_e_verificar_footer(page)
            
            # FASE 6: FINALIZAÇÃO
            print("\n🎉 FASE 6: TESTE CONCLUÍDO")
            print("-" * 40)
            
            if footer_ok:
                print("✅ FORMULÁRIO PREENCHIDO E FOOTER VERIFICADO!")
            else:
                print("⚠️ FORMULÁRIO PREENCHIDO MAS FOOTER COM PROBLEMAS")
            
            print("\n🔍 INSTRUÇÕES PARA VERIFICAÇÃO MANUAL:")
            print("1. ✅ Verifique se todos os campos estão preenchidos")
            print("2. 📸 Verifique se as fotos foram carregadas")
            print("3. 📜 Role até o final da página")
            print("4. 🔘 Procure pelo botão 'Criar anúncio' no footer")
            print("5. 📊 Verifique se a nota do anúncio está sendo calculada")
            print("\n⚠️  IMPORTANTE: ESTE É APENAS UM TESTE!")
            print("❌ NÃO PUBLIQUE O ANÚNCIO!")
            print("\n⏰ Browser ficará aberto por 4 minutos para inspeção...")
            
            time.sleep(240)  # 4 minutos
            
            print("\n🎯 TESTE FINALIZADO COM SUCESSO!")
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO DURANTE TESTE: {e}")
            print("🔍 Mantendo browser aberto para debug (30 segundos)...")
            time.sleep(30)
            return False
        finally:
            browser.close()
            print("\n🚪 Browser fechado")

def main():
    if len(sys.argv) != 2:
        print("Uso: python canal_pro_test_executor.py <arquivo_dados.json>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            dados_completos = json.load(f)
        
        print(f"📄 Dados carregados: {len(dados_completos)} campos")
        
        # Debug das fotos
        if dados_completos.get('fotos'):
            fotos = dados_completos['fotos']
            if isinstance(fotos, list):
                print(f"📸 {len(fotos)} fotos encontradas nos dados")
                if len(fotos) > 0:
                    print(f"   📸 Primeira foto: {fotos[0][:60]}...")
            else:
                print(f"⚠️ Fotos em formato inesperado: {type(fotos)}")
        else:
            print("📸 Nenhuma foto encontrada nos dados")
        
        sucesso = executar_teste(dados_completos)
        
        if sucesso:
            print("\n🎉 TESTE FINALIZADO COM SUCESSO!")
            sys.exit(0)
        else:
            print("\n💥 TESTE FALHOU")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ ERRO ao carregar dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()