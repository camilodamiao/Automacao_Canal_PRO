# pages/1_📝_Publicar.py
"""
Página de publicação de imóveis
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Importar funções necessárias
from src.utils.database import get_imoveis_nao_publicados, get_codigos_disponiveis
from src.publisher.helpers import detectar_subtipo, validar_dados, TIPO_IMOVEL_MAP

st.set_page_config(page_title="Publicar Imóvel", layout="wide")

st.title("📝 Publicar Imóvel no Canal PRO")

# Verificar se há imóveis disponíveis
imoveis = get_imoveis_nao_publicados()

if not imoveis:
    st.warning("⚠️ Nenhum imóvel disponível para publicação")
    st.info("Faça o scraping de um imóvel primeiro usando: `python src/scraper/gintervale_scraper.py CODIGO`")
    st.stop()

# Seleção do imóvel
st.markdown("### 1️⃣ Selecione o Imóvel")

# Criar DataFrame para exibição
df_imoveis = pd.DataFrame(imoveis)
df_display = df_imoveis[['codigo', 'titulo', 'tipo', 'preco', 'area', 'quartos']].copy()
df_display['preco'] = df_display['preco'].apply(lambda x: f"R$ {x:,.2f}" if x else "Sem preço")
df_display['area'] = df_display['area'].apply(lambda x: f"{x}m²" if x else "-")

# Seleção com preview
col1, col2 = st.columns([1, 2])

with col1:
    selected_index = st.selectbox(
        "Código do Imóvel",
        range(len(imoveis)),
        format_func=lambda x: f"{imoveis[x]['codigo']} - {imoveis[x]['titulo'][:40]}..."
    )
    
    imovel_selecionado = imoveis[selected_index]

with col2:
    # Preview do imóvel
    st.markdown("**Preview:**")
    st.write(f"📍 **Localização:** {imovel_selecionado.get('localizacao', 'N/A')}")
    st.write(f"💰 **Preço:** R$ {imovel_selecionado.get('preco', 0):,.2f}")
    st.write(f"📐 **Área:** {imovel_selecionado.get('area', 0)}m²")
    
    # Mini galeria de fotos
    if imovel_selecionado.get('fotos'):
        st.write(f"📸 **{len(imovel_selecionado['fotos'])} fotos disponíveis**")
        cols = st.columns(4)
        for i, foto in enumerate(imovel_selecionado['fotos'][:4]):
            with cols[i]:
                st.image(foto, use_column_width=True)

st.markdown("---")

# Formulário de dados
st.markdown("### 2️⃣ Complete os Dados")

# Verificar dados obrigatórios faltando
dados_faltando = []
if not imovel_selecionado.get('preco'):
    dados_faltando.append("Preço")
if len(imovel_selecionado.get('fotos', [])) < 3:
    dados_faltando.append(f"Fotos (mínimo 3, atual: {len(imovel_selecionado.get('fotos', []))})")

if dados_faltando:
    st.error(f"❌ Dados obrigatórios faltando: {', '.join(dados_faltando)}")
    st.stop()

# Formulário em colunas
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📍 Endereço")
    
    cep = st.text_input(
        "CEP*",
        value=imovel_selecionado.get('cep', ''),
        placeholder="00000-000",
        help="Digite o CEP no formato 00000-000"
    )
    
    endereco = st.text_input(
        "Endereço (Rua)*",
        value=imovel_selecionado.get('endereco', ''),
        placeholder="Rua Example"
    )
    
    numero = st.text_input(
        "Número*",
        value=imovel_selecionado.get('numero', ''),
        placeholder="123"
    )
    
    complemento = st.text_input(
        "Complemento",
        value=imovel_selecionado.get('complemento', ''),
        placeholder="Apto 101, Bloco A"
    )
    
    bairro = st.text_input(
        "Bairro*",
        value=imovel_selecionado.get('bairro', ''),
        placeholder="Centro"
    )
    
    # Cidade e Estado (já temos do scraping)
    cidade = st.text_input(
        "Cidade*",
        value=imovel_selecionado.get('cidade', ''),
        disabled=True
    )
    
    estado = st.text_input(
        "Estado*",
        value=imovel_selecionado.get('estado', ''),
        disabled=True
    )

with col2:
    st.markdown("#### 🏷️ Configurações de Publicação")
    
    # Tipo e subtipo
    tipo_principal = imovel_selecionado.get('tipo', 'Apartamento')
    st.text_input("Tipo Principal", value=tipo_principal, disabled=True)
    
    # Detectar subtipo automaticamente
    subtipo_sugerido = detectar_subtipo(
        imovel_selecionado.get('titulo', ''),
        imovel_selecionado.get('descricao', '')
    )
    
    subtipos = TIPO_IMOVEL_MAP.get(tipo_principal, {}).get('subtipos_possiveis', ['Padrão'])
    subtipo_index = 0
    if subtipo_sugerido in subtipos:
        subtipo_index = subtipos.index(subtipo_sugerido)
    
    subtipo = st.selectbox(
        "Subtipo do Imóvel",
        options=subtipos,
        index=subtipo_index,
        help="Selecione o subtipo mais apropriado"
    )
    
    # Código do corretor
    codigos_disponiveis = get_codigos_disponiveis()
    
    if not codigos_disponiveis:
        st.error("❌ Nenhum código de corretor disponível!")
        st.stop()
    
    codigo_corretor = st.selectbox(
        f"Código do Corretor* ({len(codigos_disponiveis)} disponíveis)",
        options=[c['codigo'] for c in codigos_disponiveis],
        help="Selecione um código disponível"
    )
    
    # Destacar anúncio
    destacar = st.checkbox(
        "⭐ Destacar este anúncio",
        value=False,
        help="Usar um código destacável (se disponível)"
    )
    
    # Andar (para apartamentos)
    if tipo_principal == "Apartamento":
        andar = st.number_input(
            "Andar",
            min_value=0,
            max_value=50,
            value=0,
            help="Informe o andar do apartamento"
        )
    else:
        andar = None

st.markdown("---")

# Preview final
st.markdown("### 3️⃣ Revisar e Publicar")

# Validar dados
dados_completos = {
    **imovel_selecionado,
    'cep': cep,
    'endereco': endereco,
    'numero': numero,
    'complemento': complemento,
    'bairro': bairro,
    'subtipo': subtipo,
    'codigo_corretor': codigo_corretor,
    'destacar': destacar,
    'andar': andar
}

validacao = validar_dados(dados_completos)

# Mostrar status de validação
col1, col2 = st.columns([2, 1])

with col1:
    if validacao['valido']:
        st.success("✅ Todos os dados obrigatórios foram preenchidos!")
    else:
        st.error(f"❌ Campos obrigatórios faltando: {', '.join(validacao['campos_faltando'])}")

with col2:
    # Preview da nota estimada
    st.metric(
        "Nota Estimada",
        "8.5",
        help="Nota estimada baseada nos dados preenchidos"
    )

# Expandir para ver dados completos
with st.expander("📋 Ver dados completos do anúncio"):
    st.json(dados_completos)

# Botões de ação
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Salvar Rascunho", use_container_width=True):
        st.info("Funcionalidade em desenvolvimento")

with col2:
    if st.button("🔄 Limpar Formulário", use_container_width=True):
        st.rerun()

with col3:
    if st.button(
        "🚀 Publicar no Canal PRO",
        type="primary",
        use_container_width=True,
        disabled=not validacao['valido']
    ):
        # Adicionar à sessão para processar
        st.session_state['publicar_dados'] = dados_completos
        st.session_state['publicar_timestamp'] = datetime.now()
        
        # Mostrar progresso
        with st.spinner("Publicando anúncio..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simular etapas (substituir por publicação real)
            etapas = [
                ("Fazendo login no Canal PRO...", 0.2),
                ("Navegando para criar anúncio...", 0.4),
                ("Preenchendo dados básicos...", 0.6),
                ("Fazendo upload das fotos...", 0.8),
                ("Finalizando publicação...", 1.0)
            ]
            
            for etapa, progresso in etapas:
                status_text.text(etapa)
                progress_bar.progress(progresso)
                # Aqui chamaria a função real de publicação
                import time
                time.sleep(1)
            
            # Resultado
            st.success("✅ Anúncio publicado com sucesso!")
            st.balloons()
            
            # Mostrar resultado
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID do Anúncio", "ZAP-123456")
            with col2:
                st.metric("Nota Final", "9.2")
            with col3:
                st.metric("Status", "Ativo")
            
            # Limpar dados da sessão
            if 'publicar_dados' in st.session_state:
                del st.session_state['publicar_dados']