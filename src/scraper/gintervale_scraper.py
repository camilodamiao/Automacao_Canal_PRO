#!/usr/bin/env python3
"""
Scraper Gintervale - Versão Corrigida
Extrai dados de imóveis e salva no Supabase
"""

import os
import sys
import re
import asyncio
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from supabase import create_client

# Configuração
load_dotenv('config/.env')
SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_KEY")
SUPA_BUCKET = os.getenv("SUPABASE_BUCKET")

if not all([SUPA_URL, SUPA_KEY, SUPA_BUCKET]):
    print("❌ Configure SUPABASE_URL, SUPABASE_KEY e SUPABASE_BUCKET no .env")
    sys.exit(1)

supabase = create_client(SUPA_URL, SUPA_KEY)


def upload_image(url, codigo, idx):
    """Baixa e envia imagem para o Supabase Storage"""
    try:
        print(f"  📸 Processando foto {idx}: {url[:50]}...")
        
        # Caminho da imagem
        path = f"images/{codigo}/{idx:03d}.jpg"
        
        # Verificar se já existe no storage
        try:
            existing = supabase.storage.from_(SUPA_BUCKET).list(f"images/{codigo}/")
            if existing and any(f.get('name') == f"{idx:03d}.jpg" for f in existing):
                print(f"  ✅ Foto {idx} já existe no storage")
                return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
        except Exception as list_error:
            print(f"  ⚠️ Erro ao verificar existência da foto {idx}: {list_error}")
        
        # Fazer download da imagem
        print(f"  ⬇️ Baixando foto {idx}...")
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        if len(response.content) < 1000:  # Imagem muito pequena, provavelmente erro
            print(f"  ❌ Foto {idx} muito pequena ({len(response.content)} bytes)")
            return None
        
        # Upload para o Supabase Storage
        print(f"  ⬆️ Fazendo upload da foto {idx}...")
        result = supabase.storage.from_(SUPA_BUCKET).upload(path, response.content)
        
        if hasattr(result, 'error') and result.error:
            # Se o erro for de duplicação, retornar a URL mesmo assim
            if "Duplicate" in str(result.error) or "already exists" in str(result.error):
                print(f"  ✅ Foto {idx} já existia, usando URL existente")
                return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
            print(f"  ❌ Erro upload foto {idx}: {result.error}")
            return None
        
        print(f"  ✅ Foto {idx} salva com sucesso!")
        return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erro ao baixar foto {idx}: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Erro geral foto {idx}: {e}")
        return None


def create_or_update_anuncio(codigo):
    """Cria ou atualiza registro na tabela anuncios"""
    try:
        # Verificar se já existe anúncio para este imóvel
        existing = supabase.table("anuncios").select("id").eq("imovel_codigo", codigo).execute()
        
        if existing.data:
            print(f"  📢 Anúncio para {codigo} já existe - mantendo configurações")
            return True
        else:
            # Criar novo registro em branco (SEM pronto_para_publicacao para ficar como "Novo")
            anuncio_data = {
                "imovel_codigo": codigo,
                "publicado": False,
                "is_highlighted": False,
                "canalpro_id": None,
                "codigo_anuncio_canalpro": None,
                "link_video_youtube": "https://www.youtube.com/watch?v=lk-sj2ZDLDU",
                "link_tour_virtual": "https://www.tourvirtual360.com.br/ibd/",
                "modo_exibicao_endereco": "completo"
                # NÃO incluir pronto_para_publicacao aqui para aparecer como "Novo"
            }
            
            result = supabase.table("anuncios").insert(anuncio_data).execute()
            
            if result.data:
                print(f"  📢 Registro de anúncio criado para {codigo} (status: Novo)")
                return True
            else:
                print(f"  ❌ Erro ao criar anúncio: {result}")
                return False
                
    except Exception as e:
        print(f"  ❌ Erro ao gerenciar anúncio: {e}")
        return False


