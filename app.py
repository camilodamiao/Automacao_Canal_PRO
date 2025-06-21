# app.py
"""
Sistema de Publicação Canal PRO
Interface principal com Streamlit
"""

import streamlit as st
from pathlib import Path
import sys

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

# Configuração da página
st.set_page_config(
    page_title="Canal PRO Publisher",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("🏠 Canal PRO Publisher")
st.markdown("Sistema de publicação automatizada de imóveis")

# Sidebar
with st.sidebar:
    st.header("Menu")
    st.markdown("""
    ### Páginas disponíveis:
    - **📝 Publicar**: Publicar novo anúncio
    - **📊 Dashboard**: Ver anúncios publicados
    - **⚙️ Configurações**: Gerenciar códigos
    """)
    
    # Status do sistema
    st.markdown("---")
    st.header("Status do Sistema")
    
    # Verificar conexões
    try:
        from src.utils.database import check_connection
        if check_connection():
            st.success("✅ Conectado ao Supabase")
        else:
            st.error("❌ Erro na conexão")
    except:
        st.warning("⚠️ Verificando conexão...")

# Conteúdo principal
st.markdown("## Bem-vindo!")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Imóveis no Banco",
        value="0",
        delta="0 novos hoje"
    )

with col2:
    st.metric(
        label="Códigos Disponíveis",
        value="34",
        delta="-1 usado hoje"
    )

with col3:
    st.metric(
        label="Publicados Hoje",
        value="0",
        delta="0%"
    )

# Instruções
st.markdown("---")
st.markdown("""
### 🚀 Como usar:

1. **Faça o scraping** de um imóvel no GINTERVALE
2. **Vá para a página Publicar** no menu lateral
3. **Complete os dados** necessários
4. **Publique** no Canal PRO

### 📋 Requisitos mínimos:
- ✅ Preço definido
- ✅ Mínimo 3 fotos
- ✅ Endereço completo
- ✅ Código do corretor disponível
""")

# Footer
st.markdown("---")
st.caption("Desenvolvido com ❤️ para automatizar publicações imobiliárias")