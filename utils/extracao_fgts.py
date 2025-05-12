import re

def extrair_dados_fgts_mensal(texto):
    padrao_empregado = re.compile(
        r"Empr\.\:\s*(\d+)\s+([A-Z\s]+)\s+Situação\:\s*\w+\s+CPF\:\s*([\d\.\-]+)\s+Adm\:\s*(\d{2}/\d{2}/\d{4})"
    )
    padrao_fgts = re.compile(
        r"Base FGTS:\s*([\d\.,]+)\s+Valor FGTS:\s*([\d\.,]+)"
    )

    linhas = texto.splitlines()
    registros = []
    buffer = None

    for linha in linhas:
        match_emp = padrao_empregado.search(linha)
        if match_emp:
            matricula, nome, cpf, admissao = match_emp.groups()
            buffer = [matricula.strip(), nome.title().strip(), admissao.strip(), cpf.strip()]
            continue

        if buffer:
            match_fgts = padrao_fgts.search(linha)
            if match_fgts:
                base_fgts, valor_fgts = match_fgts.groups()
                buffer += [
                    base_fgts.replace(".", "").replace(",", "."),
                    valor_fgts.replace(".", "").replace(",", ".")
                ]
                registros.append(buffer)
                buffer = None

    return registros

def validar_dados_fgts(dados):
    for dado in dados:
        if len(dado) != 6:
            raise ValueError(f"Dados incompletos encontrados: {dado}")
    return dados
