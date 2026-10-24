"""
Fenêtre de dialogue de progression WinRAR avec bouton d'annulation.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from ui.theme import WinRARTheme


class ProgressDialog(QDialog):
    """Dialogue de progression pendant les opérations de compression ou d'extraction."""

    cancel_requested = Signal()

    def __init__(self, title: str = "Opération en cours...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(420, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 18, 18, 18)

        self.lbl_status = QLabel("Préparation de l'opération...")
        self.lbl_status.setStyleSheet("font-weight: 600; color: #1E293B;")
        layout.addWidget(self.lbl_status)

        self.lbl_detail = QLabel("Calcul des fichiers...")
        self.lbl_detail.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(self.lbl_detail)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(22)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def update_progress(self, current_file: str, current: int, total: int):
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"Traitement : {current_file}")
        self.lbl_detail.setText(f"Élément {current} sur {total} ({pct} %)")

    def _on_cancel(self):
        self.btn_cancel.setEnabled(False)
        self.lbl_status.setText("Annulation en cours...")
        self.cancel_requested.emit()
