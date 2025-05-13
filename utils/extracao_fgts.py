import re
from utils.extrator import extrair_dados_fgts_pdfplumber

def extrair_dados_fgts_mensal(texto):
    print("[DEBUG] Iniciando extração dos dados FGTS (modelo mensal)")
    registros = []

    blocos = re.split(r"\n(?=Empr\.\:\s*\d+)", texto)

    for bloco in blocos:
        if not re.search(r"^Empr\.\:", bloco.strip()):
            continue

        match_matricula = re.search(r"Empr\.\:\s*(\d+)", bloco)
        match_nome = re.search(r"Empr\.\:\s*\d+\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÇÑ\s\-\.]+?)(?=\s+Situação|\s+CPF)", bloco)
        match_cpf = re.search(r"CPF\:\s*([\d\.\-]+)", bloco)
        match_adm = re.search(r"Adm\:\s*(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}/\d{4})", bloco)
        
        match_base = re.search(r"Base\s*FGTS\:?\s*([\d\.,]+)", bloco)
        match_valor = re.search(r"Valor\s*FGTS\:?\s*([\d\.,]+)", bloco)
        
        if match_matricula and match_nome and match_cpf and match_adm and match_base and match_valor:
            matricula = match_matricula.group(1)
            nome = match_nome.group(1).strip().title()
            cpf = match_cpf.group(1)
            admissao = match_adm.group(1)
            base_fgts = match_base.group(1).replace(".", "").replace(",", ".")
            valor_fgts = match_valor.group(1).replace(".", "").replace(",", ".")
            
            registros.append([
                matricula.strip(),
                nome,
                admissao.strip(),
                cpf.strip(),
                base_fgts, 
                valor_fgts
            ])
    
    print(f"[DEBUG] Total de registros extraídos: {len(registros)}")
    return registros

def validar_dados_fgts(dados):
    """Valida os dados extraídos do FGTS"""
    print(f"[DEBUG] Validando {len(dados)} registros extraídos...")
    dados_validos = []
    
    for dado in dados:
        if len(dado) != 6:
            print(f"[AVISO] Registro com formato inválido: {dado}")
            continue
            
        try:
            _ = float(dado[4])
            _ = float(dado[5])
            dados_validos.append(dado)
        except ValueError:
            print(f"[AVISO] Valores de FGTS inválidos: Base={dado[4]}, Valor={dado[5]}")
            continue
            
    print(f"[DEBUG] {len(dados_validos)} registros válidos após validação")
    return dados_validos