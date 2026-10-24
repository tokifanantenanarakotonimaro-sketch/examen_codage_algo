"""
Point d'entrée principal de CompressLab Archive.
Application de bureau Windows d'archivage et de compression de données.
Moteurs natifs : LZ77 et Codage Arithmétique adaptatif 32 bits.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from ui.theme import WinRARTheme


def main():
    # Définition de l'AppUserModelID pour l'affichage de l'icône dans la barre des tâches Windows
    try:
        import ctypes
        app_id = "compresslab.archive.winrar.2.5"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    # Support haute résolution DPI
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("CompressLab Archive")
    app.setOrganizationName("CompressLab Systems")

    # Forcer une palette claire à fort contraste (évite le texte blanc hérité du Dark Mode de Windows)
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F0F2F5"))
    palette.setColor(QPalette.WindowText, QColor("#0F172A"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#F8FAFC"))
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipText, QColor("#0F172A"))
    palette.setColor(QPalette.Text, QColor("#0F172A"))
    palette.setColor(QPalette.Button, QColor("#ECEFF1"))
    palette.setColor(QPalette.ButtonText, QColor("#0F172A"))
    palette.setColor(QPalette.BrightText, QColor("#EF4444"))
    palette.setColor(QPalette.Highlight, QColor("#2563EB"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    # Application du thème visuel WinRAR
    app.setStyleSheet(WinRARTheme.QSS_STYLESHEET)
    app.setWindowIcon(WinRARTheme.create_vector_icon("archive", 64))

    # Gestion de l'argument de ligne de commande (chemin optionnel)
    initial_path = None
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            initial_path = arg_path

    window = MainWindow(initial_path=initial_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
