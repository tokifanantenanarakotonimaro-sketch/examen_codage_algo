"""
Fenêtre d'analyse et de visualisation pas à pas de l'algorithme LZ77.
Affiche l'état du tampon de recherche, du tampon d'anticipation,
les triplets formels générés et la reconstruction progressive.
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from core.algorithms.lz77_engine import LZ77Engine


class LZ77DemoDialog(QDialog):
    """Fenêtre d'analyse et de trace pas à pas de l'algorithme LZ77."""

    PRESET_1 = "CABRACADABRARRARRAD"
    PRESET_2 = "ABBBTTAYFGCABRYUIUUIACADBRARRARRAD"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analyse de l'Algorithme LZ77 (Trace pas à pas)")
        self.resize(950, 650)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.engine = LZ77Engine()
        self._init_ui()
        self._load_preset(0)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # 1. Barre de configuration
        grp_ctrl = QGroupBox("Configuration de l'encodage LZ77")
        ctrl_layout = QGridLayout(grp_ctrl)

        ctrl_layout.addWidget(QLabel("Jeu d'essai :"), 0, 0)
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("1. Séquence test : CABRACADABRARRARRAD")
        self.combo_presets.addItem("2. Séquence test : ABBBTTAYFGCABRYUIUUIACADBRARRARRAD")
        self.combo_presets.addItem("3. Saisie personnalisée...")
        self.combo_presets.currentIndexChanged.connect(self._load_preset)
        ctrl_layout.addWidget(self.combo_presets, 0, 1)

        ctrl_layout.addWidget(QLabel("Taille Search Buffer (S) :"), 0, 2)
        self.spin_search = QSpinBox()
        self.spin_search.setRange(2, 65535)
        self.spin_search.setValue(7)
        ctrl_layout.addWidget(self.spin_search, 0, 3)

        ctrl_layout.addWidget(QLabel("Taille Lookahead Buffer (L) :"), 0, 4)
        self.spin_lookahead = QSpinBox()
        self.spin_lookahead.setRange(2, 65535)
        self.spin_lookahead.setValue(6)
        ctrl_layout.addWidget(self.spin_lookahead, 0, 5)

        ctrl_layout.addWidget(QLabel("Texte à compresser :"), 1, 0)
        self.txt_input = QLineEdit(self.PRESET_1)
        ctrl_layout.addWidget(self.txt_input, 1, 1, 1, 3)

        self.btn_run = QPushButton("Exécuter pas à pas")
        self.btn_run.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px;")
        self.btn_run.clicked.connect(self.run_demo)
        ctrl_layout.addWidget(self.btn_run, 1, 4, 1, 2)

        layout.addWidget(grp_ctrl)

        # 2. Tableau pas à pas
        self.table = QTableWidget()
        headers = [
            "Étape",
            "Buffer de recherche (Search)",
            "Buffer d'entrée (Lookahead)",
            "Répétition",
            "Distance",
            "Longueur",
            "Symbole suiv.",
            "Triplet (D, L, C)",
            "Décodage progressif",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 3. Zone de résultat & Vérification d'intégrité
        self.lbl_result = QLabel("")
        self.lbl_result.setStyleSheet(
            "background-color: #ECFDF5; border: 1px solid #10B981; border-radius: 4px; "
            "padding: 8px; color: #065F46; font-weight: 600; font-size: 12px;"
        )
        layout.addWidget(self.lbl_result)

        # 4. Format des triplets et fonctionnement
        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setFixedHeight(95)
        self.txt_notes.setStyleSheet("background-color: #F8FAFC; color: #334155; font-size: 11px;")
        layout.addWidget(self.txt_notes)

        self.txt_notes.setHtml(
            "<b>Format des triplets et fonctionnement :</b><br/>"
            "• Les correspondances sont émises sous la forme <b>(distance, longueur, caractère_suivant)</b>.<br/>"
            "• La distance indique le décalage vers l'arrière dans la fenêtre glissante.<br/>"
            "• Les correspondances avec chevauchement (overlap périodique) sont gérées (ex: RARRAD avec distance 3 et longueur 5).<br/>"
            "• Tous les résultats affichés sont calculés dynamiquement par le moteur LZ77."
        )

    def _load_preset(self, index: int):
        if index == 0:
            self.txt_input.setText(self.PRESET_1)
            self.spin_search.setValue(7)
            self.spin_lookahead.setValue(6)
            self.run_demo()
        elif index == 1:
            self.txt_input.setText(self.PRESET_2)
            self.spin_search.setValue(7)
            self.spin_lookahead.setValue(6)
            self.run_demo()

    def run_demo(self):
        text = self.txt_input.text()
        if not text:
            return

        s_size = self.spin_search.value()
        l_size = self.spin_lookahead.value()

        steps = self.engine.encode_step_by_step(text, search_size=s_size, lookahead_size=l_size)

        self.table.setRowCount(len(steps))
        for row, s in enumerate(steps):
            items = [
                str(s["step"]),
                f"[{s['search_buffer']}]",
                f"[{s['lookahead_buffer']}]",
                f"'{s['match']}'" if s["match"] else "-",
                str(s["distance"]),
                str(s["length"]),
                s["next_symbol"],
                s["triplet_str"],
                s["decoded_cumulative"],
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter if col not in (1, 2, 8) else (Qt.AlignLeft | Qt.AlignVCenter))
                if col == 7:  # Triplet généré
                    item.setFont(QFont("Consolas", 10, QFont.Bold))
                    item.setForeground(QColor("#1D4ED8"))
                elif col == 8:  # Décodé
                    item.setFont(QFont("Consolas", 9, QFont.Bold))
                    item.setForeground(QColor("#0F172A"))
                else:
                    item.setFont(QFont("Consolas" if col in (1, 2) else "Segoe UI", 9))
                    item.setForeground(QColor("#0F172A"))
                self.table.setItem(row, col, item)

        # Vérification finale
        final_decoded = steps[-1]["decoded_cumulative"] if steps else ""
        is_exact = (final_decoded == text)

        status_text = (
            f"✓ Opération terminée avec succès en {len(steps)} étapes | "
            f"Vérification d'intégrité : Texte décodé == Texte original : "
            f"{'OUI (100% Identique)' if is_exact else 'NON'} | "
            f"Taille originale : {len(text)} caractères -> {len(steps)} triplets"
        )
        self.lbl_result.setText(status_text)
