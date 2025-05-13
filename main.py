import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from ui.dashboard import Dashboard

def configurar_fonte():
    """Configura fontes para a aplicação"""
    fonte_id = QFontDatabase.addApplicationFont("fonts/segoeui.ttf")
    if fonte_id < 0:
        print("AVISO: Não foi possível carregar a fonte Segoe UI")

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    configurar_fonte()
    
    dashboard = Dashboard()
    dashboard.showMaximized()
    
    sys.exit(app.exec())