"""Entry point for AssetIndex. Run with `python src/main.py`."""
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from assetindex.main_window import MainWindow


def _resource(name: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, name)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AssetIndex")
    icon_path = _resource("favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
