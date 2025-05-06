import os
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout, QFileDialog, QFrame, QMessageBox, QTableWidget, QTableWidgetItem, QSizePolicy
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap
from utils.icone import usar_icone, recurso_caminho
from ui.componentes import BotaoPrimario, BotaoSecundario


class WorkerThread(QThread):
    progress = Signal(int)
    finished = Signal(list, str)
    error = Signal(str)

    def __init__(self, caminho, is_pasta=False):
        super().__init__()
        self.caminho = caminho
        self.is_pasta = is_pasta

    def run(self):
        try:
            dados_totais = []
            nome_arquivo = ""
            if self.is_pasta:
                arquivos_pdf = [f for f in os.listdir(self.caminho) if f.lower().endswith('.pdf')]
                total_arquivos = len(arquivos_pdf)
                for idx, arquivo in enumerate(arquivos_pdf, 1):
                    caminho_completo = os.path.join(self.caminho, arquivo)
                    self.processar_arquivo(caminho_completo, dados_totais, arquivo)
                    progresso = int((idx / total_arquivos) * 100)
                    self.progress.emit(progresso)
            else:
                nome_arquivo = os.path.basename(self.caminho)
                self.processar_arquivo(self.caminho, dados_totais, nome_arquivo)
                self.progress.emit(100)
            self.finished.emit(dados_totais, nome_arquivo)
        except Exception as e:
            self.error.emit(str(e))

    def processar_arquivo(self, caminho, dados_totais, nome_arquivo):
        tipo_pdf = determinar_tipo_pdf(caminho)
        if tipo_pdf == "MATRIZ":
            linhas = extrair_transacoes_matriz(caminho)
        elif tipo_pdf == "FILIAL":
            linhas = extrair_transacoes_filial(caminho)
        else:
            return
        for linha in linhas:
            dados = filtrar_dados_transacao(linha)
            if dados:
                dados.append(nome_arquivo)
                dados_totais.append(dados)


class TelaExtracao(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extração de Dados - Assertivus Contábil")
        self.setGeometry(300, 100, 1200, 720)
        self.setStyleSheet("background-color: #181818; color: #ECECEC; font-family: 'Segoe UI';")
        self.dados_extraidos = []
        self.nome_arquivo = ""
        self.caminho_csv = None
        self.init_ui()
        usar_icone(self)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header = QFrame()
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.botao_voltar = BotaoSecundario("Voltar ao Dashboard", recurso_caminho("images/voltar.png"))
        self.botao_voltar.clicked.connect(self.voltar_dashboard)
        header_layout.addWidget(self.botao_voltar)
        header_layout.addStretch()
        main_layout.addWidget(header)

        logo_label = QLabel()
        pix = QPixmap(recurso_caminho("images/logo.png"))
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        titulo = QLabel("Conversor de PDF ALELO")
        titulo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(titulo)

        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(20)
        botoes_layout.setAlignment(Qt.AlignCenter)
        self.botao_selecionar_pasta = BotaoPrimario("Selecionar Pasta de PDFs", "#43A047", "#2E7D32", recurso_caminho("images/pasta.png"))
        self.botao_selecionar_pasta.clicked.connect(lambda: self.selecionar_arquivo(True))
        self.botao_selecionar_csv = BotaoPrimario("Selecionar Arquivo CSV", "#FFC107", "#FFA000", recurso_caminho("images/csv.png"))
        self.botao_selecionar_csv.clicked.connect(self.selecionar_csv)
        self.botao_gerar = BotaoPrimario("Gerar Planilha", "#2196F3", "#1976D2", None)
        self.botao_gerar.setEnabled(False)
        self.botao_gerar.clicked.connect(self.gerar_planilha)
        botoes_layout.addWidget(self.botao_selecionar_pasta)
        botoes_layout.addWidget(self.botao_selecionar_csv)
        botoes_layout.addWidget(self.botao_gerar)
        main_layout.addLayout(botoes_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setVisible(False)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def voltar_dashboard(self):
        from ui.dashboard import Dashboard
        self.dashboard = Dashboard()
        self.dashboard.showMaximized()
        self.close()

    def selecionar_arquivo(self, is_pasta):
        if is_pasta:
            caminho = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de PDFs", "")
        else:
            return
        if caminho:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.botao_selecionar_pasta.setEnabled(False)
            self.botao_selecionar_csv.setEnabled(False)
            self.worker = WorkerThread(caminho, is_pasta)
            self.worker.progress.connect(self.atualizar_progresso)
            self.worker.finished.connect(self.processamento_concluido)
            self.worker.error.connect(self.erro_processamento)
            self.worker.start()

    def selecionar_csv(self):
        caminho_csv, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo CSV", "", "Arquivos CSV (*.csv)")
        if caminho_csv:
            try:
                # Valida a estrutura do CSV
                df_validado = carregar_planilha_relacao(caminho_csv)
                if df_validado.empty:
                    raise ValueError("O arquivo CSV está vazio após o processamento.")
                self.caminho_csv = caminho_csv
                QMessageBox.information(self, "CSV Válido", f"Arquivo CSV carregado com sucesso:\n{caminho_csv}")
            except Exception as e:
                QMessageBox.critical(self, "Erro no CSV", f"Erro ao validar o CSV:\n{str(e)}")

    def atualizar_progresso(self, valor):
        self.progress_bar.setValue(valor)

    def processamento_concluido(self, dados, nome_arquivo):
        self.dados_extraidos = dados
        self.nome_arquivo = nome_arquivo
        self.progress_bar.setVisible(False)
        self.botao_selecionar_pasta.setEnabled(True)
        self.botao_selecionar_csv.setEnabled(True)

        header = [
            'DATA', 'BASE', 'CNPJ', 'Nº NF', 'MERCADORIA',
            'QUANTIDADE', 'VALOR TOTAL', 'ESTABELECIMENTO',
            'CIDADE/UF', 'ARQUIVO ORIGEM'
        ]
        self.table.clear()
        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(dados))
        self.table.setHorizontalHeaderLabels(header)
        for r, row_data in enumerate(dados):
            for c, val in enumerate(row_data):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.setVisible(True)
        self.botao_gerar.setEnabled(True)

    def erro_processamento(self, mensagem_erro):
        self.progress_bar.setVisible(False)
        self.botao_selecionar_pasta.setEnabled(True)
        self.botao_selecionar_csv.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro ao processar o(s) arquivo(s): {mensagem_erro}")

    def gerar_planilha(self):
        if not self.dados_extraidos:
            QMessageBox.warning(self, "Aviso", "Não há dados para gerar a planilha.")
            return
        if not self.caminho_csv:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo CSV antes de gerar a planilha.")
            return

        df_pdf = pd.DataFrame(self.dados_extraidos, columns=[
            'DATA', 'BASE', 'CNPJ', 'Nº NF', 'MERCADORIA',
            'QUANTIDADE', 'VALOR TOTAL', 'ESTABELECIMENTO',
            'CIDADE/UF', 'ARQUIVO ORIGEM'
        ])

        comparar_transacoes_interface(df_pdf, self, self.caminho_csv)