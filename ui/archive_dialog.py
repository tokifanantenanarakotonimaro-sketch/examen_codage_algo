"""
Dialogue « Ajouter à l'archive » inspiré de WinRAR.
Permet de choisir l'archive cible, l'algorithme (LZ77, Arithmétique, Combiné),
ses paramètres dynamiques et les options d'archivage.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QFileDialog,
    QSpinBox,
)
from PySide6.QtCore import Qt
import os
from core.archive_format import CompressionAlgorithm


class ArchiveDialog(QDialog):
    """Fenêtre de dialogue WinRAR 'Ajouter à l'archive'."""

    def __init__(self, default_archive_name: str, source_paths: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nom et paramètres de l'archive")
        self.setFixedSize(520, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.source_paths = source_paths
        self._init_ui(default_archive_name)

    def _init_ui(self, default_name: str):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 1. Groupe Nom et destination de l'archive
        grp_dest = QGroupBox("Nom et dossier de l'archive")
        dest_layout = QGridLayout(grp_dest)

        dest_layout.addWidget(QLabel("Nom de l'archive :"), 0, 0)
        self.txt_archive_path = QLineEdit(default_name)
        dest_layout.addWidget(self.txt_archive_path, 0, 1)

        self.btn_browse = QPushButton("Parcourir...")
        self.btn_browse.clicked.connect(self._browse_destination)
        dest_layout.addWidget(self.btn_browse, 0, 2)

        main_layout.addWidget(grp_dest)

        # 2. Groupe Méthode de compression
        grp_algo = QGroupBox("Méthode et algorithme de compression")
        algo_layout = QGridLayout(grp_algo)

        algo_layout.addWidget(QLabel("Méthode de compression :"), 0, 0)
        self.combo_algo = QComboBox()
        self.combo_algo.addItem("Optimale (LZ77 + Codage Arithmétique)", CompressionAlgorithm.COMBINED)
        self.combo_algo.addItem("Dictionnaire (LZ77)", CompressionAlgorithm.LZ77)
        self.combo_algo.addItem("Entropique (Codage Arithmétique)", CompressionAlgorithm.ARITHMETIC)
        self.combo_algo.addItem("Stocker (sans compression)", CompressionAlgorithm.STORE)
        self.combo_algo.currentIndexChanged.connect(self._on_algo_changed)
        algo_layout.addWidget(self.combo_algo, 0, 1)

        main_layout.addWidget(grp_algo)

        # 3. Groupe Paramètres dynamiques de l'algorithme
        self.grp_params = QGroupBox("Paramètres de compression")
        params_layout = QGridLayout(self.grp_params)

        self.lbl_search = QLabel("Taille du dictionnaire (Search Buffer) :")
        self.combo_search = QComboBox()
        for sz, label in [
            (7, "7 octets (Minimal)"),
            (512, "512 octets (Très rapide)"),
            (1024, "1024 octets (Rapide)"),
            (2048, "2048 octets (Standard)"),
            (4096, "4096 octets (Optimal par défaut)"),
            (8192, "8192 octets (Compression forte)"),
            (16384, "16384 octets (Maximale)"),
        ]:
            self.combo_search.addItem(label, sz)
        self.combo_search.setCurrentIndex(4)  # 4096

        params_layout.addWidget(self.lbl_search, 0, 0)
        params_layout.addWidget(self.combo_search, 0, 1)

        self.lbl_lookahead = QLabel("Buffer d'anticipation (Lookahead) :")
        self.combo_lookahead = QComboBox()
        for sz, label in [
            (6, "6 octets (Minimal)"),
            (32, "32 octets"),
            (64, "64 octets"),
            (128, "128 octets"),
            (256, "256 octets (Standard)"),
        ]:
            self.combo_lookahead.addItem(label, sz)
        self.combo_lookahead.setCurrentIndex(4)  # 256

        params_layout.addWidget(self.lbl_lookahead, 1, 0)
        params_layout.addWidget(self.combo_lookahead, 1, 1)

        self.lbl_arithmetic_info = QLabel("Modèle statistique adaptatif 32 bits haute précision (sans perte)")
        self.lbl_arithmetic_info.setStyleSheet("color: #0369A1; font-size: 11px;")
        params_layout.addWidget(self.lbl_arithmetic_info, 2, 0, 1, 2)

        main_layout.addWidget(self.grp_params)

        # 4. Options d'archivage
        grp_opts = QGroupBox("Options d'archivage")
        opts_layout = QVBoxLayout(grp_opts)

        self.chk_preserve_paths = QCheckBox("Conserver les chemins relatifs des dossiers")
        self.chk_preserve_paths.setChecked(True)
        opts_layout.addWidget(self.chk_preserve_paths)

        self.lbl_files_summary = QLabel(f"Fichiers sélectionnés : {len(self.source_paths)}")
        self.lbl_files_summary.setStyleSheet("color: #475569; font-size: 11px;")
        opts_layout.addWidget(self.lbl_files_summary)

        main_layout.addWidget(grp_opts)

        # 5. Boutons OK / Annuler
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_layout)

        # Mettre à jour l'affichage des paramètres initiaux
        self._on_algo_changed()

    def _on_algo_changed(self):
        algo = self.selected_algorithm
        has_lz77 = algo in (CompressionAlgorithm.LZ77, CompressionAlgorithm.COMBINED)
        has_arith = algo in (CompressionAlgorithm.ARITHMETIC, CompressionAlgorithm.COMBINED)

        self.lbl_search.setVisible(has_lz77)
        self.combo_search.setVisible(has_lz77)
        self.lbl_lookahead.setVisible(has_lz77)
        self.combo_lookahead.setVisible(has_lz77)
        self.lbl_arithmetic_info.setVisible(has_arith)
        self.grp_params.setVisible(has_lz77 or has_arith)

    def _browse_destination(self):
        cur = self.txt_archive_path.text()
        initial_dir = os.path.dirname(cur) if cur else ""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'archive CompressLab",
            cur or initial_dir,
            "CompressLab Archive (*.cla)",
        )
        if filename:
            if not filename.lower().endswith(".cla"):
                filename += ".cla"
            self.txt_archive_path.setText(filename)

    @property
    def archive_path(self) -> str:
        path = self.txt_archive_path.text().strip()
        if not path.lower().endswith(".cla"):
            path += ".cla"
        return path

    @property
    def selected_algorithm(self) -> CompressionAlgorithm:
        return self.combo_algo.currentData()

    @property
    def search_window(self) -> int:
        return self.combo_search.currentData()

    @property
    def lookahead_window(self) -> int:
        return self.combo_lookahead.currentData()

    @property
    def preserve_paths(self) -> bool:
        return self.chk_preserve_paths.isChecked()
