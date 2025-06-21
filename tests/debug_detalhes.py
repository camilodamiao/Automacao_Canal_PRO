#!/usr/bin/env python3
"""
Debug para analisar a estrutura dos detalhes do imóvel
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_detalhes():
    codigo = input("Digite o código do imóvel (ex: AP10657): ").strip()
    url = f"https://gintervale.com.br/imoveis/referencia-{codigo}/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url)
        await page.wait_for_timeout(2000)
        
        # Fechar cookies
        try:
            await page.click('button:has-text("Prosseguir")')
        except:
            pass
        
        # Clicar no imóvel
        async with page.context.expect_page() as new_page_info:
            await page.click("#lista a[target='_blank']")
        new_page = await new_page_info.value
        
        await new_page.wait_for_timeout(3000)
        
        print("\n" + "="*60)
        print("ANÁLISE DOS DETALHES DO IMÓVEL")
        print("="*60 + "\n")
        
        # 1. Estrutura HTML completa
        try:
            detalhes_html = await new_page.locator("div.detalhes").inner_html()
            print("HTML COMPLETO DOS DETALHES:")
            print(detalhes_html)
            print("\n" + "-"*60 + "\n")
        except:
            print("❌ Não encontrou div.detalhes")
            
        # 2. Cada detalhe individualmente
        try:
            detalhes = await new_page.locator("div.detalhe").all()
            print(f"TOTAL DE DETALHES ENCONTRADOS: {len(detalhes)}\n")
            
            for i, detalhe in enumerate(detalhes, 1):
                texto = await detalhe.inner_text()
                html = await detalhe.inner_html()
                
                print(f"DETALHE {i}:")
                print(f"Texto: {texto}")
                print(f"HTML: {html}")
                
                # Tentar identificar o ícone
                try:
                    icon_class = await detalhe.locator("i.icon").get_attribute("class")
                    print(f"Ícone: {icon_class}")
                except:
                    print("Ícone: não encontrado")
                
                print("-"*40)
                
        except Exception as e:
            print(f"❌ Erro ao analisar detalhes: {e}")
        
        # 3. Screenshot destacando os detalhes
        await new_page.evaluate("""
            document.querySelectorAll('div.detalhe').forEach((el, i) => {
                el.style.border = '2px solid red';
                el.style.margin = '5px';
                el.style.backgroundColor = `hsl(${i * 30}, 100%, 95%)`;
            });
        """)
        
        await new_page.screenshot(path=f"debug_detalhes_{codigo}.png")
        print(f"\n📸 Screenshot salva: debug_detalhes_{codigo}.png")
        
        input("\nPressione ENTER para fechar...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_detalhes())