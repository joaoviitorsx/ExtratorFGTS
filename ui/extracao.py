import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout,QFileDialog, QFrame, QMessageBox, QTableWidget, QTableWidgetItem,QSizePolicy
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap

from ui.componentes import BotaoPrimario, BotaoSecundario
from utils.pdf_utils import extrair_texto_pdf
from utils.extracao_fgts import extrair_dados_fgts_mensal
from utils.gerador_planilha import gerar_planilha_fgts
from utils.mensagem import mensagem_error, mensagem_sucesso, mensagem_aviso
from utils.icone import usar_icone, recurso_caminho


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
                    texto = extrair_texto_pdf(caminho_completo)
                    dados = extrair_dados_fgts_mensal(texto)
                    dados_totais.extend(dados)
                    progresso = int((idx / total_arquivos) * 100)
                    self.progress.emit(progresso)
            else:
                nome_arquivo = os.path.basename(self.caminho)
                texto = extrair_texto_pdf(self.caminho)
                dados = extrair_dados_fgts_mensal(texto)
                dados_totais.extend(dados)
                self.progress.emit(100)

            self.finished.emit(dados_totais, nome_arquivo)
        except Exception as e:
            self.error.emit(str(e))


class TelaExtracao(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extração de Dados FGTS - Assertivus Contábil")
        self.setGeometry(300, 100, 1200, 720)
        self.setStyleSheet("background-color: #181818; color: #ECECEC; font-family: 'Segoe UI';")
        self.dados_extraidos = []
        self.nome_arquivo = ""
        self.init_ui()
        usar_icone(self)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Cabeçalho com botão de voltar
        header = QFrame()
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.botao_voltar = BotaoSecundario("Voltar ao Dashboard", recurso_caminho("images/voltar.png"))
        self.botao_voltar.clicked.connect(self.voltar_dashboard)
        header_layout.addWidget(self.botao_voltar)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # Logo
        logo_label = QLabel()
        pix = QPixmap(recurso_caminho("images/logo.png"))
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        # Título
        titulo = QLabel("Conversor de PDF FGTS")
        titulo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(titulo)

        # Botões principais
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(20)
        botoes_layout.setAlignment(Qt.AlignCenter)

        self.botao_selecionar_pasta = BotaoPrimario("Selecionar Pasta de PDFs", "#43A047", "#2E7D32", recurso_caminho("images/pasta.png"))
        self.botao_selecionar_pasta.clicked.connect(lambda: self.selecionar_arquivo(True))

        self.botao_gerar = BotaoPrimario("Gerar Planilha", "#2196F3", "#1976D2", None)
        self.botao_gerar.setEnabled(False)
        self.botao_gerar.clicked.connect(self.gerar_planilha)

        botoes_layout.addWidget(self.botao_selecionar_pasta)
        botoes_layout.addWidget(self.botao_gerar)

        main_layout.addLayout(botoes_layout)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # Tabela de resultados
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

            self.worker = WorkerThread(caminho, is_pasta)
            self.worker.progress.connect(self.atualizar_progresso)
            self.worker.finished.connect(self.processamento_concluido)
            self.worker.error.connect(self.erro_processamento)
            self.worker.start()

    def atualizar_progresso(self, valor):
        self.progress_bar.setValue(valor)

    def processamento_concluido(self, dados, nome_arquivo):
        self.dados_extraidos = dados
        self.nome_arquivo = nome_arquivo
        self.progress_bar.setVisible(False)
        self.botao_selecionar_pasta.setEnabled(True)

        header = ["Matricula", "Empregado", "Admissao", "CPF", "Base FGTS", "Valor FGTS"]
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
        QMessageBox.critical(self, "Erro", f"Erro ao processar o(s) arquivo(s): {mensagem_erro}")

    def gerar_planilha(self):
        if not self.dados_extraidos:
            QMessageBox.warning(self, "Aviso", "Não há dados para gerar a planilha.")
            return

        caminho_saida, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha", "planilha_fgts.xlsx", "Planilhas Excel (*.xlsx)")
        if caminho_saida:
            try:
                gerar_planilha_fgts(self.dados_extraidos, caminho_saida)
                QMessageBox.information(self, "Sucesso", f"Planilha gerada com sucesso em:\n{caminho_saida}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar planilha:\n{str(e)}")
