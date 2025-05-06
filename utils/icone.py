import os
import sys
from PySide6 import QtGui

def recurso_caminho(caminho_relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, caminho_relativo)

def usar_icone(janela):
    caminho = recurso_caminho("images/icone.png")
    if os.path.exists(caminho):
        janela.setWindowIcon(QtGui.QIcon(caminho))
