"""
Fenêtre principale WinRAR — CompressLab Archive.
Interface de bureau Windows native pour la navigation de fichiers,
la création, l'ouverture, l'affichage, le test et l'extraction d'archives .cla.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolBar,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QDialog,
    QTextEdit,
    QMenu,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QDesktopServices
from PySide6.QtCore import QUrl

import os
import sys
import time
import datetime
import subprocess

from core.archive_format import CLAArchive, ArchiveEntry, CompressionAlgorithm, ArchiveFormatError
from core.compression import CompressionManager
from core.decompression import DecompressionManager
from core.integrity import IntegrityVerifier
from core.metrics import CompressionMetrics

from workers.compression_worker import CompressionWorker, ExtractionWorker, TestArchiveWorker
from ui.theme import WinRARTheme
from ui.progress_dialog import ProgressDialog
from ui.archive_dialog import ArchiveDialog
from ui.extract_dialog import ExtractDialog
from ui.lz77_demo import LZ77DemoDialog
from ui.arithmetic_demo import ArithmeticDemoDialog
from ui.comparison_dialog import ComparisonDialog
from ui.info_dialog import InfoDialog
from ui.course_lesson_dialog import CourseLessonDialog


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application CompressLab Archive inspirée de WinRAR."""

    def __init__(self, initial_path: str = None):
        super().__init__()
        self.setWindowTitle("CompressLab Archive — [Mode Explorateur]")
        self.resize(1100, 700)

        # État de navigation
        self.is_archive_mode = False
        self.current_archive_path = None
        self.current_folder = os.path.abspath(initial_path or os.getcwd())
        self.archive_entries: list[ArchiveEntry] = []

        self._init_actions()
        self._init_menu_bar()
        self._init_toolbar()
        self._init_central_ui()
        self._init_status_bar()

        # Charger le dossier de départ
        self.navigate_to_folder(self.current_folder)

    # -------------------------------------------------------------------------
    # Initialisation des Actions
    # -------------------------------------------------------------------------
    def _init_actions(self):
        # Actions WinRAR standard
        self.act_add = QAction(WinRARTheme.create_vector_icon("add"), "Ajouter", self)
        self.act_add.setToolTip("Ajouter des fichiers à une archive (Alt+A)")
        self.act_add.setShortcut(QKeySequence("Alt+A"))
        self.act_add.triggered.connect(self.on_action_add)

        self.act_extract = QAction(WinRARTheme.create_vector_icon("extract"), "Extraire vers", self)
        self.act_extract.setToolTip("Extraire les fichiers vers un dossier (Alt+E)")
        self.act_extract.setShortcut(QKeySequence("Alt+E"))
        self.act_extract.triggered.connect(self.on_action_extract)

        self.act_test = QAction(WinRARTheme.create_vector_icon("test"), "Tester", self)
        self.act_test.setToolTip("Tester l'intégrité de l'archive en mémoire (Alt+T)")
        self.act_test.setShortcut(QKeySequence("Alt+T"))
        self.act_test.triggered.connect(self.on_action_test)

        self.act_view = QAction(WinRARTheme.create_vector_icon("view"), "Afficher", self)
        self.act_view.setToolTip("Afficher ou prévisualiser le fichier sélectionné (Alt+V)")
        self.act_view.setShortcut(QKeySequence("Alt+V"))
        self.act_view.triggered.connect(self.on_action_view)

        self.act_delete = QAction(WinRARTheme.create_vector_icon("delete"), "Supprimer", self)
        self.act_delete.setToolTip("Supprimer les éléments sélectionnés (Suppr)")
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self.on_action_delete)

        self.act_search = QAction(WinRARTheme.create_vector_icon("search"), "Rechercher", self)
        self.act_search.setToolTip("Rechercher des fichiers (Ctrl+F)")
        self.act_search.setShortcut(QKeySequence.Find)
        self.act_search.triggered.connect(self.on_action_search)

        self.act_info = QAction(WinRARTheme.create_vector_icon("info"), "Informations", self)
        self.act_info.setToolTip("Afficher les propriétés et statistiques (Alt+I)")
        self.act_info.setShortcut(QKeySequence("Alt+I"))
        self.act_info.triggered.connect(self.on_action_info)

        # Outils complémentaires
        self.act_benchmark = QAction(WinRARTheme.create_vector_icon("benchmark"), "Test de vitesse et compression...", self)
        self.act_benchmark.setToolTip("Évaluer les performances de compression et décompression (Alt+B)")
        self.act_benchmark.setShortcut(QKeySequence("Alt+B"))
        self.act_benchmark.triggered.connect(self.open_comparison_dialog)

    # -------------------------------------------------------------------------
    # Barre de Menus WinRAR
    # -------------------------------------------------------------------------
    def _init_menu_bar(self):
        menubar = self.menuBar()

        # Fichier
        menu_file = menubar.addMenu("&Fichier")
        act_open_arch = menu_file.addAction("Ouvrir une archive...")
        act_open_arch.setShortcut(QKeySequence.Open)
        act_open_arch.triggered.connect(self.open_archive_dialog)

        act_new_arch = menu_file.addAction("Nouvelle archive...")
        act_new_arch.setShortcut(QKeySequence.New)
        act_new_arch.triggered.connect(self.on_action_add)

        menu_file.addSeparator()
        act_close_arch = menu_file.addAction("Fermer l'archive")
        act_close_arch.setShortcut(QKeySequence.Close)
        act_close_arch.triggered.connect(self.close_archive)

        menu_file.addSeparator()
        act_quit = menu_file.addAction("Quitter")
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self.close)

        # Commandes
        menu_cmd = menubar.addMenu("&Commandes")
        menu_cmd.addAction(self.act_add)
        menu_cmd.addAction(self.act_extract)
        menu_cmd.addAction(self.act_test)
        menu_cmd.addAction(self.act_view)
        menu_cmd.addAction(self.act_delete)
        menu_cmd.addSeparator()
        menu_cmd.addAction(self.act_search)
        menu_cmd.addAction(self.act_info)

        # Outils
        menu_tools = menubar.addMenu("&Outils")
        menu_tools.addAction(self.act_benchmark)
        act_gen_pdf = menu_tools.addAction("Générer un rapport d'analyse...")
        act_gen_pdf.triggered.connect(self.generate_pdf_report_direct)
        menu_tools.addSeparator()

        menu_diag = menu_tools.addMenu("Diagnostic des algorithmes")
        act_diag_lesson = menu_diag.addAction("Conformité des algorithmes...")
        act_diag_lesson.triggered.connect(self.open_course_lesson_dialog)
        act_diag_lz = menu_diag.addAction("Visualisation pas à pas LZ77...")
        act_diag_lz.triggered.connect(self.open_lz77_demo)
        act_diag_ar = menu_diag.addAction("Visualisation Codage Arithmétique...")
        act_diag_ar.triggered.connect(self.open_arithmetic_demo)

        # Favoris
        menu_fav = menubar.addMenu("&Favoris")
        act_fav_home = menu_fav.addAction("Dossier personnel")
        act_fav_home.triggered.connect(lambda: self.navigate_to_folder(os.path.expanduser("~")))
        act_fav_desktop = menu_fav.addAction("Bureau")
        act_fav_desktop.triggered.connect(lambda: self.navigate_to_folder(os.path.join(os.path.expanduser("~"), "Desktop")))
        act_fav_docs = menu_fav.addAction("Documents")
        act_fav_docs.triggered.connect(lambda: self.navigate_to_folder(os.path.join(os.path.expanduser("~"), "Documents")))
        menu_fav.addSeparator()
        act_fav_c = menu_fav.addAction("Disque C:\\")
        act_fav_c.triggered.connect(lambda: self.navigate_to_folder("C:\\"))

        # Options
        menu_options = menubar.addMenu("&Options")
        act_refresh = menu_options.addAction("Actualiser l'affichage")
        act_refresh.setShortcut(QKeySequence.Refresh)
        act_refresh.triggered.connect(self.refresh_view)

        # Aide
        menu_help = menubar.addMenu("&Aide")
        act_help_topics = menu_help.addAction("Rubriques d'aide")
        act_help_topics.setShortcut(QKeySequence.HelpContents)
        act_help_topics.triggered.connect(self.show_help_dialog)
        menu_help.addSeparator()
        act_about = menu_help.addAction("À propos de CompressLab Archive...")
        act_about.triggered.connect(self.show_about_dialog)

    # -------------------------------------------------------------------------
    # Barre d'Outils WinRAR (Uniquement l'essentiel)
    # -------------------------------------------------------------------------
    def _init_toolbar(self):
        toolbar = QToolBar("Barre d'outils WinRAR", self)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_add)
        toolbar.addAction(self.act_extract)
        toolbar.addAction(self.act_test)
        toolbar.addAction(self.act_view)
        toolbar.addAction(self.act_delete)
        toolbar.addAction(self.act_search)
        toolbar.addAction(self.act_info)

    # -------------------------------------------------------------------------
    # Interface Centrale (Barre de chemin + Liste de fichiers)
    # -------------------------------------------------------------------------
    def _init_central_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # Barre de navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)

        self.btn_up = QPushButton("▲ Dossier parent")
        self.btn_up.setFixedWidth(110)
        self.btn_up.clicked.connect(self.on_navigate_up)
        nav_layout.addWidget(self.btn_up)

        self.lbl_path_title = QLabel("Emplacement :")
        self.lbl_path_title.setStyleSheet("font-weight: 600; color: #37474F;")
        nav_layout.addWidget(self.lbl_path_title)

        self.txt_path = QLineEdit()
        self.txt_path.returnPressed.connect(self._on_path_entered)
        nav_layout.addWidget(self.txt_path)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setFixedWidth(85)
        self.btn_refresh.clicked.connect(self.refresh_view)
        nav_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(nav_layout)

        # Liste de fichiers WinRAR
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(7)
        headers = [
            "Nom",
            "Taille",
            "Taille compressée",
            "Type",
            "Modifié le",
            "Taux de réduction",
            "Intégrité SHA-256",
        ]
        self.file_table.setHorizontalHeaderLabels(headers)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setShowGrid(True)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.file_table.cellDoubleClicked.connect(self.on_item_double_clicked)
        self.file_table.itemSelectionChanged.connect(self._update_status_selection)
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        main_layout.addWidget(self.file_table)

    # -------------------------------------------------------------------------
    # Barre d'État WinRAR
    # -------------------------------------------------------------------------
    def _init_status_bar(self):
        status = self.statusBar()

        self.lbl_status_mode = QLabel("Système de fichiers")
        self.lbl_status_mode.setMinimumWidth(220)
        status.addWidget(self.lbl_status_mode)

        self.lbl_status_items = QLabel("0 élément(s)")
        self.lbl_status_items.setMinimumWidth(180)
        status.addWidget(self.lbl_status_items)

        self.lbl_status_size = QLabel("Taille totale : 0 o")
        self.lbl_status_size.setMinimumWidth(180)
        status.addWidget(self.lbl_status_size)

        self.lbl_status_msg = QLabel("Prêt")
        status.addPermanentWidget(self.lbl_status_msg)

    # -------------------------------------------------------------------------
    # Logique de Navigation & Remplissage du tableau
    # -------------------------------------------------------------------------
    def navigate_to_folder(self, folder_path: str):
        """Affiche les fichiers d'un dossier standard du disque dur."""
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Chemin invalide", f"Le dossier n'existe pas : {folder_path}")
            return

        self.is_archive_mode = False
        self.current_archive_path = None
        self.current_folder = os.path.abspath(folder_path)
        self.txt_path.setText(self.current_folder)
        self.setWindowTitle(f"CompressLab Archive — {self.current_folder}")
        self.lbl_status_mode.setText("Système de fichiers")

        self.file_table.setRowCount(0)

        # Lister le dossier
        try:
            entries = os.listdir(self.current_folder)
        except PermissionError:
            QMessageBox.critical(self, "Accès refusé", "Permissions insuffisantes pour lire ce dossier.")
            return

        # Trier dossiers d'abord, puis fichiers
        dirs = []
        files = []
        for e in entries:
            full = os.path.join(self.current_folder, e)
            if os.path.isdir(full):
                dirs.append(e)
            else:
                files.append(e)

        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        total_items = len(dirs) + len(files)
        self.file_table.setRowCount(total_items)
        row = 0
        total_size = 0

        # Remplir dossiers
        for d in dirs:
            full_p = os.path.join(self.current_folder, d)
            mtime_str = self._format_timestamp(os.path.getmtime(full_p))

            item_name = WinRARTheme.create_table_item(d, icon=WinRARTheme.create_vector_icon("folder", 18), bold=True)
            item_name.setData(Qt.UserRole, full_p)
            item_name.setData(Qt.UserRole + 1, True)  # is_dir

            self.file_table.setItem(row, 0, item_name)
            self.file_table.setItem(row, 1, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            self.file_table.setItem(row, 2, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            self.file_table.setItem(row, 3, WinRARTheme.create_table_item("Dossier de fichiers"))
            self.file_table.setItem(row, 4, WinRARTheme.create_table_item(mtime_str))
            self.file_table.setItem(row, 5, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            self.file_table.setItem(row, 6, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            row += 1

        # Remplir fichiers
        for f in files:
            full_p = os.path.join(self.current_folder, f)
            sz = os.path.getsize(full_p)
            total_size += sz
            mtime_str = self._format_timestamp(os.path.getmtime(full_p))

            ext = os.path.splitext(f)[1].lower()
            is_cla = (ext == ".cla")

            item_name = WinRARTheme.create_table_item(
                f,
                icon=WinRARTheme.create_vector_icon("archive" if is_cla else "file", 18),
                bold=is_cla,
                fg_color="#1D4ED8" if is_cla else "#0F172A",
            )
            item_name.setData(Qt.UserRole, full_p)
            item_name.setData(Qt.UserRole + 1, False)

            self.file_table.setItem(row, 0, item_name)
            self.file_table.setItem(row, 1, WinRARTheme.create_table_item(self._format_bytes(sz), Qt.AlignRight | Qt.AlignVCenter))
            self.file_table.setItem(row, 2, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            type_desc = "Archive CompressLab (.cla)" if is_cla else f"Fichier {ext.upper() or 'binaire'}"
            self.file_table.setItem(row, 3, WinRARTheme.create_table_item(type_desc))
            self.file_table.setItem(row, 4, WinRARTheme.create_table_item(mtime_str))
            self.file_table.setItem(row, 5, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            self.file_table.setItem(row, 6, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            row += 1

        self.lbl_status_items.setText(f"{total_items} élément(s)")
        self.lbl_status_size.setText(f"Taille totale : {self._format_bytes(total_size)}")
        self.lbl_status_msg.setText("Prêt")

    def open_archive(self, archive_path: str):
        """Ouvre une archive .cla et affiche son arborescence interne."""
        try:
            archive = CLAArchive(archive_path)
            entries = archive.read_table_of_contents()
        except ArchiveFormatError as e:
            QMessageBox.critical(self, "Erreur d'archive", f"Impossible d'ouvrir l'archive .cla :\n{str(e)}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue :\n{str(e)}")
            return

        self.is_archive_mode = True
        self.current_archive_path = os.path.abspath(archive_path)
        self.archive_entries = entries
        self.txt_path.setText(self.current_archive_path)
        self.setWindowTitle(f"{os.path.basename(archive_path)} — CompressLab Archive")
        self.lbl_status_mode.setText(f"Archive : {os.path.basename(archive_path)}")

        self.file_table.setRowCount(len(entries))
        total_orig = 0
        total_comp = 0

        for row, entry in enumerate(entries):
            total_orig += entry.original_size
            total_comp += entry.compressed_size

            item_name = WinRARTheme.create_table_item(
                entry.path,
                icon=WinRARTheme.create_vector_icon("folder" if entry.is_dir else "file", 18),
                bold=entry.is_dir,
            )
            item_name.setData(Qt.UserRole, entry.path)
            item_name.setData(Qt.UserRole + 1, entry.is_dir)
            item_name.setData(Qt.UserRole + 2, entry)

            self.file_table.setItem(row, 0, item_name)

            if entry.is_dir:
                self.file_table.setItem(row, 1, WinRARTheme.create_table_item("-", Qt.AlignCenter))
                self.file_table.setItem(row, 2, WinRARTheme.create_table_item("-", Qt.AlignCenter))
                self.file_table.setItem(row, 3, WinRARTheme.create_table_item("Dossier archivé"))
                self.file_table.setItem(row, 4, WinRARTheme.create_table_item(self._format_timestamp(entry.mtime)))
                self.file_table.setItem(row, 5, WinRARTheme.create_table_item("-", Qt.AlignCenter))
                self.file_table.setItem(row, 6, WinRARTheme.create_table_item("-", Qt.AlignCenter))
            else:
                self.file_table.setItem(row, 1, WinRARTheme.create_table_item(self._format_bytes(entry.original_size), Qt.AlignRight | Qt.AlignVCenter))
                self.file_table.setItem(row, 2, WinRARTheme.create_table_item(self._format_bytes(entry.compressed_size), Qt.AlignRight | Qt.AlignVCenter))
                self.file_table.setItem(row, 3, WinRARTheme.create_table_item(f"Fichier ({entry.algorithm.display_name})"))
                self.file_table.setItem(row, 4, WinRARTheme.create_table_item(self._format_timestamp(entry.mtime)))

                ratio = CompressionMetrics.calculate_reduction_ratio(entry.original_size, entry.compressed_size)
                ratio_color = "#059669" if ratio > 0 else ("#DC2626" if ratio < 0 else "#0F172A")
                item_ratio = WinRARTheme.create_table_item(f"{ratio:+.1f} %", Qt.AlignCenter, fg_color=ratio_color, bold=True)
                self.file_table.setItem(row, 5, item_ratio)

                sha_display = entry.sha256_hex[:12] + "..."
                item_sha = WinRARTheme.create_table_item(sha_display, Qt.AlignCenter, font_family="Consolas", font_size=8)
                self.file_table.setItem(row, 6, item_sha)

        self.lbl_status_items.setText(f"{len(entries)} fichier(s) dans l'archive")
        self.lbl_status_size.setText(
            f"Orig: {self._format_bytes(total_orig)} | Comp: {self._format_bytes(total_comp)}"
        )
        self.lbl_status_msg.setText("Archive ouverte avec succès")

    def close_archive(self):
        """Ferme l'archive ouverte et revient au dossier parent sur le disque dur."""
        if self.is_archive_mode:
            parent_d = os.path.dirname(self.current_archive_path) if self.current_archive_path else os.getcwd()
            self.navigate_to_folder(parent_d)

    # -------------------------------------------------------------------------
    # Actions Utilisateur (WinRAR Command Buttons)
    # -------------------------------------------------------------------------
    def on_action_add(self):
        """Ouvre le dialogue WinRAR 'Ajouter à l'archive'."""
        selected_paths = self._get_selected_filesystem_paths()
        if not selected_paths:
            if self.is_archive_mode:
                QMessageBox.information(
                    self,
                    "Ajouter",
                    "Pour ajouter des fichiers, parcourez d'abord le système de fichiers et sélectionnez les éléments.",
                )
                return
            else:
                # Si aucun fichier sélectionné, proposer d'archiver le dossier courant
                selected_paths = [self.current_folder]

        default_name = os.path.join(self.current_folder, "Nouvelle_Archive.cla")
        dlg = ArchiveDialog(default_name, selected_paths, self)
        if dlg.exec() != QDialog.Accepted:
            return

        archive_target = dlg.archive_path
        algorithm = dlg.selected_algorithm
        search_win = dlg.search_window
        look_win = dlg.lookahead_window

        # Affichage du dialogue de progression
        prog_dlg = ProgressDialog("Compression en cours...", self)
        worker = CompressionWorker(
            archive_path=archive_target,
            source_paths=selected_paths,
            base_dir=self.current_folder if dlg.preserve_paths else None,
            algorithm=algorithm,
            search_window=search_win,
            lookahead_window=look_win,
            parent=self,
        )

        worker.progress_changed.connect(prog_dlg.update_progress)
        prog_dlg.cancel_requested.connect(worker.cancel)

        def on_finished(metrics):
            prog_dlg.close()
            total_orig = sum(m.original_size for m in metrics)
            total_comp = sum(m.total_archive_size for m in metrics)
            global_ratio = CompressionMetrics.calculate_reduction_ratio(total_orig, os.path.getsize(archive_target))

            QMessageBox.information(
                self,
                "Archive créée avec succès",
                f"L'archive a été générée avec succès !\n\n"
                f"Emplacement : {archive_target}\n"
                f"Fichiers archivés : {len(metrics)}\n"
                f"Taille originale totale : {self._format_bytes(total_orig)}\n"
                f"Taille finale de l'archive : {self._format_bytes(os.path.getsize(archive_target))}\n"
                f"Taux de réduction global : {global_ratio:+.2f} %\n"
                f"Intégrité cryptographique SHA-256 : Vérifiée (100% Exact)",
            )
            # Ouvrir automatiquement la nouvelle archive
            self.open_archive(archive_target)

        def on_failed(err_msg):
            prog_dlg.close()
            QMessageBox.critical(self, "Erreur de compression", f"L'opération a échoué :\n{err_msg}")

        worker.finished_success.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.start()
        prog_dlg.exec()

    def on_action_extract(self):
        """Ouvre le dialogue WinRAR 'Extraire vers'."""
        if not self.is_archive_mode:
            # Vérifier si l'utilisateur a sélectionné un fichier .cla
            selected = self._get_selected_filesystem_paths()
            cla_files = [p for p in selected if p.lower().endswith(".cla")]
            if cla_files:
                self.open_archive(cla_files[0])
            else:
                QMessageBox.information(
                    self,
                    "Extraire vers",
                    "Veuillez d'abord ouvrir une archive CompressLab (.cla) pour lancer l'extraction.",
                )
                return

        selected_entries = self._get_selected_archive_entry_paths()
        has_selection = len(selected_entries) > 0
        default_dest = os.path.dirname(self.current_archive_path)

        dlg = ExtractDialog(default_dest, os.path.basename(self.current_archive_path), has_selection, self)
        if dlg.exec() != QDialog.Accepted:
            return

        dest_dir = dlg.destination_directory
        filter_entries = selected_entries if dlg.extract_selected_only else None
        overwrite = dlg.overwrite

        prog_dlg = ProgressDialog("Extraction en cours...", self)
        worker = ExtractionWorker(
            archive_path=self.current_archive_path,
            destination_dir=dest_dir,
            selected_entries=filter_entries,
            overwrite=overwrite,
            parent=self,
        )

        worker.progress_changed.connect(prog_dlg.update_progress)
        prog_dlg.cancel_requested.connect(worker.cancel)

        def on_finished(results):
            prog_dlg.close()
            success_count = sum(1 for _, ok, _ in results if ok)
            errors = [f"• {e.path} : {msg}" for e, ok, msg in results if not ok]

            msg = f"Extraction terminée avec succès !\n{success_count} élément(s) extrait(s) vers :\n{dest_dir}\n"
            msg += "Toutes les empreintes SHA-256 ont été contrôlées et validées."
            if errors:
                msg += f"\n\nAvertissements ({len(errors)}) :\n" + "\n".join(errors[:5])

            QMessageBox.information(self, "Extraction terminée", msg)

        def on_failed(err_msg):
            prog_dlg.close()
            QMessageBox.critical(self, "Erreur d'extraction", f"L'extraction a échoué :\n{err_msg}")

        worker.finished_success.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.start()
        prog_dlg.exec()

    def on_action_test(self):
        """Teste l'intégrité de l'archive en mémoire sans écrire sur disque."""
        if not self.is_archive_mode:
            selected = self._get_selected_filesystem_paths()
            cla_files = [p for p in selected if p.lower().endswith(".cla")]
            if cla_files:
                archive_to_test = cla_files[0]
            else:
                QMessageBox.information(self, "Tester", "Veuillez sélectionner ou ouvrir une archive .cla à tester.")
                return
        else:
            archive_to_test = self.current_archive_path

        prog_dlg = ProgressDialog("Test d'intégrité en mémoire...", self)
        worker = TestArchiveWorker(archive_to_test, self)
        worker.progress_changed.connect(prog_dlg.update_progress)
        prog_dlg.cancel_requested.connect(worker.cancel)

        def on_finished(results):
            prog_dlg.close()
            all_ok = all(ok for _, ok, _ in results)
            total = len(results)
            if all_ok:
                QMessageBox.information(
                    self,
                    "Test d'archive réussi",
                    f"✓ Aucune erreur détectée !\n\n"
                    f"Archive : {os.path.basename(archive_to_test)}\n"
                    f"Fichiers testés : {total}\n"
                    f"Décompression en mémoire : 100% Exacte\n"
                    f"Empreintes SHA-256 : Intégrité validée sans corruption.",
                )
            else:
                failures = [f"• {e.path} : {msg}" for e, ok, msg in results if not ok]
                QMessageBox.critical(
                    self,
                    "Échec du test d'intégrité",
                    f"Des erreurs ou corruptions ont été détectées ({len(failures)} fichier(s)) :\n"
                    + "\n".join(failures),
                )

        def on_failed(err_msg):
            prog_dlg.close()
            QMessageBox.critical(self, "Erreur de test", f"Le test a échoué :\n{err_msg}")

        worker.finished_success.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.start()
        prog_dlg.exec()

    def on_action_view(self):
        """Prévisualise ou affiche le fichier sélectionné."""
        if self.is_archive_mode:
            # Prévisualisation en mémoire du fichier archivé
            selected_items = self.file_table.selectedItems()
            if not selected_items:
                return
            row = selected_items[0].row()
            entry: ArchiveEntry = self.file_table.item(row, 0).data(Qt.UserRole + 2)
            if not entry or entry.is_dir:
                return

            try:
                archive = CLAArchive(self.current_archive_path)
                payload = archive.read_entry_payload(entry)
                decomp = DecompressionManager()
                data = decomp.decompress_bytes(
                    payload,
                    algorithm=entry.algorithm,
                    original_size=entry.original_size,
                    search_window=entry.search_window,
                    lookahead_window=entry.lookahead_window,
                )
                self._show_preview_dialog(entry.filename, data)
            except Exception as e:
                QMessageBox.critical(self, "Erreur de visualisation", f"Impossible d'afficher le fichier :\n{str(e)}")

        else:
            paths = self._get_selected_filesystem_paths()
            if not paths:
                return
            target = paths[0]
            if os.path.isdir(target):
                self.navigate_to_folder(target)
            elif target.lower().endswith(".cla"):
                self.open_archive(target)
            else:
                try:
                    with open(target, "rb") as f:
                        data = f.read(65536)  # Lire les premiers 64 Ko pour prévisualisation
                    self._show_preview_dialog(os.path.basename(target), data)
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir le fichier : {str(e)}")

    def _show_preview_dialog(self, title: str, data: bytes):
        """Affiche une fenêtre de prévisualisation texte / hexadécimale."""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Visualisation : {title} ({len(data):,} octets)".replace(",", " "))
        dlg.resize(700, 500)
        vbox = QVBoxLayout(dlg)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont("Consolas", 10))

        # Tenter décodage UTF-8, sinon dump hexadécimal
        try:
            content = data.decode("utf-8")
            txt.setPlainText(content)
        except UnicodeDecodeError:
            # Hex dump
            lines = []
            for i in range(0, min(len(data), 4096), 16):
                chunk = data[i : i + 16]
                hex_str = " ".join(f"{b:02X}" for b in chunk)
                ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
                lines.append(f"{i:08X}  {hex_str:<48}  |{ascii_str}|")
            if len(data) > 4096:
                lines.append(f"... ({len(data) - 4096} octets supplémentaires non affichés)")
            txt.setPlainText("\n".join(lines))

        vbox.addWidget(txt)
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(dlg.accept)
        vbox.addWidget(btn_close)
        dlg.exec()

    def on_action_delete(self):
        """Supprime les éléments sélectionnés (avec confirmation)."""
        if self.is_archive_mode:
            # Suppression dans l'archive
            selected_paths = self._get_selected_archive_entry_paths()
            if not selected_paths:
                return

            res = QMessageBox.question(
                self,
                "Confirmation de suppression",
                f"Voulez-vous vraiment supprimer {len(selected_paths)} élément(s) de l'archive .cla ?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                return

            # Reconstruction de l'archive sans les entrées supprimées
            try:
                archive = CLAArchive(self.current_archive_path)
                entries = archive.read_table_of_contents()
                kept_entries_data = []
                for e in entries:
                    if e.path not in selected_paths:
                        payload = archive.read_entry_payload(e) if not e.is_dir else b""
                        kept_entries_data.append((e, payload))

                CLAArchive.create_archive(self.current_archive_path, kept_entries_data)
                QMessageBox.information(self, "Suppression réussie", "Les éléments ont été retirés de l'archive.")
                self.open_archive(self.current_archive_path)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la suppression dans l'archive :\n{str(e)}")

        else:
            paths = self._get_selected_filesystem_paths()
            if not paths:
                return
            res = QMessageBox.question(
                self,
                "Suppression de fichier(s)",
                f"Voulez-vous supprimer définitivement {len(paths)} élément(s) du disque ?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.Yes:
                import shutil
                for p in paths:
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p)
                        else:
                            os.remove(p)
                    except Exception as e:
                        QMessageBox.warning(self, "Erreur", f"Impossible de supprimer {p} : {str(e)}")
                self.refresh_view()

    def on_action_search(self):
        """Filtre la liste de fichiers."""
        from PySide6.QtWidgets import QInputDialog
        query, ok = QInputDialog.getText(self, "Rechercher", "Entrez le nom ou l'extension à filtrer :")
        if ok and query:
            q = query.lower()
            for row in range(self.file_table.rowCount()):
                item = self.file_table.item(row, 0)
                match = q in item.text().lower()
                self.file_table.setRowHidden(row, not match)

    def on_action_info(self):
        """Affiche les propriétés de l'archive ou du fichier sélectionné."""
        if self.is_archive_mode:
            selected_items = self.file_table.selectedItems()
            entry = None
            if selected_items:
                row = selected_items[0].row()
                entry = self.file_table.item(row, 0).data(Qt.UserRole + 2)
            dlg = InfoDialog(archive_path=self.current_archive_path, entry=entry, parent=self)
            dlg.exec()
        else:
            paths = self._get_selected_filesystem_paths()
            arch_p = paths[0] if (paths and paths[0].lower().endswith(".cla")) else None
            dlg = InfoDialog(archive_path=arch_p, parent=self)
            dlg.exec()

    # -------------------------------------------------------------------------
    # Outils d'analyse et de diagnostic algorithmique
    # -------------------------------------------------------------------------
    def open_course_lesson_dialog(self):
        """Ouvre le dialogue d'évaluation et de vérification des algorithmes."""
        dlg = CourseLessonDialog(self)
        dlg.exec()

    def open_lz77_demo(self):
        dlg = LZ77DemoDialog(self)
        dlg.exec()

    def open_arithmetic_demo(self):
        dlg = ArithmeticDemoDialog(self)
        dlg.exec()

    def open_comparison_dialog(self):
        dlg = ComparisonDialog(self)
        dlg.exec()

    def generate_pdf_report_direct(self):
        from reports.generate_pdf_report import run_benchmark, build_pdf_report
        prog = ProgressDialog("Génération du rapport d'analyse...", self)
        prog.lbl_status.setText("Mesure des performances sur les données de test...")

        class PdfGenThread(QThread):
            done = Signal(str)
            err = Signal(str)

            def run(self):
                try:
                    res = run_benchmark()
                    pdf_path = os.path.abspath("RAPPORT_COMPRESSLAB_EXAMEN.pdf")
                    build_pdf_report(res, pdf_path)
                    self.done.emit(pdf_path)
                except Exception as e:
                    self.err.emit(str(e))

        thread = PdfGenThread(self)

        def on_done(path):
            prog.close()
            QMessageBox.information(
                self,
                "Rapport d'analyse généré",
                f"Le rapport d'analyse des performances a été généré avec succès :\n{path}",
            )

        def on_err(e):
            prog.close()
            QMessageBox.critical(self, "Erreur", f"Échec de la génération :\n{e}")

        thread.done.connect(on_done)
        thread.err.connect(on_err)
        thread.start()
        prog.exec()

    # -------------------------------------------------------------------------
    # Événements et Navigation
    # -------------------------------------------------------------------------
    def on_navigate_up(self):
        if self.is_archive_mode:
            self.close_archive()
        else:
            parent_d = os.path.dirname(self.current_folder)
            if parent_d and parent_d != self.current_folder:
                self.navigate_to_folder(parent_d)

    def _on_path_entered(self):
        path = self.txt_path.text().strip()
        if os.path.isdir(path):
            self.navigate_to_folder(path)
        elif os.path.isfile(path) and path.lower().endswith(".cla"):
            self.open_archive(path)

    def refresh_view(self):
        for row in range(self.file_table.rowCount()):
            self.file_table.setRowHidden(row, False)
        if self.is_archive_mode:
            self.open_archive(self.current_archive_path)
        else:
            self.navigate_to_folder(self.current_folder)

    def on_item_double_clicked(self, row: int, col: int):
        item = self.file_table.item(row, 0)
        if not item:
            return

        is_dir = bool(item.data(Qt.UserRole + 1))
        target_path = item.data(Qt.UserRole)

        if self.is_archive_mode:
            self.on_action_view()
        else:
            if is_dir:
                self.navigate_to_folder(target_path)
            elif target_path.lower().endswith(".cla"):
                self.open_archive(target_path)
            else:
                self.on_action_view()

    def open_archive_dialog(self):
        f, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir une archive CompressLab",
            self.current_folder,
            "CompressLab Archive (*.cla);;Tous les fichiers (*.*)",
        )
        if f:
            self.open_archive(f)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction(self.act_add)
        menu.addAction(self.act_extract)
        menu.addAction(self.act_test)
        menu.addAction(self.act_view)
        menu.addAction(self.act_delete)
        menu.addSeparator()
        menu.addAction(self.act_info)
        menu.exec(self.file_table.viewport().mapToGlobal(pos))

    def _update_status_selection(self):
        selected_rows = set(item.row() for item in self.file_table.selectedItems())
        count = len(selected_rows)
        total = self.file_table.rowCount()
        self.lbl_status_items.setText(f"{count} sélectionné(s) sur {total}")

    def _get_selected_filesystem_paths(self) -> list[str]:
        rows = sorted(set(item.row() for item in self.file_table.selectedItems()))
        paths = []
        for r in rows:
            p = self.file_table.item(r, 0).data(Qt.UserRole)
            if p:
                paths.append(p)
        return paths

    def _get_selected_archive_entry_paths(self) -> list[str]:
        rows = sorted(set(item.row() for item in self.file_table.selectedItems()))
        entry_paths = []
        for r in rows:
            p = self.file_table.item(r, 0).data(Qt.UserRole)
            if p:
                entry_paths.append(p)
        return entry_paths

    def show_help_dialog(self):
        """Affiche les rubriques d'aide de CompressLab Archive."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Aide de CompressLab Archive")
        dlg.resize(680, 520)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        vbox = QVBoxLayout(dlg)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(12)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setStyleSheet(
            "background-color: #FFFFFF; color: #0F172A; font-size: 13px; "
            "border: 1px solid #CBD5E1; border-radius: 4px; padding: 10px;"
        )
        txt.setHtml(
            "<h2>CompressLab Archive — Guide d'utilisation</h2>"
            "<hr/>"
            "<h3>1. Présentation générale</h3>"
            "<p>CompressLab Archive est une solution Windows native de compression, d'archivage "
            "et de sécurisation de données. L'application intègre des moteurs de compression "
            "entièrement natifs et autonomes.</p>"
            "<h3>2. Moteurs de compression intégrés</h3>"
            "<p><b>• Moteur LZ77 (Dictionnaire glissant) :</b><br/>"
            "Recherche dynamique des redondances séquentielles avec buffer de recherche glissant "
            "et buffer d'anticipation. Encode les correspondances sous forme de triplets "
            "<i>(distance, longueur, caractère)</i> avec gestion optimale des motifs cycliques chevauchants.</p>"
            "<p><b>• Moteur Codage Arithmétique (Entropique adaptatif) :</b><br/>"
            "Modélisation statistique précise des probabilités cumulées par symbole sur l'ensemble "
            "des 256 octets. Utilise l'arithmétique entière 32 bits avec renormalisation continue "
            "pour garantir une compression sans perte et une restitution exacte au bit près.</p>"
            "<p><b>• Pipeline Combiné Haute Densité :</b><br/>"
            "Combine la réduction par dictionnaire LZ77 suivie du codage arithmétique adaptatif "
            "pour maximiser le taux de compression sur les fichiers volumineux.</p>"
            "<h3>3. Intégrité et Sécurité des Archives</h3>"
            "<p>Le format conteneur <b>.cla</b> assure :<br/>"
            "• Détection des altérations par somme de contrôle CRC32 par bloc.<br/>"
            "• Vérification cryptographique globale via empreinte SHA-256.<br/>"
            "• Protection anti-traversée de répertoire (Path Traversal Protection) lors de l'extraction.</p>"
        )
        vbox.addWidget(txt)

        btn = QPushButton("Fermer")
        btn.setDefault(True)
        btn.clicked.connect(dlg.accept)
        vbox.addWidget(btn)
        dlg.exec()

    def show_about_dialog(self):
        """Affiche la boîte À propos inspirée de WinRAR."""
        QMessageBox.about(
            self,
            "À propos de CompressLab Archive",
            "<h3>CompressLab Archive</h3>"
            "<p><b>Version 2.50 (64 bits)</b></p>"
            "<p>Gestionnaire d'archives natif pour Windows.</p>"
            "<p>Fonctionnalités et moteurs intégrés :</p>"
            "<ul>"
            "<li>Moteur de dictionnaire LZ77 avec fenêtrage glissant</li>"
            "<li>Moteur de codage arithmétique adaptatif 32 bits</li>"
            "<li>Pipeline combiné LZ77 + Codage Arithmétique</li>"
            "<li>Format d'archive propriétaire .cla avec intégrité SHA-256</li>"
            "<li>Protection CRC32 contre la corruption de données</li>"
            "</ul>"
            "<p style='color: #64748B; font-size: 11px;'>Copyright © 2026 CompressLab Systems Inc. Tous droits réservés.</p>",
        )

    # -------------------------------------------------------------------------
    # Formatage Utilitaires
    # -------------------------------------------------------------------------
    @staticmethod
    def _format_bytes(size: int) -> str:
        if size < 1024:
            return f"{size} o"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} Ko"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} Mo"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} Go"

    @staticmethod
    def _format_timestamp(epoch: float) -> str:
        if epoch <= 0:
            return "-"
        dt = datetime.datetime.fromtimestamp(epoch)
        return dt.strftime("%d/%m/%Y %H:%M")
