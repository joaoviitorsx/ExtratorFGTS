import fitz

def extrair_texto_pdf(caminho_pdf):
    print(f"[DEBUG] Iniciando extração de texto com PyMuPDF: {caminho_pdf}")
    texto = ""
    with fitz.open(caminho_pdf) as doc:
        for i, page in enumerate(doc):
            pagina_texto = page.get_text()
            print(f"[DEBUG] Página {i+1} extraída com {len(pagina_texto)} caracteres")
            texto += pagina_texto + "\n"
    print(f"[DEBUG] Extração finalizada com {len(texto)} caracteres no total")
    return texto