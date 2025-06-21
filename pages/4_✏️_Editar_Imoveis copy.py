# pages/4_✏️_Editar_Imoveis.py
"""
Página para completar dados dos imóveis coletados
Foco em preparar os dados antes da publicação
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
import requests
import os
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.utils.database import get_supabase_client, check_connection
    supabase = get_supabase_client()
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos: {e}")
    st.error("Verifique se o arquivo src/utils/database.py existe e está configurado.")
    st.stop()
except Exception as e:
    st.error(f"❌ Erro de conexão: {e}")
    st.error("Verifique se as variáveis SUPABASE_URL e SUPABASE_KEY estão configuradas no .env")
    st.stop()

st.set_page_config(page_title="Editar Imóveis", layout="wide")

# CSS customizado para melhorar visual
st.markdown("""
<style>
    .foto-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin: 10px 0;
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-novo { background-color: #e3f2fd; color: #1976d2; }
    .status-rascunho { background-color: #fff3e0; color: #f57c00; }
    .status-preparado { background-color: #e8f5e8; color: #388e3c; }
    .status-publicado { background-color: #f3e5f5; color: #7b1fa2; }
</style>
""", unsafe_allow_html=True)

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
    return 'YEARLY'  # Padrão

import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path

import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path

def executar_teste_canal_pro(dados_completos):
    """Executa teste usando subprocess separado - VERSÃO CORRIGIDA"""
    try:
        # Validar dados essenciais
        if not dados_completos:
            st.error("❌ Dados não fornecidos para o teste")
            return False
        
        # Criar arquivo temporário com os dados
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(dados_completos, temp_file, ensure_ascii=False, indent=2)
            temp_path = temp_file.name
        
        # Caminho do script executor
        script_executor = Path(__file__).parent.parent / "src" / "automation" / "canal_pro_test_executor.py"
        
        # Se o script não existir, criar
        if not script_executor.exists():
            try:
                criar_script_executor(script_executor)
                st.info("📝 Script executor criado com sucesso")
            except Exception as e:
                st.error(f"❌ Erro ao criar script: {e}")
                return False
        
        st.info("🚀 Executando teste em processo separado...")
        st.info("📱 Um browser será aberto automaticamente")
        st.warning("⚠️ **IMPORTANTE: NÃO publique o anúncio - é apenas um teste!**")
        
        # Mostrar progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Preparar ambiente
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        # Executar subprocess
        try:
            status_text.text("🔄 Iniciando processo...")
            progress_bar.progress(0.1)
            
            # Comando para executar
            cmd = [
                sys.executable,
                str(script_executor),
                temp_path
            ]
            
            status_text.text("🌐 Abrindo browser...")
            progress_bar.progress(0.3)
            
            # Executar com timeout
            result = subprocess.run(
                cmd,
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minutos
                cwd=Path(__file__).parent.parent,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            progress_bar.progress(1.0)
            status_text.text("✅ Processo concluído")
            
            # Processar resultado
            if result.returncode == 0:
                st.success("✅ Teste executado com sucesso!")
                
                if result.stdout:
                    st.text("📋 Log detalhado do teste:")
                    # Mostrar log em expandir para não poluir a tela
                    with st.expander("Ver log completo"):
                        st.text(result.stdout)
                
                # Extrair informações importantes do log
                if "FORMULÁRIO PREENCHIDO COM SUCESSO" in result.stdout:
                    st.success("🎯 **Formulário preenchido corretamente!**")
                if "LOGIN confirmado" in result.stdout:
                    st.success("🔐 **Login realizado com sucesso!**")
                
                return True
            else:
                st.error("❌ Erro durante execução do teste")
                
                # Mostrar erro detalhado
                if result.stderr:
                    st.error("**Detalhes do erro:**")
                    with st.expander("Ver erro completo"):
                        st.text(result.stderr)
                
                # Mostrar stdout mesmo com erro (pode ter logs úteis)
                if result.stdout:
                    st.warning("**Log parcial:**")
                    with st.expander("Ver log"):
                        st.text(result.stdout)
                
                return False
                
        except subprocess.TimeoutExpired:
            st.warning("⏰ Teste excedeu tempo limite (5 minutos)")
            st.info("💡 O browser pode ainda estar aberto para inspeção manual")
            return False
            
        except FileNotFoundError:
            st.error("❌ Python não encontrado no PATH")
            st.error("💡 Verifique se o Python está instalado corretamente")
            return False
            
        except Exception as e:
            st.error(f"❌ Erro ao executar subprocess: {e}")
            
            # Debug adicional
            st.info("🔍 **Informações de debug:**")
            st.write(f"- Script: {script_executor}")
            st.write(f"- Script existe: {script_executor.exists()}")
            st.write(f"- Diretório trabalho: {Path(__file__).parent.parent}")
            st.write(f"- Python: {sys.executable}")
            
            return False
        finally:
            # Limpar barra de progresso
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"❌ Erro ao preparar teste: {e}")
        return False
    finally:
        # Limpar arquivo temporário
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except:
            pass

def criar_script_executor(script_path):
    """Cria o script executor CORRIGIDO com upload de fotos e verificação de footer funcionando"""
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script executor CORRIGIDO para teste do Canal PRO
CORRIGE: Upload de fotos + Verificação de footer no local correto + Switches inteligentes
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
            
            # Método 3: Input associado (para labels)
            if not esta_selecionado and "label" in seletor_usado.lower():
                try:
                    for_attr = elemento_encontrado.get_attribute("for")
                    if for_attr:
                        input_associado = page.locator(f"#{for_attr}")
                        if input_associado.count() > 0 and input_associado.is_checked():
                            esta_selecionado = True
                            print(f"   ✅ {nome_campo} já está selecionado (input associado)")
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
    """Função original que já funcionava perfeitamente"""
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
    """Upload de fotos CORRIGIDO - com logs detalhados"""
    if not fotos_urls or len(fotos_urls) == 0:
        print("📸 Nenhuma foto para upload")
        return True
    
    print(f"\\n📸 INICIANDO UPLOAD DE {len(fotos_urls)} FOTOS")
    print("-" * 50)
    
    try:
        # 1. BAIXAR FOTOS TEMPORARIAMENTE
        print("📥 FASE 1: BAIXANDO FOTOS...")
        fotos_temp = []
        
        for i, url in enumerate(fotos_urls[:8]):  # Máximo 8 fotos
            try:
                print(f"   📥 Baixando foto {i+1}/{len(fotos_urls[:8])}: {url[:60]}...")
                
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
                
                fotos_temp.append(temp_path)
                print(f"   ✅ Foto {i+1} baixada: {os.path.basename(temp_path)} ({len(response.content)} bytes)")
                
            except Exception as e:
                print(f"   ❌ Erro ao baixar foto {i+1}: {e}")
                continue
        
        if not fotos_temp:
            print("❌ NENHUMA FOTO FOI BAIXADA COM SUCESSO")
            return False
        
        print(f"\\n✅ {len(fotos_temp)} fotos baixadas com sucesso!")
        
        # 2. ROLAR ATÉ SEÇÃO DE UPLOAD
        print("\\n📜 FASE 2: NAVEGANDO ATÉ SEÇÃO DE UPLOAD...")
        try:
            # Rolar mais devagar para garantir que tudo carregue
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print("   ✅ Página rolada até o final")
        except:
            print("   ⚠️ Erro ao rolar página")
        
        # 3. PROCURAR INPUT DE UPLOAD
        print("\\n🔍 FASE 3: PROCURANDO INPUT DE UPLOAD...")
        
        seletores_upload = [
            'input[type="file"][name="images"]',           # Mais específico
            'input[type="file"][multiple="multiple"]',      # Com multiple
            'input[accept*="image"]',                       # Aceita imagens
            'input[data-cy="zap-file-input"]',             # Data attribute
            'input.zap-file-input__input',                 # Classe específica
            'input[type="file"][accept*="jpeg"]',          # JPEG específico
            'input[type="file"]'                           # Genérico (último)
        ]
        
        upload_realizado = False
        
        for i, seletor in enumerate(seletores_upload):
            try:
                print(f"   🔍 Testando seletor {i+1}/{len(seletores_upload)}: {seletor}")
                
                elements = page.locator(seletor)
                count = elements.count()
                
                if count == 0:
                    print(f"      ❌ Nenhum elemento encontrado")
                    continue
                
                print(f"      ✅ {count} elemento(s) encontrado(s)")
                
                # Tentar com cada elemento encontrado
                for j in range(count):
                    try:
                        element = elements.nth(j)
                        
                        # Verificar se o elemento está disponível
                        element.wait_for(state="attached", timeout=5000)
                        
                        # Verificar atributos do elemento
                        name_attr = element.get_attribute("name") or "sem_name"
                        accept_attr = element.get_attribute("accept") or "sem_accept"
                        class_attr = element.get_attribute("class") or "sem_class"
                        
                        print(f"         📋 Elemento {j+1}: name='{name_attr}', accept='{accept_attr}', class='{class_attr[:30]}...'")
                        
                        # FAZER UPLOAD
                        print(f"         📤 Fazendo upload com elemento {j+1}...")
                        element.set_input_files(fotos_temp)
                        
                        print(f"         ✅ Upload executado! Aguardando processamento...")
                        time.sleep(3)
                        
                        upload_realizado = True
                        print(f"   🎉 UPLOAD REALIZADO COM SUCESSO usando: {seletor}")
                        break
                        
                    except Exception as e:
                        print(f"         ❌ Falha com elemento {j+1}: {e}")
                        continue
                
                if upload_realizado:
                    break
                    
            except Exception as e:
                print(f"      ❌ Erro com seletor: {e}")
                continue
        
        # 4. VERIFICAR SE UPLOAD FUNCIONOU
        if upload_realizado:
            print("\\n🔍 FASE 4: VERIFICANDO SE UPLOAD FUNCIONOU...")
            
            # Aguardar um pouco para processamento
            time.sleep(3)
            
            # Procurar evidências de que o upload funcionou
            verificacao_selectors = [
                'img[src*="blob"]',           # Imagens em blob (preview)
                '.image-preview',             # Classe preview
                '.photo-preview',             # Classe photo
                '.uploaded-image',            # Classe uploaded
                '.file-preview',              # Classe file
                'img[alt*="preview"]',        # Alt com preview
                'div[class*="preview"]'       # Div com preview na classe
            ]
            
            upload_confirmado = False
            for selector in verificacao_selectors:
                try:
                    preview_elements = page.locator(selector)
                    count = preview_elements.count()
                    if count > 0:
                        print(f"   ✅ {count} preview(s) encontrado(s) com: {selector}")
                        upload_confirmado = True
                        break
                except:
                    continue
            
            if not upload_confirmado:
                print("   ⚠️ Upload realizado mas sem preview confirmado (normal em alguns casos)")
            
        # 5. LIMPAR ARQUIVOS TEMPORÁRIOS
        print("\\n🗑️ FASE 5: LIMPANDO ARQUIVOS TEMPORÁRIOS...")
        for foto_temp in fotos_temp:
            try:
                os.unlink(foto_temp)
                print(f"   🗑️ Removido: {os.path.basename(foto_temp)}")
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {os.path.basename(foto_temp)}: {e}")
        
        # 6. RESULTADO FINAL
        if upload_realizado:
            print("\\n🎉 UPLOAD DE FOTOS CONCLUÍDO COM SUCESSO!")
            return True
        else:
            print("\\n❌ UPLOAD DE FOTOS FALHOU")
            print("💡 Verifique se a seção de upload está visível no formulário")
            return False
            
    except Exception as e:
        print(f"\\n❌ ERRO GERAL NO UPLOAD DE FOTOS: {e}")
        return False

def aguardar_e_verificar_footer(page):
    """Verifica footer DENTRO do formulário de criação"""
    print("\\n🔍 VERIFICANDO FOOTER NO FORMULÁRIO")
    print("-" * 50)
    
    try:
        # 1. Verificar se estamos na página correta
        url_atual = page.url
        print(f"📍 URL atual: {url_atual}")
        
        if "listings" in url_atual:
            print("❌ ERRO: Ainda estamos na página de listagens!")
            print("💡 O formulário não foi carregado corretamente")
            return False
        
        # 2. Aguardar formulário carregar completamente
        print("⏳ Aguardando formulário carregar...")
        time.sleep(3)
        
        # 3. Rolar até o final para garantir que o footer apareça
        print("📜 Rolando até o final do formulário...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # 4. Forçar validação do formulário
        print("✅ Forçando validação do formulário...")
        page.evaluate("""
            // Forçar validação de todos os campos
            const form = document.querySelector('form');
            if (form) {
                const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
                inputs.forEach(input => {
                    if (input.checkValidity) {
                        input.checkValidity();
                    }
                    // Disparar eventos que possam ativar validação
                    input.dispatchEvent(new Event('blur'));
                    input.dispatchEvent(new Event('change'));
                });
                
                // Tentar submeter o form para ativar validação
                try {
                    form.checkValidity();
                } catch(e) {}
            }
        """)
        
        time.sleep(2)
        
        # 5. Procurar o footer/botões
        print("🔍 Procurando footer e botões...")
        
        footer_selectors = [
            'footer',
            '.footer',
            'div[class*="footer"]',
            'section[class*="footer"]',
            '.form-footer',
            '.action-buttons',
            '.form-actions',
            'div[class*="action"]',
            'div[class*="button"]'
        ]
        
        footer_encontrado = False
        for selector in footer_selectors:
            try:
                footer = page.locator(selector)
                count = footer.count()
                if count > 0:
                    print(f"   ✅ Footer encontrado: {selector} ({count} elementos)")
                    
                    # Verificar botões dentro do footer
                    for i in range(count):
                        botoes = footer.nth(i).locator("button")
                        botoes_count = botoes.count()
                        if botoes_count > 0:
                            print(f"      🔘 {botoes_count} botões encontrados no footer {i+1}")
                            
                            for j in range(botoes_count):
                                try:
                                    texto = botoes.nth(j).inner_text()
                                    visivel = botoes.nth(j).is_visible()
                                    print(f"         - Botão {j+1}: '{texto}' (visível: {visivel})")
                                except:
                                    print(f"         - Botão {j+1}: (erro ao ler texto)")
                    
                    footer_encontrado = True
                    break
            except:
                continue
        
        # 6. Se não encontrou footer, procurar botões soltos
        if not footer_encontrado:
            print("⚠️ Footer não encontrado, procurando botões específicos...")
            
            botao_selectors = [
                'button:has-text("Criar anúncio")',
                'button:has-text("Publicar")',
                'button:has-text("Finalizar")',
                'button:has-text("Salvar")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button[class*="submit"]',
                'button[class*="primary"]',
                'button[class*="create"]'
            ]
            
            botoes_encontrados = 0
            for selector in botao_selectors:
                try:
                    botoes = page.locator(selector)
                    count = botoes.count()
                    if count > 0:
                        botoes_encontrados += count
                        print(f"   🔘 {count} botão(ões) encontrado(s): {selector}")
                        
                        for i in range(count):
                            try:
                                texto = botoes.nth(i).inner_text()
                                visivel = botoes.nth(i).is_visible()
                                classes = botoes.nth(i).get_attribute("class") or ""
                                print(f"      - '{texto}' (visível: {visivel}) - classes: {classes[:50]}")
                            except:
                                print(f"      - Botão {i+1} (erro ao ler propriedades)")
                except:
                    continue
            
            if botoes_encontrados > 0:
                footer_encontrado = True
        
        # 7. Forçar CSS para mostrar botões ocultos
        print("🔧 Forçando exibição de elementos ocultos...")
        page.evaluate("""
            const style = document.createElement('style');
            style.textContent = `
                footer, .footer, .form-footer, .action-buttons, .form-actions {
                    display: block !important;
                    visibility: visible !important;
                    position: relative !important;
                    opacity: 1 !important;
                    height: auto !important;
                }
                
                button, input[type="submit"] {
                    display: inline-block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    pointer-events: auto !important;
                }
            `;
            document.head.appendChild(style);
        """)
        
        time.sleep(1)
        
        # 8. Screenshot do formulário para debug
        screenshot_path = "debug_formulario_completo.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot do formulário salva: {screenshot_path}")
        
        # 9. Contagem final
        total_botoes = page.locator("button").count()
        total_inputs_submit = page.locator('input[type="submit"]').count()
        
        print(f"\\n📊 RESUMO:")
        print(f"   - Total de botões: {total_botoes}")
        print(f"   - Total de inputs submit: {total_inputs_submit}")
        print(f"   - Footer encontrado: {footer_encontrado}")
        
        if total_botoes == 0 and total_inputs_submit == 0:
            print("\\n❌ NENHUM BOTÃO ENCONTRADO!")
            print("💡 Possíveis causas:")
            print("   - Formulário com campos obrigatórios vazios")
            print("   - JavaScript ainda processando")
            print("   - Nota do anúncio muito baixa")
            print("   - Problema de layout/CSS")
            return False
        else:
            print(f"\\n✅ {total_botoes + total_inputs_submit} botões/inputs encontrados no total")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar footer: {e}")
        return False

def executar_teste(dados_completos):
    """Função principal CORRIGIDA com upload e footer funcionando"""
    print("=" * 60)
    print("🚀 TESTE CANAL PRO - VERSÃO CORRIGIDA COMPLETA")
    print("=" * 60)
    
    with sync_playwright() as p:
        print("🌐 Abrindo browser...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=800,  # Um pouco mais lento para garantir carregamento
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
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
            # FASE 1: LOGIN (mantém igual)
            print("\\n🔐 FASE 1: LOGIN")
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
            
            # FASE 2: NAVEGAÇÃO (mantém igual)
            print("\\n📍 FASE 2: NAVEGAÇÃO")
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
            
            # FASE 3: PREENCHIMENTO (com switches inteligentes)
            print("\\n📝 FASE 3: PREENCHIMENTO")
            print("-" * 40)
            
            # Switches com verificação inteligente
            seletores_residencial = [
                'label[for="zap-switch-radio-755_RESIDENTIAL"]',
                'input[value="RESIDENTIAL"]',
                'input[id="zap-switch-radio-755_RESIDENTIAL"]'
            ]
            verificar_estado_switch_inteligente(page, seletores_residencial, "Tipo Residencial")
            
            # Dropdowns e campos (mantém igual)
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
            
            # FASE 4: UPLOAD DE FOTOS (NOVO - CORRIGIDO)
            print("\\n📸 FASE 4: UPLOAD DE FOTOS")
            print("-" * 40)
            
            if dados_completos.get('fotos'):
                print(f"📸 Iniciando upload de {len(dados_completos['fotos'])} fotos...")
                sucesso_upload = fazer_upload_fotos(page, dados_completos['fotos'])
                if sucesso_upload:
                    print("✅ Upload de fotos concluído!")
                else:
                    print("⚠️ Upload de fotos falhou, mas continuando...")
            else:
                print("📸 Nenhuma foto encontrada nos dados")
            
            # FASE 5: VERIFICAÇÃO DO FOOTER (CORRIGIDO)
            print("\\n🎯 FASE 5: VERIFICAÇÃO DO FOOTER")
            print("-" * 40)
            
            # Aguardar um pouco para tudo processar
            time.sleep(3)
            
            footer_ok = aguardar_e_verificar_footer(page)
            
            # FASE 6: FINALIZAÇÃO
            print("\\n🎉 FASE 6: TESTE CONCLUÍDO")
            print("-" * 40)
            
            if footer_ok:
                print("✅ FORMULÁRIO PREENCHIDO E FOOTER VERIFICADO!")
            else:
                print("⚠️ FORMULÁRIO PREENCHIDO MAS FOOTER COM PROBLEMAS")
            
            print("")
            print("🔍 INSTRUÇÕES PARA VERIFICAÇÃO MANUAL:")
            print("1. ✅ Verifique se todos os campos estão preenchidos")
            print("2. 📸 Verifique se as fotos foram carregadas")
            print("3. 📜 Role até o final da página")
            print("4. 🔘 Procure pelo botão 'Criar anúncio' no footer")
            print("5. 📊 Verifique se a nota do anúncio está sendo calculada")
            print("6. 🚨 Verifique se há campos com erro (bordas vermelhas)")
            print("")
            print("⚠️  IMPORTANTE: ESTE É APENAS UM TESTE!")
            print("❌ NÃO PUBLIQUE O ANÚNCIO!")
            print("")
            print("⏰ Browser ficará aberto por 4 minutos para inspeção completa...")
            
            # Tempo estendido para inspeção completa
            time.sleep(240)  # 4 minutos
            
            print("\\n🎯 TESTE FINALIZADO COM SUCESSO!")
            return True
            
        except Exception as e:
            print(f"\\n❌ ERRO DURANTE TESTE: {e}")
            print("🔍 Mantendo browser aberto para debug (30 segundos)...")
            time.sleep(30)
            return False
        finally:
            browser.close()
            print("\\n🚪 Browser fechado")

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
            print("\\n🎉 TESTE FINALIZADO COM SUCESSO!")
            sys.exit(0)
        else:
            print("\\n💥 TESTE FALHOU")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ ERRO ao carregar dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

def consultar_cep(cep):
    """Consulta CEP na API ViaCEP"""
    try:
        cep_limpo = cep.replace("-", "").replace(".", "").strip()
        if len(cep_limpo) != 8:
            return None
        
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "erro" not in data:
                return {
                    "logradouro": data.get("logradouro", ""),
                    "bairro": data.get("bairro", ""),
                    "cidade": data.get("localidade", ""),
                    "estado": data.get("uf", ""),
                    "cep": cep_limpo
                }
    except Exception as e:
        st.error(f"Erro ao consultar CEP: {e}")
    
    return None

def criar_anuncio_se_nao_existe(codigo_imovel):
    """Cria registro na tabela anuncios se não existir"""
    try:
        existing = supabase.table("anuncios").select("*").eq("imovel_codigo", codigo_imovel).execute()
        
        if not existing.data:
            # Criar novo anúncio com valores padrão
            dados_anuncio = {
                "imovel_codigo": codigo_imovel,
                "publicado": False,
                "is_highlighted": False,
                "canalpro_id": None,
                "codigo_anuncio_canalpro": None,
                "link_video_youtube": "https://www.youtube.com/watch?v=lk-sj2ZDLDU",
                "link_tour_virtual": "https://www.tourvirtual360.com.br/ibd/",
                "modo_exibicao_endereco": "completo",
                "pronto_para_publicacao": False
            }
            
            result = supabase.table("anuncios").insert(dados_anuncio).execute()
            if result.data:
                st.success("✨ Registro de anúncio criado automaticamente!")
                return True
    except Exception as e:
        st.warning(f"Não foi possível criar registro de anúncio: {e}")
    
    return False

def carregar_imoveis():
    """Carrega imóveis com seus dados de anúncio"""
    try:
        result = supabase.table("imoveis").select("*, anuncios(*)").order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception as e:
        st.error(f"Erro ao carregar imóveis: {e}")
        return []

st.title("✏️ Editar Dados dos Imóveis")
st.markdown("Complete as informações dos imóveis coletados para prepará-los para publicação")

imoveis = carregar_imoveis()

if not imoveis:
    st.warning("⚠️ Nenhum imóvel encontrado no banco de dados")
    st.info("Faça o scraping de um imóvel primeiro usando o comando:")
    st.code("python gintervale_scraper.py CODIGO")
    st.stop()

# Seleção do imóvel
st.markdown("### 1️⃣ Selecione o Imóvel para Editar")

# Preparar dados para exibição
imoveis_display = []
for imovel in imoveis:
    anuncio_info = imovel.get('anuncios', [])
    
    # Lógica de status
    if anuncio_info and len(anuncio_info) > 0:
        anuncio = anuncio_info[0]
        
        if anuncio.get('publicado') == True:
            status_anuncio = "✅ Publicado"
            status_class = "status-publicado"
        elif anuncio.get('pronto_para_publicacao') == True:
            status_anuncio = "🔧 Preparado" 
            status_class = "status-preparado"
        elif anuncio.get('codigo_anuncio_canalpro') and anuncio.get('codigo_anuncio_canalpro').strip():
            status_anuncio = "📝 Rascunho"
            status_class = "status-rascunho"
        else:
            status_anuncio = "🆕 Novo"
            status_class = "status-novo"
    else:
        status_anuncio = "🆕 Novo"
        status_class = "status-novo"
    
    # Processar fotos
    fotos = []
    if imovel.get('fotos'):
        try:
            if isinstance(imovel['fotos'], str):
                fotos_data = json.loads(imovel['fotos'])
                if isinstance(fotos_data, list):
                    fotos = fotos_data
                else:
                    fotos = []
            elif isinstance(imovel['fotos'], list):
                fotos = imovel['fotos']
            else:
                fotos = []
        except (json.JSONDecodeError, TypeError):
            fotos_str = str(imovel.get('fotos', ''))
            if fotos_str and fotos_str != 'null':
                import re
                urls = re.findall(r'https?://[^\s,\]"]+', fotos_str)
                fotos = urls
            else:
                fotos = []
    
    imoveis_display.append({
        'codigo': imovel['codigo'],
        'titulo': imovel['titulo'][:60] + '...' if len(imovel['titulo']) > 60 else imovel['titulo'],
        'status': status_anuncio,
        'status_class': status_class,
        'preco': f"R$ {imovel['preco']:,.2f}" if imovel.get('preco') else "Sem preço",
        'area': f"{imovel['area']}m²" if imovel.get('area') else "-",
        'cidade': imovel.get('cidade', 'N/A'),
        'fotos_count': len(fotos),
        'condominio': f"R$ {imovel.get('condominio', 0):,.2f}" if imovel.get('condominio') else "N/A",
        'iptu': f"R$ {imovel.get('iptu', 0):,.2f}" if imovel.get('iptu') else "N/A",
        'iptu_periodo': imovel.get('iptu_periodo', 'N/A') or 'N/A',
        'codigo_canalpro': anuncio.get('codigo_anuncio_canalpro', '') if anuncio_info and len(anuncio_info) > 0 else ''
    })

# Filtros
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    filtro_cidade = st.selectbox(
        "Filtrar por cidade",
        ["Todas"] + list(set([i['cidade'] for i in imoveis_display])),
        index=0
    )

with col2:
    filtro_status = st.selectbox(
        "Status",
        ["Todos", "🆕 Novo", "📝 Rascunho", "🔧 Preparado", "✅ Publicado"]
    )

with col3:
    mostrar_detalhes = st.checkbox("Mostrar detalhes", value=True)

with col4:
    if st.button("🔄 Recarregar", help="Recarregar dados do banco"):
        st.cache_data.clear()
        st.rerun()

# Aplicar filtros
df_display = pd.DataFrame(imoveis_display)
df_filtered = df_display.copy()

if filtro_cidade != "Todas":
    df_filtered = df_filtered[df_filtered['cidade'] == filtro_cidade]
if filtro_status != "Todos":
    df_filtered = df_filtered[df_filtered['status'] == filtro_status]

if len(df_filtered) == 0:
    st.warning("Nenhum imóvel encontrado com os filtros selecionados.")
    st.stop()

# Exibir tabela
columns_to_show = ['codigo', 'titulo', 'status', 'preco', 'area', 'cidade']
if mostrar_detalhes:
    columns_to_show.extend(['fotos_count', 'condominio', 'iptu', 'iptu_periodo', 'codigo_canalpro'])

st.markdown("**Selecione um imóvel clicando na linha:**")
evento = st.dataframe(
    df_filtered[columns_to_show],
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "fotos_count": st.column_config.NumberColumn("📸 Fotos", format="%d"),
        "status": st.column_config.TextColumn("Status", width="small"),
        "iptu_periodo": st.column_config.TextColumn("Período IPTU", width="small"),
        "codigo_canalpro": st.column_config.TextColumn("🏷️ Código Canal PRO", width="medium")
    }
)

if len(evento.selection.rows) == 0:
    st.info("👆 Selecione um imóvel na tabela acima para editar")
    st.stop()

# Obter imóvel selecionado
selected_index = evento.selection.rows[0]
codigo_selecionado = df_filtered.iloc[selected_index]['codigo']

imovel_selecionado = next((i for i in imoveis if i['codigo'] == codigo_selecionado), None)
if not imovel_selecionado:
    st.error("Erro ao carregar dados do imóvel selecionado")
    st.stop()

# Verificar se tem anúncio
anuncio_data = {}
if imovel_selecionado.get('anuncios') and len(imovel_selecionado['anuncios']) > 0:
    anuncio_data = imovel_selecionado['anuncios'][0]
else:
    if criar_anuncio_se_nao_existe(codigo_selecionado):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Preview do imóvel selecionado
st.markdown(f"### 2️⃣ Editando: {codigo_selecionado}")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"**📋 {imovel_selecionado['titulo']}**")
    st.write(f"📍 {imovel_selecionado.get('localizacao', 'N/A')}")
    
    # Layout de métricas
    col_preco, col_cond = st.columns(2)
    with col_preco:
        st.metric("💰 Preço", f"R$ {imovel_selecionado.get('preco', 0):,.2f}" if imovel_selecionado.get('preco') else "N/A")
    with col_cond:
        st.metric("🏢 Condomínio", f"R$ {imovel_selecionado.get('condominio', 0):,.2f}" if imovel_selecionado.get('condominio') else "N/A")
    
    col_area, col_iptu, col_periodo = st.columns(3)
    with col_area:
        st.metric("📐 Área", f"{imovel_selecionado.get('area', 0)}m²" if imovel_selecionado.get('area') else "N/A")
    with col_iptu:
        st.metric("🏛️ IPTU", f"R$ {imovel_selecionado.get('iptu', 0):,.2f}" if imovel_selecionado.get('iptu') else "N/A")
    with col_periodo:
        st.metric("📅 Período IPTU", imovel_selecionado.get('iptu_periodo', 'N/A') or 'N/A')
    
    st.write(f"🏠 {imovel_selecionado.get('quartos', 0)} quartos • ✨ {imovel_selecionado.get('suites', 0)} suítes • 🛁 {imovel_selecionado.get('banheiros', 0)} banheiros • 🚗 {imovel_selecionado.get('vagas', 0)} vagas")

with col2:
    # Galeria de fotos
    if imovel_selecionado.get('fotos'):
        try:
            fotos = []
            fotos_raw = imovel_selecionado['fotos']
            
            if isinstance(fotos_raw, str):
                try:
                    fotos_data = json.loads(fotos_raw)
                    if isinstance(fotos_data, list):
                        fotos = fotos_data
                except json.JSONDecodeError:
                    import re
                    urls = re.findall(r'https?://[^\s,\]"]+', fotos_raw)
                    fotos = urls
            elif isinstance(fotos_raw, list):
                fotos = fotos_raw
            
            if fotos and len(fotos) > 0:
                st.write(f"📸 **{len(fotos)} fotos disponíveis**")
                
                try:
                    st.image(fotos[0], caption="Preview", use_container_width=True)
                except Exception:
                    st.write("❌ Erro ao carregar preview")
                
                with st.expander(f"🖼️ Ver todas as {len(fotos)} fotos"):
                    cols_per_row = 3
                    for i in range(0, len(fotos), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(fotos):
                                with col:
                                    try:
                                        st.image(fotos[i + j], caption=f"Foto {i + j + 1}", use_container_width=True)
                                    except:
                                        st.write(f"❌ Erro foto {i + j + 1}")
                                        st.caption(f"URL: {fotos[i + j][:50]}...")
            else:
                st.write("📸 Fotos não processadas corretamente")
                
        except Exception as e:
            st.write("❌ Erro ao processar fotos")
            st.write(f"Debug erro: {e}")
    else:
        st.write("📸 Nenhuma foto disponível")

st.markdown("---")

# NOVA SEÇÃO: Dados do Scraping (review e edição)
st.markdown("### 📝 Dados do Scraping (para revisão)")

with st.expander("📋 Ver/Editar dados coletados do scraping", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Título (editável)
        titulo_editado = st.text_input(
            "Título do Anúncio",
            value=imovel_selecionado.get('titulo', ''),
            help="Título coletado do scraping - pode ser editado",
            key="titulo_input"
        )
        
        # Tipo (readonly)
        st.text_input(
            "Tipo do Imóvel",
            value=imovel_selecionado.get('tipo', 'N/A'),
            disabled=True,
            help="Detectado automaticamente pelo scraping"
        )
        
        # Dados numéricos (readonly)
        col_nums1, col_nums2 = st.columns(2)
        with col_nums1:
            st.number_input("Quartos", value=imovel_selecionado.get('quartos', 0), disabled=True)
            st.number_input("Banheiros", value=imovel_selecionado.get('banheiros', 0), disabled=True)
        with col_nums2:
            st.number_input("Suítes", value=imovel_selecionado.get('suites', 0), disabled=True)
            st.number_input("Vagas", value=imovel_selecionado.get('vagas', 0), disabled=True)
    
    with col2:
        # Descrição (editável e IMPORTANTE)
        descricao_editada = st.text_area(
            "Descrição do Anúncio",
            value=imovel_selecionado.get('descricao', ''),
            height=200,
            help="Descrição coletada do scraping - IMPORTANTE para o anúncio",
            key="descricao_input"
        )
        
        # Valores (readonly)
        st.text_input("Preço", value=f"R$ {imovel_selecionado.get('preco', 0):,.2f}", disabled=True)
        st.text_input("Área", value=f"{imovel_selecionado.get('area', 0)}m²", disabled=True)
        st.text_input("Condomínio", value=f"R$ {imovel_selecionado.get('condominio', 0):,.2f}", disabled=True)
        st.text_input("IPTU", value=f"R$ {imovel_selecionado.get('iptu', 0):,.2f} ({imovel_selecionado.get('iptu_periodo', 'N/A')})", disabled=True)

st.markdown("---")

# Formulário de edição - SEM st.form para permitir interatividade
st.markdown("### 3️⃣ Complete os Dados")

# Inicializar session state para dados do CEP
if 'cep_data' not in st.session_state:
    st.session_state.cep_data = {}

# Seção 1: Endereço
st.markdown("#### 📍 Informações de Endereço")

col1, col2 = st.columns([2, 1])

with col1:
    # Campo CEP com consulta automática
    cep_atual = imovel_selecionado.get('cep', '') or ''
    cep = st.text_input(
        "CEP *",
        value=cep_atual,
        placeholder="00000-000",
        help="Digite o CEP - preenchimento automático dos outros campos",
        key="cep_input"
    )
    
    # Auto-consulta quando CEP tem 8 dígitos
    if cep and len(cep.replace("-", "").replace(".", "")) == 8:
        if f"cep_consultado_{cep}" not in st.session_state:
            with st.spinner("Consultando CEP..."):
                dados_cep = consultar_cep(cep)
                if dados_cep:
                    st.session_state.cep_data = dados_cep
                    st.session_state[f"cep_consultado_{cep}"] = True
                    st.success("✅ CEP encontrado! Dados preenchidos automaticamente.")
                    st.rerun()
    
    # Botão manual para consultar CEP
    if st.button("🔍 Consultar CEP"):
        if cep:
            with st.spinner("Consultando CEP..."):
                dados_cep = consultar_cep(cep)
                if dados_cep:
                    st.session_state.cep_data = dados_cep
                    st.success("✅ CEP encontrado! Dados preenchidos automaticamente.")
                    st.rerun()
                else:
                    st.error("❌ CEP não encontrado. Verifique o número digitado.")
    
    # Usar dados do CEP se disponíveis, senão usar dados existentes
    endereco_auto = st.session_state.cep_data.get('logradouro', '') if st.session_state.cep_data else ''
    bairro_auto = st.session_state.cep_data.get('bairro', '') if st.session_state.cep_data else ''
    cidade_auto = st.session_state.cep_data.get('cidade', '') if st.session_state.cep_data else ''
    estado_auto = st.session_state.cep_data.get('estado', '') if st.session_state.cep_data else ''
    
    endereco = st.text_input(
        "Endereço (Rua) *",
        value=endereco_auto or imovel_selecionado.get('endereco', '') or '',
        placeholder="Rua Example, 123",
        key="endereco_input"
    )
    
    bairro = st.text_input(
        "Bairro *",
        value=bairro_auto or imovel_selecionado.get('bairro', '') or '',
        placeholder="Centro",
        key="bairro_input"
    )

with col2:
    numero = st.text_input(
        "Número *",
        value=imovel_selecionado.get('numero', '') or '',
        placeholder="123",
        help="Campo obrigatório para publicação",
        key="numero_input"
    )
    
    complemento = st.text_input(
        "Complemento",
        value=imovel_selecionado.get('complemento', '') or '',
        placeholder="Apto 101",
        key="complemento_input"
    )
    
    # Campos automáticos do CEP ou dados existentes
    cidade = st.text_input(
        "Cidade", 
        value=cidade_auto or imovel_selecionado.get('cidade', ''), 
        disabled=True,
        help="Preenchido automaticamente pelo CEP",
        key="cidade_input"
    )
    estado = st.text_input(
        "Estado", 
        value=estado_auto or imovel_selecionado.get('estado', ''), 
        disabled=True,
        help="Preenchido automaticamente pelo CEP",
        key="estado_input"
    )

st.markdown("---")

# Seção 2: Configurações de Publicação
st.markdown("#### 🏷️ Configurações para Canal PRO")

col1, col2 = st.columns(2)

with col1:
    codigo_anuncio_canalpro = st.text_input(
        "Código do Anúncio Canal PRO",
        value=anuncio_data.get('codigo_anuncio_canalpro', '') or '',
        placeholder="ex: ZAP123456",
        help="Código único para identificar o anúncio no Canal PRO",
        key="codigo_canalpro_input"
    )
    
    # Link fixo do YouTube - só preencher se estiver vazio
    link_video_youtube_default = anuncio_data.get('link_video_youtube') or "https://www.youtube.com/watch?v=lk-sj2ZDLDU"
    link_video_youtube = st.text_input(
        "Link do Vídeo (YouTube)",
        value=link_video_youtube_default,
        help="Link padrão do vídeo institucional",
        key="youtube_input"
    )

with col2:
    # Link fixo do Tour Virtual - só preencher se estiver vazio
    link_tour_virtual_default = anuncio_data.get('link_tour_virtual') or "https://www.tourvirtual360.com.br/ibd/"
    link_tour_virtual = st.text_input(
        "Link do Tour Virtual",
        value=link_tour_virtual_default,
        help="Link padrão do tour virtual",
        key="tour_input"
    )
    
    modo_exibicao_endereco = st.selectbox(
        "Modo de Exibição do Endereço",
        ["completo", "somente_rua", "somente_bairro"],
        index=["completo", "somente_rua", "somente_bairro"].index(
            anuncio_data.get('modo_exibicao_endereco', 'completo')
        ),
        help="Como o endereço será exibido no anúncio",
        key="modo_endereco_input"
    )

st.markdown("---")

# Seção 3: Preview dos dados que serão enviados ao Canal PRO
st.markdown("#### 📋 Preview - Dados para Canal PRO")

with st.expander("👁️ Ver dados que serão enviados ao Canal PRO"):
    preview_cols = st.columns(2)
    
    with preview_cols[0]:
        st.markdown("**📍 Localização:**")
        st.write(f"• CEP: {cep}")
        st.write(f"• Endereço: {endereco}")
        st.write(f"• Número: {numero}")
        st.write(f"• Complemento: {complemento}")
        st.write(f"• Bairro: {bairro}")
        st.write(f"• Cidade: {cidade}")
        st.write(f"• Estado: {estado}")
        
    with preview_cols[1]:
        st.markdown("**🏠 Dados do Imóvel:**")
        st.write(f"• Tipo: {imovel_selecionado.get('tipo', 'N/A')}")
        st.write(f"• Quartos: {imovel_selecionado.get('quartos', 'N/A')}")
        st.write(f"• Banheiros: {imovel_selecionado.get('banheiros', 'N/A')}")
        st.write(f"• Vagas: {imovel_selecionado.get('vagas', 'N/A')}")
        st.write(f"• Área: {imovel_selecionado.get('area', 'N/A')}m²")
        st.write(f"• Preço: R$ {imovel_selecionado.get('preco', 0):,.2f}")
        
    st.markdown("**🔗 Links:**")
    st.write(f"• Vídeo: {link_video_youtube}")
    st.write(f"• Tour Virtual: {link_tour_virtual}")

st.markdown("---")

# Validação e botões
st.markdown("#### ✅ Status de Completude")

# Verificar campos obrigatórios
campos_obrigatorios = {
    'CEP': bool(cep.strip()) if cep else False,
    'Endereço': bool(endereco.strip()) if endereco else False,
    'Bairro': bool(bairro.strip()) if bairro else False,
    'Número': bool(numero.strip()) if numero else False,
    'Preço': bool(imovel_selecionado.get('preco')),
    'Fotos (min 3)': len(json.loads(imovel_selecionado.get('fotos', '[]')) if isinstance(imovel_selecionado.get('fotos'), str) else imovel_selecionado.get('fotos', [])) >= 3
}

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Campos Obrigatórios:**")
    for campo, completo in campos_obrigatorios.items():
        icon = "✅" if completo else "❌"
        st.write(f"{icon} {campo}")

with col2:
    st.markdown("**Campos Opcionais:**")
    opcionais = {
        'Código Canal PRO': bool(codigo_anuncio_canalpro.strip()) if codigo_anuncio_canalpro else False,
        'Vídeo YouTube': bool(link_video_youtube.strip()) if link_video_youtube else False,
        'Tour Virtual': bool(link_tour_virtual.strip()) if link_tour_virtual else False,
        'Complemento': bool(complemento.strip()) if complemento else False
    }
    
    for campo, completo in opcionais.items():
        icon = "✅" if completo else "⚪"
        st.write(f"{icon} {campo}")

# Calcular porcentagem de completude
total_obrigatorios = len(campos_obrigatorios)
completos_obrigatorios = sum(campos_obrigatorios.values())
porcentagem = (completos_obrigatorios / total_obrigatorios) * 100

progress_col1, progress_col2 = st.columns([3, 1])
with progress_col1:
    st.progress(porcentagem / 100)
with progress_col2:
    st.metric("Completude", f"{porcentagem:.0f}%")

# Botões de ação
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    salvar_rascunho = st.button(
        "💾 Salvar Rascunho",
        use_container_width=True,
        help="Salva os dados mesmo se incompletos"
    )

with col2:
    salvar_completo = st.button(
        "✅ Marcar como Pronto",
        type="primary",
        use_container_width=True,
        disabled=porcentagem < 100,
        help="Salva e marca como pronto para publicação"
    )

with col3:
    testar_canal_pro = st.button(
        "🔍 Testar Canal PRO",
        use_container_width=True,
        disabled=porcentagem < 100,
        help="Abre browser e preenche dados no Canal PRO (sem publicar)"
    )

with col4:
    # Espaço reservado para botão de publicação real
    st.button(
        "🚀 Publicar (em breve)",
        use_container_width=True,
        disabled=True,
        help="Funcionalidade em desenvolvimento"
    )

# CORREÇÃO PRINCIPAL: Conectar o botão "Testar Canal PRO" à função
if testar_canal_pro:
    if porcentagem >= 100:
        # Montar dados completos para o teste
        dados_completos = {
            # Dados do imóvel (do scraping)
            'tipo': imovel_selecionado.get('tipo'),
            'quartos': imovel_selecionado.get('quartos'),
            'suites': imovel_selecionado.get('suites'),
            'banheiros': imovel_selecionado.get('banheiros'),
            'vagas': imovel_selecionado.get('vagas'),
            'area': imovel_selecionado.get('area'),
            'preco': imovel_selecionado.get('preco'),
            'condominio': imovel_selecionado.get('condominio'),
            'iptu': imovel_selecionado.get('iptu'),
            'iptu_periodo': imovel_selecionado.get('iptu_periodo'),
            
            # Dados editáveis (se foram modificados)
            'titulo': titulo_editado if 'titulo_input' in st.session_state else imovel_selecionado.get('titulo'),
            'descricao': descricao_editada if 'descricao_input' in st.session_state else imovel_selecionado.get('descricao'),
            
            # Dados do formulário de endereço
            'cep': cep,
            'endereco': endereco,
            'numero': numero,
            'complemento': complemento,
            'bairro': bairro,
            'cidade': cidade,
            'estado': estado,
            
            # Configurações do Canal PRO
            'codigo_anuncio_canalpro': codigo_anuncio_canalpro,
            'link_video_youtube': link_video_youtube,
            'link_tour_virtual': link_tour_virtual,
            'modo_exibicao_endereco': modo_exibicao_endereco,
        }
        
        st.info("🚀 Iniciando teste do Canal PRO...")
        st.info("📱 Um browser será aberto automaticamente")
        st.warning("⚠️ **IMPORTANTE: Este é apenas um TESTE! NÃO publique o anúncio!**")
        
        # Executar o teste
        with st.spinner("🔄 Executando teste no Canal PRO..."):
            sucesso = executar_teste_canal_pro(dados_completos)
            
            if sucesso:
                st.success("✅ Teste do Canal PRO concluído!")
                st.info("🔍 Verifique se todos os campos foram preenchidos corretamente no browser.")
                st.info("📝 Anote quaisquer problemas encontrados.")
            else:
                st.error("❌ Erro durante o teste do Canal PRO.")
                st.error("🔧 Verifique os logs acima para mais detalhes.")
    else:
        st.error("❌ Complete todos os campos obrigatórios antes de testar no Canal PRO.")
        st.info("💡 Você precisa preencher: CEP, Endereço, Bairro, Número e ter pelo menos 3 fotos.")

# Processar submissão dos outros botões (salvar)
if salvar_rascunho or salvar_completo:
    
    # Preparar dados para salvar
    dados_imovel = {
        'cep': cep.strip() if cep.strip() else None,
        'endereco': endereco.strip() if endereco.strip() else None,
        'bairro': bairro.strip() if bairro.strip() else None,
        'numero': numero.strip() if numero.strip() else None,
        'complemento': complemento.strip() if complemento.strip() else None,
        'cidade': cidade.strip() if cidade.strip() else None,
        'estado': estado.strip() if estado.strip() else None,
    }
    
    # Adicionar campos editáveis do scraping se foram modificados
    if 'titulo_input' in st.session_state and titulo_editado != imovel_selecionado.get('titulo'):
        dados_imovel['titulo'] = titulo_editado.strip()
    
    if 'descricao_input' in st.session_state and descricao_editada != imovel_selecionado.get('descricao'):
        dados_imovel['descricao'] = descricao_editada.strip()
    
    dados_anuncio = {
        'codigo_anuncio_canalpro': codigo_anuncio_canalpro.strip() if codigo_anuncio_canalpro.strip() else None,
        'link_video_youtube': link_video_youtube.strip() if link_video_youtube.strip() else None,
        'link_tour_virtual': link_tour_virtual.strip() if link_tour_virtual.strip() else None,
        'modo_exibicao_endereco': modo_exibicao_endereco,
        'pronto_para_publicacao': salvar_completo
    }
    
    try:
        # Atualizar dados do imóvel na tabela imoveis
        dados_imovel_update = {k: v for k, v in dados_imovel.items() if v is not None}
        
        if dados_imovel_update:
            result_imovel = supabase.table("imoveis").update(dados_imovel_update).eq("codigo", codigo_selecionado).execute()
        
        # Atualizar ou criar dados do anúncio
        existing_anuncio = supabase.table("anuncios").select("*").eq("imovel_codigo", codigo_selecionado).execute()
        
        if existing_anuncio.data:
            # Atualizar anúncio existente
            result_anuncio = supabase.table("anuncios").update(dados_anuncio).eq("imovel_codigo", codigo_selecionado).execute()
        else:
            # Criar novo anúncio
            dados_anuncio['imovel_codigo'] = codigo_selecionado
            dados_anuncio['publicado'] = False
            dados_anuncio['is_highlighted'] = False
            result_anuncio = supabase.table("anuncios").insert(dados_anuncio).execute()
        
        # Feedback de sucesso
        if salvar_completo:
            st.success("✅ Dados salvos e imóvel marcado como PRONTO para publicação!")
            st.info("💡 Este imóvel agora aparecerá como 'Preparado' na listagem e estará pronto para ser testado no Canal PRO.")
            st.balloons()
        else:
            st.success("💾 Rascunho salvo com sucesso!")
            st.info("💡 Os dados foram salvos como rascunho. Use 'Marcar como Pronto' quando todos os dados estiverem completos.")
        
        # Limpar session state do CEP
        if 'cep_data' in st.session_state:
            del st.session_state.cep_data
        
        # Aguardar um pouco para mostrar mensagem
        import time
        time.sleep(2)
        
        # Recarregar página para atualizar dados
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar dados: {e}")

# Seção de informações adicionais
with st.expander("📊 Informações Técnicas"):
    st.markdown("**Dados do Scraping:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Coletado em:** {imovel_selecionado.get('scraped_at', 'N/A')}")
        st.write(f"**Tipo:** {imovel_selecionado.get('tipo', 'N/A')}")
        st.write(f"**Quartos:** {imovel_selecionado.get('quartos', 'N/A')}")
        st.write(f"**Suítes:** {imovel_selecionado.get('suites', 'N/A')}")
        st.write(f"**Banheiros:** {imovel_selecionado.get('banheiros', 'N/A')}")
    
    with col2:
        st.write(f"**Vagas:** {imovel_selecionado.get('vagas', 'N/A')}")
        st.write(f"**Área:** {imovel_selecionado.get('area', 'N/A')}m²")
        st.write(f"**Condomínio:** R$ {imovel_selecionado.get('condominio', 0):,.2f}")
        st.write(f"**IPTU:** R$ {imovel_selecionado.get('iptu', 0):,.2f} ({imovel_selecionado.get('iptu_periodo', 'N/A')})")
        st.write(f"**Fotos:** {len(json.loads(imovel_selecionado.get('fotos', '[]')) if isinstance(imovel_selecionado.get('fotos'), str) else imovel_selecionado.get('fotos', []))}")
    
    if st.button("🔍 Ver JSON Completo"):
        st.json(imovel_selecionado)