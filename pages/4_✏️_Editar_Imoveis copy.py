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
import subprocess
import tempfile
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

def executar_teste_canal_pro(dados_completos):
    """Executa teste usando subprocess separado - VERSÃO FINAL"""
    try:
        # Validar dados essenciais
        if not dados_completos:
            st.error("❌ Dados não fornecidos para o teste")
            return False
        
        # Adicionar fotos aos dados (importante!)
        imovel_selecionado = st.session_state.get('imovel_selecionado', {})
        if imovel_selecionado and imovel_selecionado.get('fotos'):
            # Processar fotos
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
            
            dados_completos['fotos'] = fotos
        
        # Criar arquivo temporário com os dados
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(dados_completos, temp_file, ensure_ascii=False, indent=2)
            temp_path = temp_file.name
            print(f"🔍 DEBUG: Arquivo JSON criado em: {temp_path}")
            print(f"🔍 DEBUG: Fotos incluídas: {'fotos' in dados_completos}")
            if 'fotos' in dados_completos:
                print(f"🔍 DEBUG: Quantidade de fotos: {len(dados_completos.get('fotos', []))}")
           
        
        # Caminho do script executor
        script_executor = Path(__file__).parent.parent / "src" / "automation" / "canal_pro_test_executor.py"
        
        # Verificar se o script existe
        if not script_executor.exists():
            st.error(f"❌ Script executor não encontrado em: {script_executor}")
            st.info("💡 Certifique-se de que o arquivo 'canal_pro_test_executor.py' está em 'src/automation/'")
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
                if "Login confirmado" in result.stdout:
                    st.success("🔐 **Login realizado com sucesso!**")
                if "fotos enviadas" in result.stdout:
                    st.success("📸 **Fotos carregadas com sucesso!**")
                
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

# Salvar imóvel selecionado no session state para uso no teste
st.session_state['imovel_selecionado'] = imovel_selecionado

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

# Processar clique no botão "Testar Canal PRO"
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
        
        # Executar o teste
        sucesso = executar_teste_canal_pro(dados_completos)
        
        if sucesso:
            st.success("✅ Teste do Canal PRO concluído com sucesso!")
            st.balloons()
        else:
            st.error("❌ O teste encontrou problemas. Verifique os logs acima.")
    else:
        st.error("❌ Complete todos os campos obrigatórios antes de testar no Canal PRO.")
        campos_faltando = [campo for campo, completo in campos_obrigatorios.items() if not completo]
        st.info(f"💡 Campos faltando: {', '.join(campos_faltando)}")

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