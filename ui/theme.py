"""
Thème visuel et générateur d'icônes vectorielles inspirés de WinRAR.
Offre une interface de bureau Windows native, professionnelle et compacte.
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, QPoint, QRectF


class WinRARTheme:
    """Palette de couleurs et feuille de style QSS inspirées de WinRAR."""

    QSS_STYLESHEET = """
    QWidget {
        color: #0F172A;
    }
    QMainWindow, QDialog {
        background-color: #F0F2F5;
        color: #0F172A;
    }
    QMenuBar {
        background-color: #ECEFF1;
        border-bottom: 1px solid #CFD8DC;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        padding: 2px;
        color: #0F172A;
    }
    QMenuBar::item {
        background-color: transparent;
        padding: 4px 10px;
        border-radius: 3px;
        color: #0F172A;
    }
    QMenuBar::item:selected {
        background-color: #CFD8DC;
        color: #000000;
    }
    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #B0BEC5;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        padding: 4px;
        color: #0F172A;
    }
    QMenu::item {
        padding: 6px 24px 6px 20px;
        border-radius: 2px;
        color: #0F172A;
    }
    QMenu::item:selected {
        background-color: #E3F2FD;
        color: #0D47A1;
    }
    QMenu::separator {
        height: 1px;
        background-color: #ECEFF1;
        margin: 4px 8px;
    }
    QToolBar {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FAFAFA, stop:1 #ECEFF1);
        border-top: 1px solid #FFFFFF;
        border-bottom: 1px solid #CFD8DC;
        spacing: 4px;
        padding: 3px 6px;
    }
    QToolButton {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 4px 8px;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 11px;
        font-weight: 600;
        color: #1E293B;
    }
    QToolButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E3F2FD, stop:1 #BBDEFB);
        border: 1px solid #90CAF9;
        color: #0D47A1;
    }
    QToolButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BBDEFB, stop:1 #90CAF9);
        border: 1px solid #64B5F6;
    }
    QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #B0BEC5;
        border-radius: 3px;
        padding: 4px 8px;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        color: #0F172A;
    }
    QLineEdit:focus {
        border: 1px solid #1E88E5;
    }
    QTableWidget, QTableView {
        background-color: #FFFFFF;
        alternate-background-color: #F8FAFC;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        gridline-color: #E2E8F0;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
    }
    QTableWidget::item, QTableView::item {
        color: #0F172A;
        background-color: transparent;
        padding: 4px 6px;
    }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #DBEAFE;
        color: #1E3A8A;
        font-weight: 600;
    }
    QHeaderView::section {
        background-color: #F1F5F9;
        color: #0F172A;
        font-weight: 700;
        font-size: 11px;
        padding: 6px 8px;
        border: none;
        border-right: 1px solid #CBD5E1;
        border-bottom: 1px solid #94A3B8;
    }
    QTableCornerButton::section {
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
    }
    QComboBox {
        background-color: #FFFFFF;
        color: #0F172A;
        border: 1px solid #B0BEC5;
        border-radius: 3px;
        padding: 4px 8px;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #0F172A;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
        border: 1px solid #B0BEC5;
    }
    QTextEdit, QPlainTextEdit {
        background-color: #FFFFFF;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        font-family: "Segoe UI", Arial, sans-serif;
    }
    QLabel {
        color: #0F172A;
    }
    QStatusBar {
        background-color: #ECEFF1;
        border-top: 1px solid #CFD8DC;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 11px;
        color: #1E293B;
    }
    QStatusBar::item {
        border: 1px solid #CFD8DC;
        border-radius: 2px;
        padding: 2px 8px;
        background-color: #FFFFFF;
        color: #0F172A;
    }
    QProgressBar {
        border: 1px solid #B0BEC5;
        border-radius: 4px;
        background-color: #ECEFF1;
        text-align: center;
        font-weight: 600;
        font-size: 11px;
        color: #0F172A;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
        border-radius: 3px;
    }
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #ECEFF1);
        border: 1px solid #B0BEC5;
        border-radius: 3px;
        padding: 5px 16px;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #0F172A;
        min-width: 75px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0F9FF, stop:1 #E0F2FE);
        border: 1px solid #38BDF8;
        color: #0369A1;
    }
    QPushButton:pressed {
        background: #BAE6FD;
        border: 1px solid #0284C7;
    }
    QPushButton:default {
        border: 1px solid #2563EB;
        font-weight: 700;
    }
    QGroupBox {
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 4px;
        background-color: #F0F2F5;
        color: #0F172A;
    }
    QTabWidget::pane {
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
    }
    QTabBar::tab {
        background-color: #E2E8F0;
        color: #334155;
        padding: 6px 14px;
        border: 1px solid #CBD5E1;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12px;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #1E3A8A;
    """

    @staticmethod
    def create_table_item(
        text: str,
        align=Qt.AlignLeft | Qt.AlignVCenter,
        fg_color: str = "#0F172A",
        bold: bool = False,
        icon: QIcon = None,
        font_family: str = "Segoe UI",
        font_size: int = 9,
    ):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align)
        item.setForeground(QColor(fg_color))
        font = QFont(font_family, font_size)
        if bold:
            font.setBold(True)
        item.setFont(font)
        if icon:
            item.setIcon(icon)
        return item

    @staticmethod
    def create_vector_icon(icon_type: str, size: int = 32) -> QIcon:
        """
        Génère une icône vectorielle nette de haute qualité sans dépendre de fichiers images externes.
        """
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        s = float(size)

        if icon_type == "add":
            # Pile de livres WinRAR avec signe Plus vert
            # Livres (bleu, vert, violet)
            p.setPen(QPen(QColor("#1E3A8A"), 1.2))
            p.setBrush(QBrush(QColor("#3B82F6")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.50, s * 0.55, s * 0.14), 2, 2)

            p.setBrush(QBrush(QColor("#10B981")))
            p.drawRoundedRect(QRectF(s * 0.18, s * 0.35, s * 0.52, s * 0.14), 2, 2)

            p.setBrush(QBrush(QColor("#8B5CF6")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.20, s * 0.55, s * 0.14), 2, 2)

            # Ceinture boucle noire
            p.setPen(QPen(QColor("#111827"), 1.5))
            p.drawLine(QPoint(int(s * 0.42), int(s * 0.18)), QPoint(int(s * 0.42), int(s * 0.66)))

            # Signe PLUS vert en bas à droite
            p.setPen(QPen(QColor("#047857"), 1.2))
            p.setBrush(QBrush(QColor("#10B981")))
            p.drawEllipse(QRectF(s * 0.55, s * 0.55, s * 0.40, s * 0.40))
            p.setPen(QPen(Qt.white, 2.2))
            p.drawLine(QPoint(int(s * 0.75), int(s * 0.63)), QPoint(int(s * 0.75), int(s * 0.87)))
            p.drawLine(QPoint(int(s * 0.63), int(s * 0.75)), QPoint(int(s * 0.87), int(s * 0.75)))

        elif icon_type == "extract":
            # Livres WinRAR avec flèche d'extraction bleue vers le haut/droite
            p.setPen(QPen(QColor("#1E3A8A"), 1.2))
            p.setBrush(QBrush(QColor("#3B82F6")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.55, s * 0.55, s * 0.14), 2, 2)

            p.setBrush(QBrush(QColor("#10B981")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.40, s * 0.55, s * 0.14), 2, 2)

            # Flèche bleue d'extraction
            p.setPen(QPen(QColor("#1D4ED8"), 1.2))
            p.setBrush(QBrush(QColor("#2563EB")))
            poly = QPolygon([
                QPoint(int(s * 0.55), int(s * 0.45)),
                QPoint(int(s * 0.85), int(s * 0.15)),
                QPoint(int(s * 0.70), int(s * 0.15)),
                QPoint(int(s * 0.85), int(s * 0.15)),
                QPoint(int(s * 0.85), int(s * 0.30)),
            ])
            p.drawPolygon(poly)
            p.setPen(QPen(QColor("#2563EB"), 3.5))
            p.drawLine(QPoint(int(s * 0.45), int(s * 0.55)), QPoint(int(s * 0.80), int(s * 0.20)))

        elif icon_type == "test":
            # Livres avec coche de validation verte
            p.setPen(QPen(QColor("#1E3A8A"), 1.2))
            p.setBrush(QBrush(QColor("#3B82F6")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.45, s * 0.55, s * 0.14), 2, 2)

            p.setBrush(QBrush(QColor("#10B981")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.30, s * 0.55, s * 0.14), 2, 2)

            # Cercle vert avec coche
            p.setPen(QPen(QColor("#047857"), 1.2))
            p.setBrush(QBrush(QColor("#059669")))
            p.drawEllipse(QRectF(s * 0.50, s * 0.50, s * 0.45, s * 0.45))
            p.setPen(QPen(Qt.white, 2.5))
            p.drawLine(QPoint(int(s * 0.58), int(s * 0.72)), QPoint(int(s * 0.68), int(s * 0.83)))
            p.drawLine(QPoint(int(s * 0.68), int(s * 0.83)), QPoint(int(s * 0.86), int(s * 0.61)))

        elif icon_type == "view":
            # Loupe de visualisation
            p.setPen(QPen(QColor("#3B82F6"), 3.0))
            p.setBrush(QBrush(QColor(224, 242, 254, 180)))
            p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.45, s * 0.45))
            p.setPen(QPen(QColor("#1E293B"), 3.5))
            p.drawLine(QPoint(int(s * 0.52), int(s * 0.52)), QPoint(int(s * 0.82), int(s * 0.82)))

        elif icon_type == "delete":
            # Croix rouge classique WinRAR
            p.setPen(QPen(QColor("#DC2626"), 1.2))
            p.setBrush(QBrush(QColor("#EF4444")))
            p.drawEllipse(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70))
            p.setPen(QPen(Qt.white, 3.0))
            p.drawLine(QPoint(int(s * 0.35), int(s * 0.35)), QPoint(int(s * 0.65), int(s * 0.65)))
            p.drawLine(QPoint(int(s * 0.65), int(s * 0.35)), QPoint(int(s * 0.35), int(s * 0.65)))

        elif icon_type == "info":
            # Bulle bleue 'i'
            p.setPen(QPen(QColor("#1D4ED8"), 1.2))
            p.setBrush(QBrush(QColor("#3B82F6")))
            p.drawEllipse(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70))
            p.setPen(QPen(Qt.white, 3.0))
            p.drawPoint(QPoint(int(s * 0.50), int(s * 0.36)))
            p.drawLine(QPoint(int(s * 0.50), int(s * 0.48)), QPoint(int(s * 0.50), int(s * 0.68)))

        elif icon_type == "search":
            # Lampe torche ou jumelles
            p.setPen(QPen(QColor("#F59E0B"), 1.2))
            p.setBrush(QBrush(QColor("#FBBF24")))
            p.drawRoundedRect(QRectF(s * 0.20, s * 0.25, s * 0.60, s * 0.50), 4, 4)
            p.setPen(QPen(QColor("#B45309"), 2.0))
            p.drawEllipse(QRectF(s * 0.28, s * 0.35, s * 0.18, s * 0.30))
            p.drawEllipse(QRectF(s * 0.54, s * 0.35, s * 0.18, s * 0.30))

        elif icon_type == "folder":
            # Dossier jaune Windows
            p.setPen(QPen(QColor("#D97706"), 1.0))
            p.setBrush(QBrush(QColor("#F59E0B")))
            p.drawRoundedRect(QRectF(s * 0.10, s * 0.30, s * 0.80, s * 0.55), 2, 2)
            p.setBrush(QBrush(QColor("#FCD34D")))
            p.drawRoundedRect(QRectF(s * 0.10, s * 0.20, s * 0.35, s * 0.18), 2, 2)

        elif icon_type == "archive":
            # Archive WinRAR (pile de 3 livres reliés)
            p.setPen(QPen(QColor("#1E3A8A"), 1.0))
            p.setBrush(QBrush(QColor("#2563EB")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.55, s * 0.70, s * 0.18), 2, 2)

            p.setBrush(QBrush(QColor("#059669")))
            p.drawRoundedRect(QRectF(s * 0.18, s * 0.37, s * 0.67, s * 0.18), 2, 2)

            p.setBrush(QBrush(QColor("#7C3AED")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.19, s * 0.70, s * 0.18), 2, 2)

            p.setPen(QPen(QColor("#111827"), 2.0))
            p.drawLine(QPoint(int(s * 0.45), int(s * 0.16)), QPoint(int(s * 0.45), int(s * 0.75)))
            p.setBrush(QBrush(QColor("#F59E0B")))
            p.drawRect(QRectF(s * 0.41, s * 0.42, s * 0.08, s * 0.08))

        elif icon_type == "file":
            # Document feuille blanche avec coin replié
            p.setPen(QPen(QColor("#94A3B8"), 1.0))
            p.setBrush(QBrush(Qt.white))
            poly = QPolygon([
                QPoint(int(s * 0.20), int(s * 0.15)),
                QPoint(int(s * 0.60), int(s * 0.15)),
                QPoint(int(s * 0.80), int(s * 0.35)),
                QPoint(int(s * 0.80), int(s * 0.85)),
                QPoint(int(s * 0.20), int(s * 0.85)),
            ])
            p.drawPolygon(poly)
            p.setPen(QPen(QColor("#CBD5E1"), 1.0))
            p.drawLine(QPoint(int(s * 0.30), int(s * 0.45)), QPoint(int(s * 0.70), int(s * 0.45)))
            p.drawLine(QPoint(int(s * 0.30), int(s * 0.55)), QPoint(int(s * 0.70), int(s * 0.55)))
            p.drawLine(QPoint(int(s * 0.30), int(s * 0.65)), QPoint(int(s * 0.60), int(s * 0.65)))

        elif icon_type == "demo":
            # Symbole scientifique / mathématique
            p.setPen(QPen(QColor("#4F46E5"), 1.2))
            p.setBrush(QBrush(QColor("#EEF2FF")))
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70), 4, 4)
            p.setPen(QPen(QColor("#4338CA"), 2.0))
            p.setFont(QFont("Segoe UI", int(s * 0.38), QFont.Bold))
            p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "f(x)")

        elif icon_type == "benchmark":
            # Graphique barres comparatives
            p.setPen(QPen(QColor("#0891B2"), 1.2))
            p.setBrush(QBrush(QColor("#06B6D4")))
            p.drawRect(QRectF(s * 0.20, s * 0.55, s * 0.15, s * 0.30))
            p.setBrush(QBrush(QColor("#3B82F6")))
            p.drawRect(QRectF(s * 0.42, s * 0.35, s * 0.15, s * 0.50))
            p.setBrush(QBrush(QColor("#10B981")))
            p.drawRect(QRectF(s * 0.65, s * 0.20, s * 0.15, s * 0.65))

        p.end()
        return QIcon(pix)
