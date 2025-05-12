import pdfplumber
import re
import json
import os
import webbrowser
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from tkinter import *
from tkinter import ttk, filedialog, messagebox

dados_extraidos = []

def extrair_dados_fgts_pdfplumber(caminho_pdf):
    dados_por_competencia = {}
    competencia_atual = None
    buffer = None

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue

            match_comp = re.search(r"(?i)\bcompet[êe]ncia\:? ?(\d{2}/\d{4})", texto)
            if match_comp:
                competencia_atual = match_comp.group(1)

            if not competencia_atual:
                continue

            linhas = texto.splitlines()
            for linha in linhas:
                linha = linha.strip()

                match_emp = re.search(
                    r"Empr\.\:\s*(\d+)([A-Z\sÇÁÉÍÓÚÃÕÂÊÔ]+)Situação\:\s*\w+\s+CPF\:\s*([\d\.\-]+)\s+Adm\:\s*(\d{2}/\d{4}|\d{2}/\d{2}/\d{4})",
                    linha
                )

                if match_emp:
                    matricula, nome, cpf, adm = match_emp.groups()
                    nome = re.sub(r"\s+", " ", nome.strip()).title()
                    buffer = {
                        "Matricula": matricula,
                        "Empregado": nome,
                        "CPF": cpf,
                        "Admissao": adm,
                        "Base FGTS": None,
                        "Valor FGTS": None
                    }

                # Tenta capturar Base FGTS e Valor FGTS em qualquer linha
                if "Base FGTS:" in linha and "Valor FGTS:" in linha and buffer:
                    match_fgts = re.search(
                        r"Base FGTS:\s*([\d\.,]+).*?Valor FGTS:\s*([\d\.,]+)",
                        linha
                    )
                    if match_fgts:
                        base_fgts, valor_fgts = match_fgts.groups()
                        buffer["Base FGTS"] = base_fgts.replace(".", "").replace(",", ".")
                        buffer["Valor FGTS"] = valor_fgts.replace(".", "").replace(",", ".")
                        dados_por_competencia.setdefault(competencia_atual, []).append(buffer)
                        buffer = None  # reset para próximo empregado

    return dados_por_competencia

def atualizar_visualizacao(registros_por_competencia):
    global dados_extraidos
    dados_extraidos = registros_por_competencia
    text_widget.delete(1.0, END)
    text_widget.insert(END, json.dumps(registros_por_competencia, indent=4, ensure_ascii=False))
    status_var.set(f"{sum(len(v) for v in registros_por_competencia.values())} registros distribuídos em {len(registros_por_competencia)} competências.")

def processar_arquivo(caminho):
    registros = extrair_dados_fgts_pdfplumber(caminho)
    atualizar_visualizacao(registros)

def processar_pasta():
    pasta = filedialog.askdirectory()
    if not pasta:
        return
    registros_por_competencia = {}

    for arquivo in os.listdir(pasta):
        if arquivo.lower().endswith(".pdf"):
            caminho_completo = os.path.join(pasta, arquivo)
            dados_pdf = extrair_dados_fgts_pdfplumber(caminho_completo)

            for competencia, registros in dados_pdf.items():
                registros_por_competencia.setdefault(competencia, []).extend(registros)

    atualizar_visualizacao(registros_por_competencia)

def escolher_pdf():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos PDF", "*.pdf")])
    if caminho:
        processar_arquivo(caminho)

def salvar_planilha_formatada():
    if not dados_extraidos:
        messagebox.showwarning("Aviso", "Nenhum dado foi extraído para salvar.")
        return

    caminho_saida = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Planilhas Excel", "*.xlsx")],
        title="Salvar planilha formatada"
    )
    if not caminho_saida:
        return

    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        competencias_ordenadas = sorted(
            dados_extraidos.keys(),
            key=lambda x: pd.to_datetime(f"01/{x}", dayfirst=True)
        )

        for competencia in competencias_ordenadas:
            registros = dados_extraidos[competencia]
            dados_formatados = []
            for item in registros:
                item_copia = item.copy()
                try:
                    item_copia["Base FGTS"] = f"{float(item_copia['Base FGTS']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    item_copia["Valor FGTS"] = f"{float(item_copia['Valor FGTS']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except (ValueError, TypeError):
                    item_copia["Base FGTS"] = item_copia.get("Base FGTS", "")
                    item_copia["Valor FGTS"] = item_copia.get("Valor FGTS", "")
                dados_formatados.append(item_copia)

            df = pd.DataFrame(dados_formatados, columns=["Matricula", "Empregado", "CPF", "Admissao", "Base FGTS", "Valor FGTS"])
            aba_nome = competencia.replace("/", "_")
            df.to_excel(writer, sheet_name=aba_nome, index=False)

    wb = load_workbook(caminho_saida)
    fonte_arial = Font(name='Arial', size=10)
    for aba in wb.worksheets:
        for row in aba.iter_rows(min_row=2):
            for i, cell in enumerate(row):
                cell.font = fonte_arial
                if i == 0:
                    cell.number_format = "@"
                if i in (4, 5):
                    cell.number_format = '#.##0,00'
                else:
                    cell.number_format = "@"
    wb.save(caminho_saida)

    if messagebox.askyesno("Planilha salva", "Deseja abrir a planilha agora?"):
        webbrowser.open(f"file://{os.path.abspath(caminho_saida)}")

root = Tk()
root.title("Extrator de FGTS de PDFs - Assertivus")
root.geometry("1100x700")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10, "bold"))

frame_botoes = ttk.LabelFrame(root, text="Ações")
frame_botoes.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

btn_pdf = ttk.Button(frame_botoes, text="Selecionar PDF Único", command=escolher_pdf)
btn_pdf.grid(row=0, column=0, padx=5, pady=5)

btn_pasta = ttk.Button(frame_botoes, text="Selecionar Pasta de PDFs", command=processar_pasta)
btn_pasta.grid(row=0, column=1, padx=5, pady=5)

btn_salvar = ttk.Button(frame_botoes, text="Gerar Planilha Formatada", command=salvar_planilha_formatada)
btn_salvar.grid(row=0, column=2, padx=5, pady=5)

frame_texto = Frame(root)
frame_texto.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

scrollbar = Scrollbar(frame_texto)
scrollbar.pack(side=RIGHT, fill=Y)

text_widget = Text(frame_texto, wrap="word", yscrollcommand=scrollbar.set, font=("Courier New", 10))
text_widget.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.config(command=text_widget.yview)

status_var = StringVar()
status_var.set("Nenhum dado carregado.")
status_bar = Label(root, textvariable=status_var, bd=1, relief=SUNKEN, anchor="w")
status_bar.grid(row=2, column=0, sticky="ew")

root.mainloop()
