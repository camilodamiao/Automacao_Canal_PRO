#!/usr/bin/env python3
"""
TESTE ISOLADO - Apenas receber URLs e baixar fotos
Não faz login, não abre browser, apenas baixa as fotos
"""

import sys
import json
import os
import requests
from datetime import datetime
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def criar_pasta_downloads():
    """Cria pasta para salvar as fotos baixadas"""
    # Criar pasta na área de trabalho ou no diretório do projeto
    if sys.platform.startswith('win'):
        desktop = Path.home() / "Desktop" / "teste_fotos_canal_pro"
    else:
        desktop = Path.home() / "teste_fotos_canal_pro"
    
    # Adicionar timestamp para não sobrescrever
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta = desktop / timestamp
    pasta.mkdir(parents=True, exist_ok=True)
    
    return pasta

def baixar_fotos(urls_fotos, pasta_destino):
    """Baixa as fotos e salva na pasta especificada"""
    print(f"\n📥 INICIANDO DOWNLOAD DE {len(urls_fotos)} FOTOS")
    print(f"📁 Salvando em: {pasta_destino}")
    print("-" * 60)
    
    fotos_baixadas = []
    
    for i, url in enumerate(urls_fotos, 1):
        print(f"\n🔄 Foto {i}/{len(urls_fotos)}:")
        print(f"   URL: {url}")
        
        try:
            # Baixar
            print("   ⬇️  Baixando...", end="", flush=True)
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Verificar tamanho
            tamanho = len(response.content)
            print(f" OK! ({tamanho:,} bytes)")
            
            if tamanho < 1000:
                print("   ❌ Arquivo muito pequeno, pulando...")
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
                ext = '.jpg'  # padrão
            
            # Salvar
            nome_arquivo = f"foto_{i:03d}{ext}"
            caminho_completo = pasta_destino / nome_arquivo
            
            with open(caminho_completo, 'wb') as f:
                f.write(response.content)
            
            print(f"   💾 Salvo como: {nome_arquivo}")
            
            # Verificar
            if caminho_completo.exists():
                file_size = caminho_completo.stat().st_size
                print(f"   ✅ Verificado: {file_size:,} bytes")
                fotos_baixadas.append(str(caminho_completo))
            else:
                print("   ❌ Erro: arquivo não foi criado!")
                
        except requests.exceptions.RequestException as e:
            print(f" ERRO!")
            print(f"   ❌ Erro de rede: {type(e).__name__}")
            print(f"   💡 Detalhes: {str(e)}")
        except Exception as e:
            print(f" ERRO!")
            print(f"   ❌ Erro geral: {type(e).__name__}")
            print(f"   💡 Detalhes: {str(e)}")
    
    return fotos_baixadas

def main():
    print("="*60)
    print("🧪 TESTE DE DOWNLOAD DE FOTOS - CANAL PRO")
    print("="*60)
    
    # Verificar argumentos
    if len(sys.argv) != 2:
        print("\n❌ Erro: arquivo de dados não fornecido!")
        print("Uso: python test_download_fotos_only.py <arquivo_dados.json>")
        sys.exit(1)
    
    arquivo_dados = sys.argv[1]
    print(f"\n📄 Lendo dados de: {arquivo_dados}")
    
    try:
        # Ler dados
        with open(arquivo_dados, 'r', encoding='utf-8') as f:
            dados_completos = json.load(f)
        
        print(f"✅ Dados carregados: {len(dados_completos)} campos")
        
        # Verificar se tem fotos
        fotos = dados_completos.get('fotos', [])
        
        if not fotos:
            print("\n❌ NENHUMA FOTO ENCONTRADA NOS DADOS!")
            print("\n🔍 Campos disponíveis nos dados:")
            for campo in sorted(dados_completos.keys()):
                valor = dados_completos[campo]
                if isinstance(valor, (list, dict)):
                    print(f"   - {campo}: {type(valor).__name__} com {len(valor)} items")
                elif isinstance(valor, str) and len(valor) > 50:
                    print(f"   - {campo}: {valor[:50]}...")
                else:
                    print(f"   - {campo}: {valor}")
            sys.exit(1)
        
        # Mostrar informações das fotos
        print(f"\n📸 FOTOS ENCONTRADAS: {len(fotos)}")
        
        if isinstance(fotos, list):
            print("✅ Formato: Lista de URLs")
            for i, url in enumerate(fotos[:3], 1):  # Mostrar apenas as 3 primeiras
                print(f"   {i}. {url[:80]}...")
            if len(fotos) > 3:
                print(f"   ... e mais {len(fotos) - 3} fotos")
        else:
            print(f"❌ Formato inesperado: {type(fotos)}")
            print(f"   Conteúdo: {str(fotos)[:200]}...")
            sys.exit(1)
        
        # Criar pasta para downloads
        pasta_downloads = criar_pasta_downloads()
        
        # Baixar fotos
        fotos_baixadas = baixar_fotos(fotos, pasta_downloads)
        
        # Resumo
        print("\n" + "="*60)
        print(f"📊 RESUMO DO TESTE:")
        print(f"   - Fotos recebidas: {len(fotos)}")
        print(f"   - Fotos baixadas: {len(fotos_baixadas)}")
        print(f"   - Pasta de destino: {pasta_downloads}")
        
        if fotos_baixadas:
            print(f"\n✅ SUCESSO! {len(fotos_baixadas)} fotos baixadas")
            
            # Abrir pasta no Windows
            if sys.platform.startswith('win'):
                print(f"\n📂 Abrindo pasta com as fotos...")
                os.startfile(pasta_downloads)
            
            print("\n💡 As fotos foram salvas permanentemente em:")
            print(f"   {pasta_downloads}")
            print("\n🔍 Verifique se as fotos estão corretas antes de prosseguir!")
        else:
            print("\n❌ FALHA! Nenhuma foto foi baixada")
            print("\n💡 Possíveis causas:")
            print("   - URLs inválidas ou expiradas")
            print("   - Problema de conexão")
            print("   - Bucket do Supabase privado")
        
        # Salvar log
        log_file = pasta_downloads / "download_log.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Teste de Download - {datetime.now()}\n")
            f.write(f"Fotos recebidas: {len(fotos)}\n")
            f.write(f"Fotos baixadas: {len(fotos_baixadas)}\n\n")
            f.write("URLs recebidas:\n")
            for i, url in enumerate(fotos, 1):
                f.write(f"{i}. {url}\n")
        
        print(f"\n📝 Log salvo em: {log_file}")
        
    except FileNotFoundError:
        print(f"\n❌ Arquivo não encontrado: {arquivo_dados}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ Erro ao ler JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {type(e).__name__}")
        print(f"   Detalhes: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()