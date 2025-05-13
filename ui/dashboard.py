from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QScrollArea, QGridLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap
from ui.componentes import AnimatedCard
from ui.extracao import TelaExtracao
from utils.icone import usar_icone, recurso_caminho

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard Inicial - Assertivus Contábil")
        self.setGeometry(300, 100, 1200, 700)
        self.setStyleSheet("background-color: #181818; color: white; font-family: Segoe UI;")
        self.animations = []
        
        usar_icone(self)
        self.init_ui()
        QTimer.singleShot(100, self.start_animations)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background-color: #121212;
                border-bottom: 1px solid #2c2c2c;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 0, 25, 0)
        header_layout.setSpacing(15)

        logo_label = QLabel()
        icone_path = recurso_caminho("images/icone.png")
        logo_pixmap = QPixmap(icone_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignVCenter)

        header_layout.addWidget(logo_label)
        header_layout.addStretch()

        main_layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent;")

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

        welcome_section = QVBoxLayout()
        welcome_section.setSpacing(8)

        bem_vindo = QLabel("Bem-vindo!")
        bem_vindo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        bem_vindo.setStyleSheet("color: white; font-size: 32px;")

        subtitulo = QLabel("O que você deseja fazer hoje?")
        subtitulo.setStyleSheet("color: #CCCCCC; font-size: 16px;")

        welcome_section.addWidget(bem_vindo)
        welcome_section.addWidget(subtitulo)

        content_layout.addLayout(welcome_section)

        cards_section = QVBoxLayout()
        cards_section.setSpacing(15)

        section_title = QLabel("Ações Disponíveis")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-top: 30px; margin-bottom: 20px;")
        cards_section.addWidget(section_title)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(15)

        card1 = AnimatedCard(
            recurso_caminho("images/card2.png"),
            "Conversor PDF FGTS",
            [
                "Selecionar pasta",
                "Extração do nome do Empregado",
                "Base e Valor do FGTS",
                "Gerar planilha"
            ],
            "#C62828"
        )
        card1.clicked.connect(self.abrir_tela_extracao)
        self.animations.append(card1.animation)

        cards_grid.addWidget(card1, 0, 0)

        cards_section.addLayout(cards_grid)
        content_layout.addLayout(cards_section)

        footer = QLabel("© 2025 Assertivus Contábil - Todos os direitos reservados.")
        footer.setStyleSheet("color: #FFFFFF; font-size: 12px; margin-top: 30px;")
        footer.setAlignment(Qt.AlignCenter)

        content_layout.addStretch()
        content_layout.addWidget(footer)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def start_animations(self):
        for i, animation in enumerate(self.animations):
            QTimer.singleShot(i * 150, animation.start)

    def abrir_tela_extracao(self):
        self.tela_extracao = TelaExtracao()
        self.tela_extracao.showMaximized()
        self.close()

