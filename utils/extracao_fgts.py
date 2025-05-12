import re

def extrair_dados_fgts_mensal(texto):
    print("[DEBUG] Iniciando extração dos dados FGTS (modelo mensal)")

    padrao_fgts = re.compile(r"Base FGTS:\s*([\d\.,]+)\s+Valor FGTS:\s*([\d\.,]+)")

    linhas = texto.splitlines()
    print(f"[DEBUG] Total de linhas encontradas: {len(linhas)}")

    registros = []
    buffer = None

    for i in range(len(linhas) - 4):
        l0 = linhas[i].strip()
        l1 = linhas[i + 1].strip()
        l2 = linhas[i + 2].strip()
        l3 = linhas[i + 3].strip()
        l4 = linhas[i + 4].strip()

        # Identifica início de bloco com 'Empr.:'
        if l0.startswith("Empr.:") and l1.isdigit():
            matricula = l1
            nome = l2.title()
            
            # Confirma se há CPF e Admissão nos próximos blocos
            adm = None
            cpf = None

            for j in range(i, i + 6):
                linha = linhas[j].strip()
                if linha.startswith("Adm:"):
                    adm = linha.replace("Adm:", "").strip()
                if linha.startswith("CPF:"):
                    cpf = linha.replace("CPF:", "").strip()

            if not adm or not cpf:
                print(f"[DEBUG] ⚠️ Dados incompletos em bloco de {nome}")
                continue

            buffer = [matricula, nome, adm, cpf]

        # Se buffer preenchido, procurar linha de FGTS
        if buffer:
            linha = linhas[i].strip()
            match_fgts = padrao_fgts.search(linha)
            if match_fgts:
                base_fgts, valor_fgts = match_fgts.groups()
                buffer.append(base_fgts.replace(".", "").replace(",", "."))
                buffer.append(valor_fgts.replace(".", "").replace(",", "."))
                registros.append(buffer)
                print(f"[DEBUG] ✅ Registro completo: {buffer}")
                buffer = None

    print(f"[DEBUG] Total de registros extraídos: {len(registros)}")
    return registros

def validar_dados_fgts(dados):
    print(f"[DEBUG] Validando {len(dados)} registros extraídos...")
    for dado in dados:
        if len(dado) != 6:
            raise ValueError(f"Dados incompletos encontrados: {dado}")
    print("[DEBUG] Todos os dados foram validados com sucesso")
    return dados
