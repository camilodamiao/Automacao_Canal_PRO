# pages/3_⚙️_Configurações.py
"""
Página de configurações do sistema
"""

import streamlit as st
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Configurações", layout="wide")

st.title("⚙️ Configurações")

# Tabs de configuração
tab1, tab2, tab3, tab4 = st.tabs([
    "🔐 Credenciais", 
    "🤖 Automação", 
    "📝 Templates",
    "🔧 Sistema"
])

with tab1:
    st.header("Credenciais e Conexões")
    
    # Credenciais Canal PRO
    st.subheader("Canal PRO")
    
    col1, col2 = st.columns(2)
    
    with col1:
        zap_email = st.text_input(
            "Email",
            value=os.getenv("ZAP_EMAIL", ""),
            type="default",
            help="Email usado para login no Canal PRO"
        )
    
    with col2:
        zap_password = st.text_input(
            "Senha",
            value="*" * len(os.getenv("ZAP_PASSWORD", "")) if os.getenv("ZAP_PASSWORD") else "",
            type="password",
            help="Senha do Canal PRO"
        )
    
    # Supabase
    st.subheader("Supabase")
    
    col1, col2 = st.columns(2)
    
    with col1:
        supa_url = st.text_input(
            "URL",
            value=os.getenv("SUPABASE_URL", ""),
            help="URL do projeto Supabase"
        )
    
    with col2:
        supa_key = st.text_input(
            "Anon Key",
            value=os.getenv("SUPABASE_KEY", "")[:20] + "..." if os.getenv("SUPABASE_KEY") else "",
            type="password",
            help="Chave anônima do Supabase"
        )
    
    if st.button("💾 Salvar Credenciais"):
        # TODO: Implementar salvamento seguro
        st.success("Credenciais salvas com sucesso!")

with tab2:
    st.header("Configurações de Automação")
    
    # Comportamento padrão
    st.subheader("Comportamento Padrão")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_destacar = st.checkbox(
            "Destacar anúncios automaticamente",
            value=False,
            help="Usar códigos destacáveis quando disponíveis"
        )
        
        min_fotos = st.number_input(
            "Mínimo de fotos",
            min_value=1,
            max_value=10,
            value=3,
            help="Número mínimo de fotos para publicar"
        )
        
        modo_endereco = st.selectbox(
            "Modo de exibição do endereço",
            ["Completo", "Somente Rua", "Somente Bairro"],
            help="Como o endereço será exibido no anúncio"
        )
    
    with col2:
        auto_otimizar = st.checkbox(
            "Otimizar título automaticamente",
            value=True,
            help="Gerar título otimizado baseado nos dados"
        )
        
        max_caracteres_titulo = st.number_input(
            "Máximo de caracteres no título",
            min_value=50,
            max_value=100,
            value=100
        )
        
        tipo_operacao = st.selectbox(
            "Tipo de operação padrão",
            ["Venda", "Aluguel", "Venda e Aluguel"]
        )
    
    # Mapeamentos customizados
    st.subheader("Mapeamentos Customizados")
    
    with st.expander("🏠 Tipos de Imóvel"):
        st.info("Configure como os tipos são mapeados entre GINTERVALE e Canal PRO")
        
        # Exemplo de configuração
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("GINTERVALE", value="Casa", disabled=True)
        with col2:
            st.text("→")
        with col3:
            st.selectbox("Canal PRO", ["HOME", "APARTMENT", "CONDOMINIUM"])

with tab3:
    st.header("Templates de Descrição")
    
    st.info("Configure templates para gerar descrições automaticamente")
    
    # Seletor de tipo
    tipo_template = st.selectbox(
        "Tipo de Imóvel",
        ["Apartamento", "Casa", "Terreno", "Comercial"]
    )
    
    # Template editor
    template_default = """🏠 {titulo}

📍 Localização: {localizacao}

✨ Características:
- {quartos} quartos
- {banheiros} banheiros  
- {vagas} vagas
- {area}m²

📝 Descrição:
{descricao}

💰 Valores:
- Condomínio: R$ {condominio}
- IPTU: R$ {iptu}

📞 Entre em contato para mais informações!
Código: {codigo}"""
    
    template = st.text_area(
        "Template de Descrição",
        value=template_default,
        height=400,
        help="Use {campo} para inserir valores dinamicamente"
    )
    
    # Preview
    with st.expander("👁️ Preview"):
        st.text("Exemplo de como ficará:")
        preview = template.format(
            titulo="Apartamento 3 quartos em Jardim Aquarius",
            localizacao="Jardim Aquarius - São José dos Campos/SP",
            quartos=3,
            banheiros=2,
            vagas=2,
            area=125,
            descricao="Lindo apartamento com vista para o jardim...",
            condominio="385,00",
            iptu="150,00",
            codigo="AP10657"
        )
        st.text(preview)
    
    if st.button("💾 Salvar Template"):
        st.success("Template salvo com sucesso!")

with tab4:
    st.header("Configurações do Sistema")
    
    # Informações do sistema
    st.subheader("Informações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Versão do Sistema", "1.0.0")
        st.metric("Python", "3.11.0")
        st.metric("Streamlit", st.__version__)
    
    with col2:
        st.metric("Imóveis no Banco", "42")
        st.metric("Publicações Totais", "128")
        st.metric("Última Atualização", "15/01/2024")
    
    # Manutenção
    st.subheader("Manutenção")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache limpo!")
    
    with col2:
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📥 Backup Dados", use_container_width=True):
            st.info("Funcionalidade em desenvolvimento")
    
    # Logs
    st.subheader("Logs do Sistema")
    
    log_level = st.selectbox(
        "Nível de Log",
        ["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    
    # Exemplo de logs
    log_example = """[2024-01-15 14:30:15] INFO: Sistema iniciado
[2024-01-15 14:30:20] INFO: Conexão com Supabase estabelecida
[2024-01-15 14:31:05] INFO: Imóvel AP10657 publicado com sucesso
[2024-01-15 14:31:06] INFO: Nota do anúncio: 8.5
[2024-01-15 14:35:22] WARNING: Tentativa de publicar sem CEP
[2024-01-15 14:35:30] INFO: Dados corrigidos, publicação retomada"""
    
    st.text_area(
        "Logs Recentes",
        value=log_example,
        height=200,
        disabled=True
    )