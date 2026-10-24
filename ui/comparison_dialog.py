"""
Fenêtre de test de vitesse et benchmark multi-formats.
Mesure les performances comparées entre LZ77, Codage Arithmétique et Mode Combiné.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
import os
import subprocess
from reports.generate_pdf_report import run_benchmark, build_pdf_report


class BenchmarkWorker(QThread):
    finished_data = Signal(list)

    def run(self):
        results = run_benchmark()
        self.finished_data.emit(results)


class ComparisonDialog(QDialog):
    """Fenêtre de benchmark comparatif entre LZ77, Arithmétique et Combiné."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test de vitesse et compression — Benchmark multi-formats")
        self.resize(1050, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.results_data = []
        self._init_ui()
        self._start_benchmark()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("Évaluation des performances de compression sur données hétérogènes")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E3A8A;")
        header_layout.addWidget(self.lbl_title)

        header_layout.addStretch()

        self.btn_refresh = QPushButton("Relancer le test")
        self.btn_refresh.clicked.connect(self._start_benchmark)
        header_layout.addWidget(self.btn_refresh)

        self.btn_pdf = QPushButton("Exporter le rapport PDF d'analyse")
        self.btn_pdf.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_pdf.clicked.connect(self._export_pdf)
        header_layout.addWidget(self.btn_pdf)

        layout.addLayout(header_layout)

        # Barre de progression pendant l'évaluation
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Mode indéterminé
        layout.addWidget(self.progress)

        # Tableau comparatif
        self.table = QTableWidget()
        headers = [
            "Catégorie",
            "Format",
            "Taille Originale",
            "LZ77 Seul (Ratio / Tps)",
            "Arithmétique (Ratio / Tps)",
            "Pipeline Combiné (Ratio / Tps)",
            "Intégrité SHA-256",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Légende explicative
        lbl_legend = QLabel(
            "Note technique : Les taux négatifs sur les fichiers multimédias déjà compressés (MP3, JPEG, MP4) "
            "sont normaux et illustrent les limites de la théorie de l'information (entropie maximale du flux d'origine)."
        )
        lbl_legend.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;")
        layout.addWidget(lbl_legend)

    def _start_benchmark(self):
        self.progress.setVisible(True)
        self.btn_refresh.setEnabled(False)
        self.btn_pdf.setEnabled(False)

        self.worker = BenchmarkWorker(self)
        self.worker.finished_data.connect(self._on_benchmark_finished)
        self.worker.start()

    def _on_benchmark_finished(self, results):
        self.results_data = results
        self.progress.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self.btn_pdf.setEnabled(True)

        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            lz = r["algos"]["LZ77"]
            ar = r["algos"]["Arithmétique"]
            cb = r["algos"]["Combiné"]

            all_ok = lz["valid"] and ar["valid"] and cb["valid"]

            item_cat = QTableWidgetItem(r["category"])
            item_cat.setForeground(QColor("#0F172A"))
            self.table.setItem(row, 0, item_cat)

            item_fmt = QTableWidgetItem(r["format"])
            item_fmt.setForeground(QColor("#0F172A"))
            item_fmt.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 1, item_fmt)

            item_size = QTableWidgetItem(f"{r['orig_size']:,} o".replace(",", " "))
            item_size.setForeground(QColor("#0F172A"))
            self.table.setItem(row, 2, item_size)

            def format_algo(a):
                sign = "+" if a["reduction"] > 0 else ""
                return f"{sign}{a['reduction']:.1f}% ({a['comp_time_ms']:.1f}ms)"

            item_lz = QTableWidgetItem(format_algo(lz))
            item_lz.setForeground(QColor("#0F172A"))
            self.table.setItem(row, 3, item_lz)

            item_ar = QTableWidgetItem(format_algo(ar))
            item_ar.setForeground(QColor("#0F172A"))
            self.table.setItem(row, 4, item_ar)

            item_cb = QTableWidgetItem(format_algo(cb))
            if cb["reduction"] > 0:
                item_cb.setForeground(QColor("#059669"))
                item_cb.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                item_cb.setForeground(QColor("#DC2626"))
                item_cb.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 5, item_cb)

            status_item = QTableWidgetItem("✓ Conforme (100%)" if all_ok else "✗ Échec")
            status_item.setForeground(QColor("#059669") if all_ok else QColor("#DC2626"))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 6, status_item)

            for col in range(7):
                self.table.item(row, col).setTextAlignment(Qt.AlignCenter)

    def _export_pdf(self):
        if not self.results_data:
            return
        pdf_path = os.path.abspath("RAPPORT_COMPRESSLAB_EXAMEN.pdf")
        try:
            build_pdf_report(self.results_data, pdf_path)
            QMessageBox.information(
                self,
                "Rapport PDF généré",
                f"Le rapport d'analyse a été généré avec succès :\n{pdf_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'exportation", f"Impossible de générer le PDF :\n{str(e)}")
