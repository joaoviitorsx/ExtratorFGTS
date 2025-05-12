import pdfplumber

def extrair_texto_pdf(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages):
            conteudo = pagina.extract_text()
            if conteudo:
                texto += conteudo + "\n"
    return texto

def identificar_layout_pdf(texto):
    if "Base FGTS:" in texto:
        return "FGTS"
    elif "Empr.:" in texto:
        return "Folha Mensal"
    else:
        return "Desconhecido"
