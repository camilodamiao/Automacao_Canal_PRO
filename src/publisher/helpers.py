# src/publisher/helpers.py
"""
Funções auxiliares para o publicador
"""

# Mapeamento de tipos de imóvel
TIPO_IMOVEL_MAP = {
    "Apartamento": {
        "type": "APARTMENT",
        "subtipos_possiveis": ["Padrão", "Duplex", "Triplex", "Cobertura"]
    },
    "Casa": {
        "type": "HOME", 
        "subtipos_possiveis": ["Padrão", "Casa de condomínio", "Casa de vila"]
    },
    "Terreno": {
        "type": "ALLOTMENT_LAND",
        "subtipos_possiveis": ["Padrão"]
    }
}

# Mapeamento de subtipos para valores do Canal PRO
SUBTIPO_MAP = {
    "Padrão": "CategoryNONE",
    "Duplex": "DUPLEX",
    "Triplex": "TRIPLEX",
    "Cobertura": "PENTHOUSE",
    "Casa de condomínio": "CONDOMINIUM",
    "Casa de vila": "VILLAGE_HOUSE"
}

def detectar_subtipo(titulo: str, descricao: str) -> str:
    """Detecta o subtipo do imóvel baseado no título e descrição"""
    texto = f"{titulo} {descricao}".lower()
    
    if "duplex" in texto:
        return "Duplex"
    elif "triplex" in texto:
        return "Triplex"
    elif "cobertura" in texto:
        return "Cobertura"
    elif "condomínio" in texto or "condominio" in texto:
        return "Casa de condomínio"
    elif "vila" in texto:
        return "Casa de vila"
    
    return "Padrão"

def validar_dados(dados: dict) -> dict:
    """Valida se todos os dados obrigatórios estão preenchidos"""
    campos_obrigatorios = {
        'preco': 'Preço',
        'cep': 'CEP',
        'endereco': 'Endereço',
        'numero': 'Número',
        'bairro': 'Bairro',
        'cidade': 'Cidade',
        'estado': 'Estado',
        'codigo_corretor': 'Código do Corretor'
    }
    
    campos_faltando = []
    
    for campo, nome in campos_obrigatorios.items():
        if not dados.get(campo):
            campos_faltando.append(nome)
    
    # Verificar fotos
    if len(dados.get('fotos', [])) < 3:
        campos_faltando.append('Mínimo 3 fotos')
    
    return {
        'valido': len(campos_faltando) == 0,
        'campos_faltando': campos_faltando
    }

def formatar_preco(valor: float) -> str:
    """Formata valor para exibição"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_titulo_anuncio(dados: dict) -> str:
    """Gera título otimizado para o anúncio"""
    tipo = dados.get('tipo', 'Imóvel')
    quartos = dados.get('quartos', 0)
    area = dados.get('area', 0)
    bairro = dados.get('bairro', '')
    
    partes = [tipo]
    
    if quartos:
        partes.append(f"{quartos} quartos")
    
    if area:
        partes.append(f"{int(area)}m²")
    
    if bairro:
        partes.append(f"- {bairro}")
    
    return " ".join(partes)[:100]