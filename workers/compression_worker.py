"""
Worker QThread asynchrone pour les opérations de compression,
décompression et test d'archive en arrière-plan avec rapport de progression
et prise en charge de l'annulation.
"""

from PySide6.QtCore import QThread, Signal
from typing import List, Optional, Callable
from core.compression import CompressionManager
from core.decompression import DecompressionManager
from core.archive_format import CompressionAlgorithm, ArchiveEntry


class CompressionWorker(QThread):
    """Thread exécutant la création d'archive sans figer l'interface."""

    progress_changed = Signal(str, int, int)  # (fichier_courant, index, total)
    finished_success = Signal(list)           # list[CompressionMetrics]
    failed = Signal(str)                      # message d'erreur

    def __init__(
        self,
        archive_path: str,
        source_paths: List[str],
        base_dir: Optional[str] = None,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.COMBINED,
        search_window: int = 4096,
        lookahead_window: int = 256,
        parent=None,
    ):
        super().__init__(parent)
        self.archive_path = archive_path
        self.source_paths = source_paths
        self.base_dir = base_dir
        self.algorithm = algorithm
        self.search_window = search_window
        self.lookahead_window = lookahead_window
        self._is_cancelled = False
        self.compression_manager = CompressionManager()

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            def callback(filename: str, current: int, total: int):
                if self._is_cancelled:
                    raise InterruptedError("Opération annulée par l'utilisateur.")
                self.progress_changed.emit(filename, current, total)

            metrics = self.compression_manager.create_archive_from_files(
                archive_path=self.archive_path,
                source_paths=self.source_paths,
                base_dir=self.base_dir,
                algorithm=self.algorithm,
                search_window=self.search_window,
                lookahead_window=self.lookahead_window,
                progress_callback=callback,
            )
            self.finished_success.emit(metrics)
        except InterruptedError:
            self.failed.emit("Opération annulée.")
        except Exception as e:
            self.failed.emit(str(e))


class ExtractionWorker(QThread):
    """Thread exécutant l'extraction d'archive en arrière-plan."""

    progress_changed = Signal(str, int, int)  # (fichier_courant, index, total)
    finished_success = Signal(list)           # list[tuple(entry, bool, msg)]
    failed = Signal(str)                      # message d'erreur

    def __init__(
        self,
        archive_path: str,
        destination_dir: str,
        selected_entries: Optional[List[str]] = None,
        overwrite: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.archive_path = archive_path
        self.destination_dir = destination_dir
        self.selected_entries = selected_entries
        self.overwrite = overwrite
        self._is_cancelled = False
        self.decompression_manager = DecompressionManager()

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            def callback(filename: str, current: int, total: int):
                if self._is_cancelled:
                    raise InterruptedError("Opération annulée par l'utilisateur.")
                self.progress_changed.emit(filename, current, total)

            results = self.decompression_manager.extract_archive(
                archive_path=self.archive_path,
                destination_dir=self.destination_dir,
                selected_entries=self.selected_entries,
                overwrite=self.overwrite,
                progress_callback=callback,
            )
            self.finished_success.emit(results)
        except InterruptedError:
            self.failed.emit("Extraction annulée.")
        except Exception as e:
            self.failed.emit(str(e))


class TestArchiveWorker(QThread):
    """Thread exécutant le test d'intégrité en mémoire sans écriture disque."""

    progress_changed = Signal(str, int, int)
    finished_success = Signal(list)
    failed = Signal(str)

    def __init__(self, archive_path: str, parent=None):
        super().__init__(parent)
        self.archive_path = archive_path
        self._is_cancelled = False
        self.decompression_manager = DecompressionManager()

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            def callback(filename: str, current: int, total: int):
                if self._is_cancelled:
                    raise InterruptedError("Test annulé par l'utilisateur.")
                self.progress_changed.emit(filename, current, total)

            results = self.decompression_manager.test_archive_integrity(
                archive_path=self.archive_path,
                progress_callback=callback,
            )
            self.finished_success.emit(results)
        except InterruptedError:
            self.failed.emit("Test annulé.")
        except Exception as e:
            self.failed.emit(str(e))
