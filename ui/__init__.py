"""
Package de l'interface graphique PySide6 WinRAR.
"""
from ui.main_window import MainWindow
from ui.theme import WinRARTheme
from ui.archive_dialog import ArchiveDialog
from ui.extract_dialog import ExtractDialog
from ui.progress_dialog import ProgressDialog
from ui.lz77_demo import LZ77DemoDialog
from ui.arithmetic_demo import ArithmeticDemoDialog
from ui.comparison_dialog import ComparisonDialog
from ui.info_dialog import InfoDialog
from ui.course_lesson_dialog import CourseLessonDialog

__all__ = [
    "MainWindow",
    "WinRARTheme",
    "ArchiveDialog",
    "ExtractDialog",
    "ProgressDialog",
    "LZ77DemoDialog",
    "ArithmeticDemoDialog",
    "ComparisonDialog",
    "InfoDialog",
    "CourseLessonDialog",
]
