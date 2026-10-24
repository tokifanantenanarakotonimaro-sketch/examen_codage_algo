"""
Dialogue « Extraire vers » inspiré de WinRAR.
Permet de choisir le dossier de destination, les options d'écrasement
et la sélection des fichiers.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QGroupBox,
    QFileDialog,
    QCheckBox,
)
from PySide6.QtCore import Qt
import os


class ExtractDialog(QDialog):
    """Fenêtre de dialogue WinRAR 'Extraire vers'."""

    def __init__(self, default_dest: str, archive_name: str, has_selection: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chemin d'extraction et options")
        self.setFixedSize(500, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.archive_name = archive_name
        self.has_selection = has_selection
        self._init_ui(default_dest)

    def _init_ui(self, default_dest: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Dossier de destination
        grp_dest = QGroupBox("Dossier de destination")
        d_layout = QGridLayout(grp_dest)

        self.txt_dest_dir = QLineEdit(default_dest)
        d_layout.addWidget(self.txt_dest_dir, 0, 0)

        self.btn_browse = QPushButton("Parcourir...")
        self.btn_browse.clicked.connect(self._browse_directory)
        d_layout.addWidget(self.btn_browse, 0, 1)

        self.chk_subfolder = QCheckBox(f"Extraire dans un sous-dossier /{os.path.splitext(self.archive_name)[0]}")
        self.chk_subfolder.setChecked(False)
        d_layout.addWidget(self.chk_subfolder, 1, 0, 1, 2)

        layout.addWidget(grp_dest)

        # 2. Fichiers à extraire
        grp_files = QGroupBox("Sélection des fichiers")
        f_layout = QVBoxLayout(grp_files)

        self.radio_all = QRadioButton("Extraire tous les fichiers de l'archive")
        self.radio_all.setChecked(not self.has_selection)
        f_layout.addWidget(self.radio_all)

        self.radio_selected = QRadioButton("Extraire uniquement les fichiers sélectionnés")
        self.radio_selected.setChecked(self.has_selection)
        self.radio_selected.setEnabled(self.has_selection)
        f_layout.addWidget(self.radio_selected)

        layout.addWidget(grp_files)

        # 3. Mode d'écrasement des conflits
        grp_overwrite = QGroupBox("Mode d'écrasement des fichiers existants")
        o_layout = QVBoxLayout(grp_overwrite)

        self.radio_overwrite = QRadioButton("Écraser les fichiers existants sans confirmation")
        self.radio_overwrite.setChecked(True)
        o_layout.addWidget(self.radio_overwrite)

        self.radio_skip = QRadioButton("Ignorer les fichiers déjà existants")
        o_layout.addWidget(self.radio_skip)

        layout.addWidget(grp_overwrite)

        # 4. Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _browse_directory(self):
        d = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de destination pour l'extraction",
            self.txt_dest_dir.text() or os.path.expanduser("~"),
        )
        if d:
            self.txt_dest_dir.setText(d)

    @property
    def destination_directory(self) -> str:
        base = self.txt_dest_dir.text().strip()
        if self.chk_subfolder.isChecked():
            sub = os.path.splitext(self.archive_name)[0]
            base = os.path.join(base, sub)
        return base

    @property
    def extract_selected_only(self) -> bool:
        return self.radio_selected.isChecked()

    @property
    def overwrite(self) -> bool:
        return self.radio_overwrite.isChecked()
