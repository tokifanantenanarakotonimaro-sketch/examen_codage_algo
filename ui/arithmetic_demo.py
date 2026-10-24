"""
Fenêtre d'analyse et de simulation pas à pas du Codage Arithmétique.
Visualise le découpage d'intervalles sur chaîne de test (ex: 'CALCUL').
Affiche :
- La modélisation des symboles et des probabilités cumulées
- Le raffinement successif des intervalles [L_j, R_j]
- La valeur numérique encodée
- Le décodage séquentiel pas à pas
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QTextEdit,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from core.algorithms.arithmetic_engine import ArithmeticEngine


class ArithmeticDemoDialog(QDialog):
    """Fenêtre de démonstration interactive du Codage Arithmétique."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulation du Codage Arithmétique (Découpage d'intervalles)")
        self.resize(1000, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()
        self.run_demo("CALCUL")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # 1. Barre de contrôle
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Texte à modéliser et encoder :"))

        self.txt_input = QLineEdit("CALCUL")
        self.txt_input.setStyleSheet("font-weight: bold; font-size: 13px;")
        ctrl_layout.addWidget(self.txt_input)

        self.btn_preset_calcul = QPushButton("Séquence test 'CALCUL'")
        self.btn_preset_calcul.clicked.connect(lambda: self.run_demo("CALCUL"))
        ctrl_layout.addWidget(self.btn_preset_calcul)

        self.btn_run = QPushButton("Calculer")
        self.btn_run.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px 16px;")
        self.btn_run.clicked.connect(lambda: self.run_demo(self.txt_input.text()))
        ctrl_layout.addWidget(self.btn_run)

        main_layout.addLayout(ctrl_layout)

        # 2. Onglets pour les différentes étapes
        tabs = QTabWidget()

        # Onglet 1 : Modèle et Encodage
        tab_enc = QWidget()
        enc_layout = QVBoxLayout(tab_enc)

        # Modèle des symboles
        grp_model = QGroupBox("1. Modélisation statistique des symboles et intervalles initiaux")
        m_layout = QVBoxLayout(grp_model)
        self.tbl_model = QTableWidget()
        self.tbl_model.setColumnCount(5)
        self.tbl_model.setHorizontalHeaderLabels([
            "N°",
            "Symbole",
            "Nombre d'occurrences",
            "Fréquence relative",
            "Intervalle cumulé initial [Low ; High[",
        ])
        self.tbl_model.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_model.setFixedHeight(140)
        m_layout.addWidget(self.tbl_model)
        enc_layout.addWidget(grp_model)

        # Raffinement des intervalles
        grp_steps = QGroupBox("2. Raffinement successif des bornes d'intervalles")
        s_layout = QVBoxLayout(grp_steps)
        self.tbl_steps = QTableWidget()
        self.tbl_steps.setColumnCount(6)
        self.tbl_steps.setHorizontalHeaderLabels([
            "j",
            "Symbole",
            "L_j (Fraction)",
            "R_j (Fraction)",
            "Intervalle [L_j ; R_j[",
            "Intervalle flottant",
        ])
        self.tbl_steps.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        s_layout.addWidget(self.tbl_steps)
        enc_layout.addWidget(grp_steps)

        tabs.addTab(tab_enc, "1. Modélisation & Encodage")

        # Onglet 2 : Décodage
        tab_dec = QWidget()
        dec_layout = QVBoxLayout(tab_dec)

        grp_dec = QGroupBox("3. Décodage séquentiel par normalisation inverse")
        d_layout = QVBoxLayout(grp_dec)
        self.tbl_dec = QTableWidget()
        self.tbl_dec.setColumnCount(6)
        self.tbl_dec.setHorizontalHeaderLabels([
            "j",
            "D_j (Valeur courante)",
            "s_i (Indice)",
            "Données (Symbole)",
            "Intervalle du symbole",
            "D_{j+1} = (D_j - C(s_{i-1})) / P(s_i)",
        ])
        self.tbl_dec.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        d_layout.addWidget(self.tbl_dec)
        dec_layout.addWidget(grp_dec)

        tabs.addTab(tab_dec, "2. Décodage progressif")

        main_layout.addWidget(tabs)

        # 3. Cartes récapitulatives
        summary_layout = QHBoxLayout()

        self.box_code_course = QLabel("")
        self.box_code_course.setStyleSheet(
            "background-color: #EFF6FF; border: 1px solid #3B82F6; border-radius: 4px; "
            "padding: 8px; color: #1E40AF; font-weight: bold; font-size: 12px;"
        )
        summary_layout.addWidget(self.box_code_course)

        self.box_code_exact = QLabel("")
        self.box_code_exact.setStyleSheet(
            "background-color: #F5F3FF; border: 1px solid #8B5CF6; border-radius: 4px; "
            "padding: 8px; color: #5B21B6; font-weight: bold; font-size: 12px;"
        )
        summary_layout.addWidget(self.box_code_exact)

        self.box_decoded = QLabel("")
        self.box_decoded.setStyleSheet(
            "background-color: #ECFDF5; border: 1px solid #10B981; border-radius: 4px; "
            "padding: 8px; color: #065F46; font-weight: bold; font-size: 12px;"
        )
        summary_layout.addWidget(self.box_decoded)

        main_layout.addLayout(summary_layout)

        # 4. Résumé analytique
        self.txt_explanation = QTextEdit()
        self.txt_explanation.setReadOnly(True)
        self.txt_explanation.setFixedHeight(100)
        self.txt_explanation.setStyleSheet("background-color: #F8FAFC; color: #334155; font-size: 11px;")
        main_layout.addWidget(self.txt_explanation)

    def run_demo(self, text: str):
        if not text:
            return
        self.txt_input.setText(text)

        demo = ArithmeticEngine.pedagogical_course_demo(text)

        # 1. Remplissage Modèle
        sym_table = demo["symbol_table"]
        self.tbl_model.setRowCount(len(sym_table))
        for row, s in enumerate(sym_table):
            self.tbl_model.setItem(row, 0, QTableWidgetItem(str(s["num"])))
            self.tbl_model.setItem(row, 1, QTableWidgetItem(s["symbol"]))
            self.tbl_model.setItem(row, 2, QTableWidgetItem(str(s["count"])))
            self.tbl_model.setItem(row, 3, QTableWidgetItem(s["prob_rounded"]))
            self.tbl_model.setItem(row, 4, QTableWidgetItem(s["interval_str"]))
            for c in range(5):
                item = self.tbl_model.item(row, c)
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#0F172A"))
                if c == 1:
                    item.setFont(QFont("Consolas", 10, QFont.Bold))
                    item.setForeground(QColor("#1D4ED8"))

        # 2. Remplissage Encodage
        enc_steps = demo["encoding_steps"]
        self.tbl_steps.setRowCount(len(enc_steps))
        for row, s in enumerate(enc_steps):
            items = [
                str(s["step"]),
                s["symbol"],
                s.get("l_frac", s["new_low"]),
                s.get("r_frac", s["new_high"]),
                f"[{s.get('l_frac', s['new_low'])} ; {s.get('r_frac', s['new_high'])}[",
                s["interval_str"],
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col in (2, 3, 4):
                    item.setFont(QFont("Consolas", 10, QFont.Bold))
                    item.setForeground(QColor("#1D4ED8"))
                elif col == 1:
                    item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    item.setForeground(QColor("#0F172A"))
                else:
                    item.setFont(QFont("Segoe UI", 9))
                    item.setForeground(QColor("#0F172A"))
                self.tbl_steps.setItem(row, col, item)

        # 3. Remplissage Décodage
        dec_steps = demo["decoding_steps"]
        self.tbl_dec.setRowCount(len(dec_steps))
        for row, s in enumerate(dec_steps):
            items = [
                str(s["step"]),
                s["value"],
                s.get("symbol_index", f"s_{s['step']}"),
                s["found_symbol"],
                s["symbol_interval"],
                s["next_value"],
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3:
                    item.setFont(QFont("Consolas", 12, QFont.Bold))
                    item.setForeground(QColor("#059669"))
                elif col in (1, 5):
                    item.setFont(QFont("Consolas", 10, QFont.Bold))
                    item.setForeground(QColor("#1D4ED8"))
                else:
                    item.setFont(QFont("Segoe UI", 9))
                    item.setForeground(QColor("#0F172A"))
                self.tbl_dec.setItem(row, col, item)

        # 4. Cartes résumées
        self.box_code_course.setText(f"Code représentatif : {demo['encoded_value_course']}")
        self.box_code_exact.setText(f"Code rationnel exact : {demo['encoded_value_exact']}")
        is_exact = (demo["decoded_text"] == text)
        self.box_decoded.setText(
            f"Texte restitué : '{demo['decoded_text']}' {'(✓ 100% Exact)' if is_exact else '(Échec)'}"
        )

        # 5. Note explicative
        self.txt_explanation.setText(demo["explanation"])