async def scrape_imovel(page, codigo):
    """Extrai dados do imóvel da página"""
    # Fechar popup de cookies se existir
    try:
        await page.click('button:has-text("Prosseguir")', timeout=2000)
    except:
        pass
    
    # Aguardar página carregar
    await page.wait_for_selector("h1.titulo", timeout=10000)
    
    # Extrair dados básicos
    titulo = await page.locator("h1.titulo").inner_text()
    localizacao = await page.locator("h2.localizacao span").inner_text()
    
    # Descrição (pode não existir)
    try:
        descricao = await page.locator("div.descricao_imovel div.texto").inner_text()
    except:
        descricao = ""
    
    # Detectar tipo do imóvel
    tipo = "Apartamento"
    if "casa" in titulo.lower():
        tipo = "Casa"
    elif "terreno" in titulo.lower():
        tipo = "Terreno"
    
    # Extrair PREÇO
    preco = None
    try:
        preco_elem = await page.locator("div.valor:has(h3:text('Venda')) h4").inner_text()
        preco_str = preco_elem.replace("R$", "").replace(".", "").replace(",", ".").strip()
        preco = float(preco_str)
    except:
        pass
    
    # Extrair CONDOMÍNIO
    condominio = None
    try:
        cond_elem = await page.locator("div.valor:has(small:text('Condomínio')) span").inner_text()
        cond_str = cond_elem.replace("R$", "").replace(".", "").replace(",", ".").strip()
        condominio = float(cond_str)
    except:
        pass
    
    # Extrair IPTU
    iptu = None
    iptu_periodo = None
    try:
        # Procurar div que contém IPTU
        iptu_div = page.locator("div.valor:has(small:text('IPTU'))")
        if await iptu_div.count() > 0:
            # Pegar o texto do valor
            iptu_elem = await iptu_div.locator("span").inner_text()
            iptu_str = iptu_elem.replace("R$", "").replace(".", "").replace(",", ".").strip()
            iptu = float(iptu_str)
            
            # Verificar se tem período (Mensal/Anual)
            iptu_text = await iptu_div.inner_text()
            if "Mensal" in iptu_text:
                iptu_periodo = "Mensal"
            elif "Anual" in iptu_text:
                iptu_periodo = "Anual"
    except:
        pass
    
    # Extrair DETALHES (quartos, suites, banheiros, vagas, área)
    quartos = suites = banheiros = vagas = area = None
    try:
        # Aguardar div.detalhes carregar
        await page.wait_for_selector("div.detalhes", timeout=5000)
        
        # Pegar apenas os primeiros detalhes (do imóvel principal)
        # Geralmente são os primeiros 7-8 elementos antes de repetir
        detalhes_elements = await page.locator("div.detalhe").all()
        
        # Processar apenas até encontrar todos os dados ou máximo 8 elementos
        dados_encontrados = set()
        
        for i, detalhe in enumerate(detalhes_elements[:8]):  # Limitar aos primeiros 8
            texto = await detalhe.inner_text()
            
            # Quartos/Dormitórios (pegar apenas o primeiro)
            if "dormitório" in texto and "quartos" not in dados_encontrados:
                match = re.search(r'(\d+)', texto)
                if match:
                    quartos = int(match.group(1))
                    dados_encontrados.add("quartos")
            
            # Suítes (exemplo: "sendo 2 suítes")
            elif "suíte" in texto and "suites" not in dados_encontrados:
                match = re.search(r'(\d+)', texto)
                if match:
                    suites = int(match.group(1))
                    dados_encontrados.add("suites")
            
            # Banheiros
            elif "banheiro" in texto and "banheiros" not in dados_encontrados:
                # Só pegar se não for suíte
                if "suíte" not in texto:
                    match = re.search(r'(\d+)', texto)
                    if match:
                        banheiros = int(match.group(1))
                        dados_encontrados.add("banheiros")
            
            # Vagas (pegar apenas o primeiro)
            elif ("vaga" in texto or "garagem" in texto) and "vagas" not in dados_encontrados:
                match = re.search(r'(\d+)\s*(?:vaga|vagas|garagem)', texto)
                if match:
                    vagas = int(match.group(1))
                    dados_encontrados.add("vagas")
            
            # Área
            elif "m²" in texto and "area" not in dados_encontrados:
                # Priorizar área útil
                if "útil" in texto:
                    match = re.search(r'([\d,]+)\s*m²', texto)
                    if match:
                        area = float(match.group(1).replace(",", "."))
                        dados_encontrados.add("area")
                # Se não achou área ainda, pegar total
                elif not area and "total" in texto:
                    match = re.search(r'([\d,]+)\s*m²', texto)
                    if match:
                        area = float(match.group(1).replace(",", "."))
                        dados_encontrados.add("area")
        
    except Exception as e:
        print(f"  ⚠️ Erro ao extrair detalhes: {e}")
    
    # Extrair cidade/estado
    cidade = estado = None
    if "-" in localizacao and "/" in localizacao:
        parts = localizacao.split("-")[-1].strip()
        if "/" in parts:
            cidade, estado = [p.strip() for p in parts.split("/")]
    
    # CORREÇÃO PRINCIPAL: Processar fotos adequadamente
    fotos = []
    imgs = await page.locator("div.fotos_imovel img.swiper_slide_img").all()
    
    print(f"📸 Encontradas {len(imgs)} fotos para processar...")
    
    # Fazer upload real de cada foto
    fotos_sucesso = 0
    for i, img in enumerate(imgs, 1):
        try:
            src = await img.get_attribute("data-src") or await img.get_attribute("src")
            if src and src.startswith("http"):
                url_final = upload_image(src, codigo, i)
                if url_final:
                    fotos.append(url_final)
                    fotos_sucesso += 1
                else:
                    print(f"  ⚠️ Falha no upload da foto {i}")
            else:
                print(f"  ⚠️ Foto {i} sem URL válida: {src}")
        except Exception as e:
            print(f"  ❌ Erro ao processar foto {i}: {e}")
    
    print(f"✅ {fotos_sucesso}/{len(imgs)} fotos salvas com sucesso!")
    
    # Montar dados
    return {
        "codigo": codigo,
        "titulo": titulo,
        "tipo": tipo,
        "preco": preco,
        "condominio": condominio,
        "iptu": iptu,
        "iptu_periodo": iptu_periodo,
        "area": area,
        "quartos": quartos,
        "suites": suites,
        "banheiros": banheiros,
        "vagas": vagas,
        "descricao": descricao,
        "localizacao": localizacao,
        "cidade": cidade,
        "estado": estado,
        "fotos": fotos,  # Array de URLs já validadas
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        # Campos para preencher manualmente
        "endereco": None,
        "bairro": None,
        "cep": None,
        "numero": None,
        "complemento": None,
    }


