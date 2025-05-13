import pdfplumber
import re
import warnings
import json
import os

def extrair_dados_fgts_pdfplumber(caminho_pdf, progress_callback=None):
    warnings.filterwarnings('ignore')
    dados_por_competencia = {}
    competencia_atual = None
    
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            total_paginas = len(pdf.pages)
            
            if progress_callback:
                progress_callback(0, total_paginas)
                
            for i, pagina in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_paginas)
                    
                texto = pagina.extract_text()
                if not texto:
                    continue

                match_comp = re.search(r"(?i)\bcompet[êeéè]ncia\:?\s*(\d{2}/\d{4})", texto)
                if match_comp:
                    competencia_atual = match_comp.group(1)

                if not competencia_atual:
                    continue

                blocos = re.split(r"\n(?=Empr\.\:\s*\d+)", texto)

                for bloco in blocos:
                    if not re.search(r"^Empr\.\:", bloco.strip()):
                        continue
                    
                    match_dados = re.search(
                        r"Empr\.\:\s*(\d+)\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÇÑ\s\-\.]+?)"  
                        r"\s+Situação\:\s*\w+\s+CPF\:\s*([\d\.\-]+)"            
                        r".*?Adm\:\s*(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}/\d{4})",
                        bloco, 
                        flags=re.DOTALL
                    )
                    
                    if not match_dados:
                        match_dados = re.search(
                            r"Empr\.\:\s*(\d+)\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÇÑ\s\-\.]+?)"
                            r"(?=\s+Situação:|\s+CPF:)"                          
                            r".*?CPF\:\s*([\d\.\-]+)"                           
                            r".*?Adm\:\s*(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}/\d{4})",
                            bloco, 
                            flags=re.DOTALL
                        )
                    
                    if not match_dados:
                        match_matricula = re.search(r"Empr\.\:\s*(\d+)", bloco)
                        match_cpf = re.search(r"CPF\:\s*([\d\.\-]+)", bloco)
                        match_adm = re.search(r"Adm\:\s*(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}/\d{4})", bloco)
                        
                        if match_matricula and match_cpf and match_adm:
                            inicio_texto = bloco[match_matricula.end():]
                            match_fim = re.search(r"\s+(?:Situação|CPF)\:", inicio_texto)
                            
                            if match_fim:
                                nome = inicio_texto[:match_fim.start()].strip()
                                class MockMatch:
                                    def groups(self):
                                        return (match_matricula.group(1), nome, 
                                                match_cpf.group(1), match_adm.group(1))
                                
                                match_dados = MockMatch()

                    if not match_dados:
                        continue

                    matricula, nome, cpf, admissao = match_dados.groups()
                    
                    nome = re.sub(r"\s+", " ", nome.strip())
                    nome = nome.title()
                    
                    match_fgts = re.search(
                        r"Base\s*FGTS\:?\s*([\d\.,]+)[\s\n]*Valor\s*FGTS\:?\s*([\d\.,]+)", 
                        bloco
                    )
                    
                    if not match_fgts:
                        match_fgts = re.search(
                            r"Base\s*FGTS\:?\s*([\d\.,]+).*?Valor\s*FGTS\:?\s*([\d\.,]+)",
                            bloco,
                            flags=re.DOTALL
                        )
                        
                    if not match_fgts:
                        linhas = bloco.split('\n')
                        for linha in linhas:
                            if "Base IRRF" in linha and "Base FGTS" in linha:
                                match_fgts = re.search(
                                    r"Base\s*FGTS\:?\s*([\d\.,]+).*?Valor\s*FGTS\:?\s*([\d\.,]+)",
                                    linha
                                )
                                if match_fgts:
                                    break
                                    
                    if not match_fgts:
                        match_base = re.search(r"Base\s*FGTS\:?\s*([\d\.,]+)", bloco)
                        match_valor = re.search(r"Valor\s*FGTS\:?\s*([\d\.,]+)", bloco)
                        
                        if match_base and match_valor:
                            class FGTSMatch:
                                def groups(self):
                                    return match_base.group(1), match_valor.group(1)
                            match_fgts = FGTSMatch()
                                    
                    if not match_fgts:
                        continue

                    base_fgts, valor_fgts = match_fgts.groups()
                    
                    try:
                        base_fgts_num = base_fgts.replace(".", "").replace(",", ".")
                        valor_fgts_num = valor_fgts.replace(".", "").replace(",", ".")
                        
                        _ = float(base_fgts_num)
                        _ = float(valor_fgts_num)
                    except ValueError:
                        continue

                    registro = {
                        "Matricula": matricula.strip(),
                        "Empregado": nome,
                        "CPF": cpf.strip(),
                        "Admissao": admissao.strip(),
                        "Base FGTS": base_fgts_num,
                        "Valor FGTS": valor_fgts_num
                    }

                    if all(registro.values()):
                        dados_por_competencia.setdefault(competencia_atual, []).append(registro)

        return dados_por_competencia
        
    except Exception as e:
        print(f"Erro ao processar o PDF: {str(e)}")
        return {}

def processar_pasta(caminho_pasta, progress_callback=None):
    registros_por_competencia = {}
    
    pdfs = [arquivo for arquivo in os.listdir(caminho_pasta) 
            if arquivo.lower().endswith(".pdf")]
    
    total_pdfs = len(pdfs)
    for i, arquivo in enumerate(pdfs):
        if progress_callback:
            progress_callback(i, total_pdfs, arquivo)
            
        caminho_completo = os.path.join(caminho_pasta, arquivo)
        
        def pdf_progress(pagina_atual, total_paginas):
            if progress_callback:
                progresso_arquivo = (i / total_pdfs) * 100
                progresso_pagina = (pagina_atual / total_paginas) * (1 / total_pdfs) * 100
                progress_callback(i, total_pdfs, arquivo, pagina_atual, total_paginas, 
                                  int(progresso_arquivo + progresso_pagina))
        
        dados_pdf = extrair_dados_fgts_pdfplumber(caminho_completo, pdf_progress)
        
        for competencia, registros in dados_pdf.items():
            registros_por_competencia.setdefault(competencia, []).extend(registros)
    
    return registros_por_competencia

def salvar_dados_json(registros_por_competencia, caminho_saida):
    """
    Salva os dados extraídos em formato JSON.
    
    Args:
        registros_por_competencia (dict): Dados organizados por competência
        caminho_saida (str): Caminho para salvar o arquivo JSON
    """
    try:
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(registros_por_competencia, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Erro ao salvar JSON: {str(e)}")
        return False