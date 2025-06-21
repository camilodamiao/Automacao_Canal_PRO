# src/utils/database.py
"""
Funções de acesso ao banco de dados
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv('config/.env')

SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
supabase = create_client(SUPA_URL, SUPA_KEY)

# Lista dos seus códigos
CODIGOS_CORRETOR = [
    # Ativos
    {"codigo": "AP11007", "data_anuncio": "17/05/2025", "destacado": "SIM", "em_uso": True},
    {"codigo": "AP10157", "data_anuncio": "17/05/2025", "destacado": "SIM", "em_uso": True},
    {"codigo": "AP11074", "data_anuncio": "17/05/2025", "destacado": "SIM", "em_uso": True},
    {"codigo": "AP09970", "data_anuncio": "17/05/2025", "destacado": "NAO", "em_uso": True},
    {"codigo": "AP10522", "data_anuncio": "17/05/2025", "destacado": "SIM", "em_uso": True},
    {"codigo": "CA12203", "data_anuncio": "14/06/2025", "destacado": "SIM", "em_uso": True},
    # Disponíveis
    {"codigo": "HA00011", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00012", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00013", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00014", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00015", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00016", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00017", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00018", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00020", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00021", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00022", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00023", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00024", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00025", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00026", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00040", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00041", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00042", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00043", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00044", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00045", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00046", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00047", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00048", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00049", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00050", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00051", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00052", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00053", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00054", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00055", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00056", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00057", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "HA00058", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "PT01537", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "PT01478", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "PT01479", "data_anuncio": None, "destacado": None, "em_uso": False},
    {"codigo": "PT01480", "data_anuncio": None, "destacado": None, "em_uso": False},
]

def get_supabase_client():
    """Retorna cliente Supabase"""
    if not SUPA_URL or not SUPA_KEY:
        raise Exception("Configurar SUPABASE_URL e SUPABASE_KEY no .env")
    return create_client(SUPA_URL, SUPA_KEY)

def check_connection():
    """Verifica conexão com Supabase"""
    try:
        client = get_supabase_client()
        # Tenta fazer uma query simples
        result = client.table("imoveis").select("codigo").limit(1).execute()
        return True
    except:
        return False

def get_imoveis_nao_publicados():
    """Busca imóveis que ainda não foram publicados no Canal PRO"""
    try:
        client = get_supabase_client()
        result = client.table("anuncios").select("*").is_("publicado", "null").execute()
        return result.data
    except Exception as e:
        print(f"Erro ao buscar imóveis: {e}")
        return []

def get_codigos_disponiveis():
    """Retorna lista de códigos de corretor disponíveis"""
    # Por enquanto, usar lista estática
    # TODO: Migrar para tabela no Supabase
    return [c for c in CODIGOS_CORRETOR if not c['em_uso']]

def marcar_codigo_usado(codigo: str, imovel_codigo: str):
    """Marca um código como usado"""
    # TODO: Implementar no Supabase
    for c in CODIGOS_CORRETOR:
        if c['codigo'] == codigo:
            c['em_uso'] = True
            c['imovel_associado'] = imovel_codigo
            c['data_uso'] = datetime.now()
            break

def salvar_publicacao(dados_publicacao: dict):
    """Salva os dados da publicação no banco"""
    try:
        client = get_supabase_client()
        
        # Atualizar tabela de imóveis
        update_data = {
            'canal_pro_codigo_corretor': dados_publicacao['codigo_corretor'],
            'canal_pro_publicado_em': datetime.now().isoformat(),
            'canal_pro_anuncio_id': dados_publicacao.get('anuncio_id'),
            'canal_pro_nota_anuncio': dados_publicacao.get('nota'),
            'canal_pro_destacado': dados_publicacao.get('destacado', False)
        }
        
        result = client.table("imoveis").update(update_data).eq(
            "codigo", dados_publicacao['codigo_imovel']
        ).execute()
        
        # Marcar código como usado
        marcar_codigo_usado(
            dados_publicacao['codigo_corretor'],
            dados_publicacao['codigo_imovel']
        )
        
        return True
    except Exception as e:
        print(f"Erro ao salvar publicação: {e}")
        return False

def get_estatisticas():
    """Retorna estatísticas do sistema"""
    try:
        client = get_supabase_client()
        
        # Total de imóveis
        total = client.table("imoveis").select("codigo", count="exact").execute()
        
        # Publicados hoje
        hoje = datetime.now().date().isoformat()
        publicados_hoje = client.table("imoveis").select(
            "codigo", count="exact"
        ).gte("canal_pro_publicado_em", f"{hoje}T00:00:00").execute()
        
        # Códigos disponíveis
        codigos_livres = len(get_codigos_disponiveis())
        
        return {
            'total_imoveis': len(total.data) if total.data else 0,
            'publicados_hoje': len(publicados_hoje.data) if publicados_hoje.data else 0,
            'codigos_disponiveis': codigos_livres
        }
    except:
        return {
            'total_imoveis': 0,
            'publicados_hoje': 0,
            'codigos_disponiveis': len(get_codigos_disponiveis())
        }