async def main():
    if len(sys.argv) != 2:
        print("Uso: python gintervale_scraper.py <CODIGO>")
        print("Exemplo: python gintervale_scraper.py AP10657")
        sys.exit(1)
    
    codigo = sys.argv[1].upper()
    url = f"https://gintervale.com.br/imoveis/referencia-{codigo}/"
    
    print(f"\n🏠 Scraping imóvel: {codigo}")
    print(f"🌐 URL: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Acessar página de listagem
            await page.goto(url)
            await page.wait_for_selector("#lista", timeout=10000)
            
            # Clicar no imóvel (abre nova aba)
            async with page.context.expect_page() as new_page_info:
                await page.click("#lista a[target='_blank']")
            new_page = await new_page_info.value
            
            await new_page.wait_for_load_state("domcontentloaded")
            await new_page.wait_for_timeout(2000)
            
            # Extrair dados
            print("📝 Extraindo dados...")
            dados = await scrape_imovel(new_page, codigo)
            
            # Salvar no Supabase
            print("💾 Salvando no banco...")
            
            # Verificar se já existe
            existing = supabase.table("imoveis").select("codigo").eq("codigo", codigo).execute()
            
            if existing.data:
                result = supabase.table("imoveis").update(dados).eq("codigo", codigo).execute()
                print("✅ Imóvel atualizado!")
            else:
                result = supabase.table("imoveis").insert(dados).execute()
                print("✅ Imóvel cadastrado!")
            
            # Criar registro na tabela anuncios
            print("📢 Gerenciando registro de anúncio...")
            create_or_update_anuncio(codigo)
            
            # Resumo
            print(f"\n📊 Resumo:")
            print(f"  - Tipo: {dados['tipo']}")
            print(f"  - Preço: R$ {dados['preco']:,.2f}" if dados['preco'] else "  - Preço: não informado")
            print(f"  - Condomínio: R$ {dados['condominio']:,.2f}" if dados['condominio'] else "  - Condomínio: não informado")
            print(f"  - IPTU: R$ {dados['iptu']:,.2f} ({dados['iptu_periodo']})" if dados['iptu'] else "  - IPTU: não informado")
            print(f"  - Área: {dados['area']}m²" if dados['area'] else "  - Área: não informada")
            print(f"  - Quartos: {dados['quartos']}" if dados['quartos'] else "  - Quartos: não informado")
            print(f"  - Suítes: {dados['suites']}" if dados['suites'] else "  - Suítes: não informado")
            print(f"  - Banheiros: {dados['banheiros']}" if dados['banheiros'] else "  - Banheiros: não informado")
            print(f"  - Vagas: {dados['vagas']}" if dados['vagas'] else "  - Vagas: não informado")
            print(f"  - Cidade: {dados['cidade']}/{dados['estado']}" if dados['cidade'] else "  - Cidade: não identificada")
            print(f"  - Fotos salvas: {len(dados['fotos'])}")
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            await page.screenshot(path=f"erro_{codigo}.png")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())