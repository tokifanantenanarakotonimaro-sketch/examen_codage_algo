"""
Fenêtre d'informations et statistiques d'archive / fichier inspirée de WinRAR.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)
from PySide6.QtCore import Qt
import os
from typing import Optional
from core.archive_format import CLAArchive, ArchiveEntry


class InfoDialog(QDialog):
    """Dialogue d'informations sur l'archive ou le fichier sélectionné."""

    def __init__(self, archive_path: Optional[str] = None, entry: Optional[ArchiveEntry] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Informations et statistiques")
        self.setFixedSize(460, 340)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        grp = QGroupBox("Propriétés de l'archive / fichier")
        grid = QGridLayout(grp)
        grid.setSpacing(8)

        row = 0
        if archive_path and os.path.exists(archive_path):
            grid.addWidget(QLabel("Nom de l'archive :"), row, 0)
            grid.addWidget(QLabel(os.path.basename(archive_path)), row, 1)
            row += 1

            grid.addWidget(QLabel("Chemin complet :"), row, 0)
            lbl_path = QLabel(archive_path)
            lbl_path.setWordWrap(True)
            grid.addWidget(lbl_path, row, 1)
            row += 1

            arch_size = os.path.getsize(archive_path)
            grid.addWidget(QLabel("Taille sur le disque :"), row, 0)
            grid.addWidget(QLabel(f"{arch_size:,} octets".replace(",", " ")), row, 1)
            row += 1

            try:
                arch = CLAArchive(archive_path)
                entries = arch.read_table_of_contents()
                total_orig = sum(e.original_size for e in entries)
                total_comp = sum(e.compressed_size for e in entries)
                ratio = ((total_orig - arch_size) / total_orig * 100) if total_orig > 0 else 0.0

                grid.addWidget(QLabel("Nombre d'éléments :"), row, 0)
                grid.addWidget(QLabel(f"{len(entries)} fichier(s) et dossier(s)"), row, 1)
                row += 1

                grid.addWidget(QLabel("Taille originale totale :"), row, 0)
                grid.addWidget(QLabel(f"{total_orig:,} octets".replace(",", " ")), row, 1)
                row += 1

                grid.addWidget(QLabel("Taux de compression global :"), row, 0)
                grid.addWidget(QLabel(f"{ratio:+.2f} %"), row, 1)
                row += 1

            except Exception:
                pass

        elif entry:
            grid.addWidget(QLabel("Nom du fichier :"), row, 0)
            grid.addWidget(QLabel(entry.filename), row, 1)
            row += 1

            grid.addWidget(QLabel("Chemin dans l'archive :"), row, 0)
            grid.addWidget(QLabel(entry.path), row, 1)
            row += 1

            grid.addWidget(QLabel("Taille originale :"), row, 0)
            grid.addWidget(QLabel(f"{entry.original_size:,} octets".replace(",", " ")), row, 1)
            row += 1

            grid.addWidget(QLabel("Taille compressée :"), row, 0)
            grid.addWidget(QLabel(f"{entry.compressed_size:,} octets".replace(",", " ")), row, 1)
            row += 1

            grid.addWidget(QLabel("Algorithme :"), row, 0)
            grid.addWidget(QLabel(entry.algorithm.display_name), row, 1)
            row += 1

            grid.addWidget(QLabel("SHA-256 d'origine :"), row, 0)
            lbl_sha = QLabel(entry.sha256_hex)
            lbl_sha.setStyleSheet("font-family: Consolas; font-size: 10px;")
            lbl_sha.setWordWrap(True)
            grid.addWidget(lbl_sha, row, 1)
            row += 1

        layout.addWidget(grp)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
