import re
import pdfplumber
import pandas as pd
import warnings


warnings.simplefilter("default")

def extrair_texto_pdf(caminho_pdf):
    """Converte o PDF para texto bruto usando pdfplumber."""
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages):
            conteudo = pagina.extract_text()
            if conteudo:
                texto += conteudo + "\n"
    return texto

def extrair_dados_fgts(texto):
    """
    Extrai os dados de cada empregado com base em padrões visuais do PDF.
    Os campos extraídos são: Matricula, Empregado, Admissao, CPF, Base FGTS, Valor FGTS.
    """
    padrao_linha_empregado = re.compile(
        r"(\\d{1,4})\\s+([A-Z \\u00C0-\\u00DA]+?)\\s+(\\d{2}/\\d{2}/\\d{4})Adm:(\\d{3}\\.\\d{3}\\.\\d{3}\\-\\d{2})",
        re.UNICODE
    )

    padrao_valores = re.compile(
        r"Base FGTS:\s*([\d\.,]+)\s+Valor FGTS:\s*([\d\.,]+)", re.UNICODE
    )

    linhas = texto.splitlines()
    registros = []
    buffer_empregado = None

    for i, linha in enumerate(linhas):
        if "Trabalhando CPF:Situação:Empr.:" in linha:
            print(f"[DEBUG] Linha empregado: {linha}")
            match_emp = padrao_linha_empregado.search(linha)
            if match_emp:
                matricula, nome, admissao, cpf = match_emp.groups()
                buffer_empregado = [
                    matricula.strip(),
                    nome.title().strip(),
                    admissao.strip(),
                    cpf.strip()
                ]
                print(f"[DEBUG] Encontrado empregado: {buffer_empregado}")
        elif "Base FGTS:" in linha and buffer_empregado:
            print(f"[DEBUG] Linha valores: {linha}")
            match_fgts = padrao_valores.search(linha)
            if match_fgts:
                base_fgts, valor_fgts = match_fgts.groups()
                buffer_empregado.extend([
                    base_fgts.replace(".", "").replace(",", "."),
                    valor_fgts.replace(".", "").replace(",", ".")
                ])
                registros.append(buffer_empregado)
                print(f"[DEBUG] Registro completo adicionado: {buffer_empregado}")
                buffer_empregado = None

    print(f"[DEBUG] Total de registros extraídos: {len(registros)}")
    return registros

def gerar_planilha_fgts(dados, caminho_saida):
    """Gera planilha Excel com os dados extraídos."""
    df = pd.DataFrame(dados, columns=[
        "Matricula", "Empregado", "Admissao", "CPF", "Base FGTS", "Valor FGTS"
    ])
    df.to_excel(caminho_saida, index=False)

def processar_fgts_pdf(caminho_pdf, caminho_saida_planilha):
    texto = extrair_texto_pdf(caminho_pdf)
    dados = extrair_dados_fgts(texto)
    gerar_planilha_fgts(dados, caminho_saida_planilha)
    return dados
