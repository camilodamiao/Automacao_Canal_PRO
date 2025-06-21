# pages/2_📊_Dashboard.py
"""
Dashboard com estatísticas e histórico
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from src.utils.database import get_supabase_client, CODIGOS_CORRETOR

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("📊 Dashboard - Canal PRO Publisher")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Estatísticas", "📋 Códigos do Corretor", "📜 Histórico"])

with tab1:
    st.header("Estatísticas Gerais")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    # Buscar dados reais (simulados por enquanto)
    with col1:
        st.metric(
            "Total de Imóveis",
            "42",
            "+5 esta semana"
        )
    
    with col2:
        st.metric(
            "Publicados",
            "8",
            "+2 hoje"
        )
    
    with col3:
        st.metric(
            "Taxa de Sucesso",
            "95%",
            "+5%"
        )
    
    with col4:
        st.metric(
            "Nota Média",
            "8.7",
            "+0.3"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Publicações por Dia")
        
        # Dados simulados
        dates = pd.date_range(end=datetime.now(), periods=30)
        df_publicacoes = pd.DataFrame({
            'Data': dates,
            'Publicações': [2, 1, 3, 0, 2, 1, 4] * 4 + [2, 3]
        })
        
        fig = px.line(df_publicacoes, x='Data', y='Publicações',
                     title="Últimos 30 dias")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏠 Tipos de Imóveis")
        
        # Dados simulados
        df_tipos = pd.DataFrame({
            'Tipo': ['Apartamento', 'Casa', 'Terreno', 'Comercial'],
            'Quantidade': [25, 12, 3, 2]
        })
        
        fig = px.pie(df_tipos, values='Quantidade', names='Tipo',
                    title="Distribuição por Tipo")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("📋 Gestão de Códigos do Corretor")
    
    # Estatísticas dos códigos
    col1, col2, col3 = st.columns(3)
    
    codigos_em_uso = len([c for c in CODIGOS_CORRETOR if c['em_uso']])
    codigos_livres = len(CODIGOS_CORRETOR) - codigos_em_uso
    
    with col1:
        st.metric("Total de Códigos", len(CODIGOS_CORRETOR))
    
    with col2:
        st.metric("Em Uso", codigos_em_uso)
    
    with col3:
        st.metric("Disponíveis", codigos_livres)
    
    st.markdown("---")
    
    # Tabela de códigos
    st.subheader("Lista de Códigos")
    
    # Converter para DataFrame
    df_codigos = pd.DataFrame(CODIGOS_CORRETOR)
    
    # Filtros
    col1, col2 = st.columns([1, 3])
    
    with col1:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos", "Em uso", "Disponíveis"]
        )
    
    # Aplicar filtro
    if filtro_status == "Em uso":
        df_filtered = df_codigos[df_codigos['em_uso'] == True]
    elif filtro_status == "Disponíveis":
        df_filtered = df_codigos[df_codigos['em_uso'] == False]
    else:
        df_filtered = df_codigos
    
    # Exibir tabela
    st.dataframe(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "codigo": "Código",
            "data_anuncio": "Data do Anúncio",
            "destacado": "Destacado",
            "em_uso": st.column_config.CheckboxColumn("Em Uso")
        }
    )
    
    # Adicionar novo código
    with st.expander("➕ Adicionar Novo Código"):
        col1, col2 = st.columns(2)
        
        with col1:
            novo_codigo = st.text_input("Código")
        
        with col2:
            tipo_codigo = st.selectbox("Tipo", ["Normal", "Destacável"])
        
        if st.button("Adicionar Código"):
            st.success(f"Código {novo_codigo} adicionado!")
            # TODO: Implementar adição real

with tab3:
    st.header("📜 Histórico de Publicações")
    
    # Filtros de data
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        data_inicio = st.date_input(
            "De",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col2:
        data_fim = st.date_input(
            "Até",
            value=datetime.now()
        )
    
    # Dados simulados de histórico
    historico_data = [
        {
            "Data": "2024-01-15 14:30",
            "Código Imóvel": "AP10657",
            "Título": "Apartamento 3 quartos, 125m²",
            "Código Corretor": "HA00011",
            "Nota": 8.5,
            "Status": "✅ Publicado"
        },
        {
            "Data": "2024-01-15 10:15",
            "Código Imóvel": "CA12203",
            "Título": "Casa em condomínio, 200m²",
            "Código Corretor": "HA00012",
            "Nota": 9.2,
            "Status": "✅ Publicado"
        },
        {
            "Data": "2024-01-14 16:45",
            "Código Imóvel": "AP11074",
            "Título": "Apartamento 2 quartos",
            "Código Corretor": "HA00013",
            "Nota": 7.8,
            "Status": "✅ Publicado"
        }
    ]
    
    df_historico = pd.DataFrame(historico_data)
    
    # Exibir tabela
    st.dataframe(
        df_historico,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nota": st.column_config.NumberColumn(
                "Nota",
                format="%.1f",
                min_value=0,
                max_value=10
            )
        }
    )
    
    # Exportar dados
    col1, col2 = st.columns([3, 1])
    
    with col2:
        csv = df_historico.to_csv(index=False)
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"historico_publicacoes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )