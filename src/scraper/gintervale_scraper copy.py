#!/usr/bin/env python3
"""
Scraper Gintervale - Versão Limpa
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
        # Caminho da imagem
        path = f"images/{codigo}/{idx:03d}.jpg"
        
        # Verificar se já existe
        existing = supabase.storage.from_(SUPA_BUCKET).list(f"images/{codigo}/")
        if any(f['name'] == f"{idx:03d}.jpg" for f in existing):
            # Se já existe, retornar a URL
            return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
        
        # Se não existe, fazer download e upload
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        result = supabase.storage.from_(SUPA_BUCKET).upload(path, response.content)
        
        if isinstance(result, dict) and result.get("error"):
            # Se o erro for de duplicação, retornar a URL mesmo assim
            if "Duplicate" in str(result.get("error", "")):
                return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
            print(f"  ❌ Erro upload imagem {idx}: {result['error']}")
            return None
            
        return f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
    except Exception as e:
        print(f"  ❌ Erro imagem {idx}: {e}")
        return None


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
    
    # Processar fotos
    fotos = []
    imgs = await page.locator("div.fotos_imovel img.swiper_slide_img").all()
    
    print(f"📸 Processando {len(imgs)} fotos...")
    
    # Tentar pegar fotos existentes se já estiverem no storage
    for i in range(1, len(imgs) + 1):
        path = f"images/{codigo}/{i:03d}.jpg"
        url = f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{path}"
        fotos.append(url)
    
    # Se não tiver fotos no array, tentar fazer upload
    if not fotos or len([f for f in fotos if f]) == 0:
        fotos = []
        for i, img in enumerate(imgs, 1):
            src = await img.get_attribute("data-src") or await img.get_attribute("src")
            if src and src.startswith("http"):
                url = upload_image(src, codigo, i)
                if url:
                    fotos.append(url)
    
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
        "fotos": fotos,
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
            print(f"  - Fotos: {len(dados['fotos'])}")
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            await page.screenshot(path=f"erro_{codigo}.png")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())