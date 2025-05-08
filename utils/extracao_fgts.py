import re
import fitz 
import pandas as pd

def extrair_texto_pdf(caminho_pdf):
    texto = ""
    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def extrair_dados_fgts(texto):
    padrao_empregado = re.compile(
        r"Empr\.:\s*(\d+)\s+(.*?)\s+Situação:\s*Trabalhando\s+CPF:\s*([\d\.\-]+)\s+Adm:\s*(\d{2}/\d{2}/\d{4})"
    )

    padrao_fgts = re.compile(
        r"Base FGTS:\s*([\d\.,]+)\s+Valor FGTS:\s*([\d\.,]+)"
    )

    linhas = texto.splitlines()
    registros = []

    for i in range(len(linhas) - 1):
        match_emp = padrao_empregado.search(linhas[i])
        match_fgts = padrao_fgts.search(linhas[i + 1])

        if match_emp and match_fgts:
            matricula, nome, cpf, admissao = match_emp.groups()
            base_fgts, valor_fgts = match_fgts.groups()

            registros.append([
                matricula.strip(),
                nome.strip(),
                admissao.strip(),
                cpf.strip(),
                base_fgts.replace(".", "").replace(",", "."),
                valor_fgts.replace(".", "").replace(",", ".")
            ])

    return registros

def gerar_planilha_fgts(dados, caminho_saida):
    df = pd.DataFrame(dados, columns=[
        "Matricula", "Empregado", "Admissao", "CPF", "Base FGTS", "Valor FGTS"
    ])
    df.to_excel(caminho_saida, index=False)

def processar_fgts_pdf(caminho_pdf, caminho_saida_planilha):
    texto = extrair_texto_pdf(caminho_pdf)
    dados = extrair_dados_fgts(texto)
    gerar_planilha_fgts(dados, caminho_saida_planilha)
    return dados
