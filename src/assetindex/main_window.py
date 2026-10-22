"""Main application window."""
from __future__ import annotations

import os

from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import processor
from .constants import APP_NAME
from .widgets.console import ConsoleWidget
from .widgets.path_picker import PathPicker

_STYLE = """
QMainWindow, QWidget#Central { background-color: #fff6f9; }
QLabel { color: #5c2436; }
QLabel#PickerTitle { font-weight: bold; font-size: 14px; }
QFrame#PathPicker {
    background-color: #ffffff; border: 1px solid #f0cdd9; border-radius: 8px;
}
QFrame#PathPicker[dragging="true"] { border: 2px dashed #d88fa5; background-color: #fdecf2; }
QLineEdit {
    border: 1px solid #ecc3d1; border-radius: 4px; padding: 6px; background: #fffafc;
    color: #4a2230; selection-background-color: #e3a8ba;
}
QLineEdit:focus { border: 1px solid #d88fa5; }
QPushButton { font-size: 13px; }
QPushButton#SoftButton {
    background-color: #f7dbe5; color: #5c2436; border: none; border-radius: 4px; padding: 7px 16px;
}
QPushButton#SoftButton:hover { background-color: #f0c3d3; }
QPushButton#OpenButton {
    background-color: #f2b8cb; color: #5c2436; border: none; border-radius: 8px;
    min-height: 46px; font-size: 16px; font-weight: bold;
}
QPushButton#OpenButton:hover { background-color: #e99fb8; }
QPushButton#PrimaryButton {
    background-color: #e3a8ba; color: #5c2436; border: none; border-radius: 6px;
    min-height: 38px; min-width: 220px; padding: 0 28px; font-size: 15px; font-weight: bold;
}
QPushButton#PrimaryButton:hover:!disabled { background-color: #d88fa5; }
QPushButton#PrimaryButton:disabled { background-color: #f2e2e7; color: #bda0a8; }
"""


class _Worker(QThread):
    message = Signal(str, str)
    done = Signal(object)

    def __init__(self, resource_dir: str, output_dir: str, parent=None):
        super().__init__(parent)
        self._resource = resource_dir
        self._output = output_dir

    def run(self) -> None:
        try:
            summary = processor.run(self._resource, self._output, lambda lvl, txt: self.message.emit(lvl, txt))
        except Exception as exc:  # keep the UI alive on unexpected failures
            self.message.emit("error", f"发生未预期的错误：{exc}")
            summary = processor.RunSummary(aborted=True)
        self.done.emit(summary)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AssetIndex - 资产照片自动重命名工具")
        self.resize(900, 720)
        self.setStyleSheet(_STYLE)
        self._settings = QSettings(APP_NAME, APP_NAME)
        self._worker: _Worker | None = None

        self._build_ui()
        self.resource_picker.set_path(self._settings.value("resource_dir", "", str), emit=False)
        self.output_picker.set_path(self._settings.value("output_dir", "", str), emit=False)
        self.console.info("就绪。请选择图片来源（Resource）与图片输出（Output）目录，然后点击“开始重命名输出”。")

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        pickers = QHBoxLayout()
        pickers.setSpacing(14)
        self.resource_picker = PathPicker("图片来源（Resource）", "输入路径、点击浏览，或拖入文件夹")
        self.output_picker = PathPicker("图片输出（Output）", "输入路径、点击浏览，或拖入文件夹")
        pickers.addWidget(self.resource_picker, 1)
        pickers.addWidget(self.output_picker, 1)
        layout.addLayout(pickers)

        opens = QHBoxLayout()
        opens.setSpacing(14)
        self.open_resource_btn = QPushButton("📂  打开图片来源目录")
        self.open_output_btn = QPushButton("📂  打开图片输出目录")
        for btn in (self.open_resource_btn, self.open_output_btn):
            btn.setObjectName("OpenButton")
            btn.setCursor(Qt.PointingHandCursor)
            opens.addWidget(btn, 1)
        layout.addLayout(opens)

        self.run_btn = QPushButton("开始重命名输出")
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        run_row = QHBoxLayout()
        run_row.addStretch(1)
        run_row.addWidget(self.run_btn)
        run_row.addStretch(1)
        layout.addLayout(run_row)

        self.console = ConsoleWidget()
        layout.addWidget(self.console, 1)

        self.resource_picker.path_changed.connect(lambda p: self._settings.setValue("resource_dir", p))
        self.output_picker.path_changed.connect(lambda p: self._settings.setValue("output_dir", p))
        self.open_resource_btn.clicked.connect(lambda: self._open_dir(self.resource_picker.path(), "图片来源", False))
        self.open_output_btn.clicked.connect(lambda: self._open_dir(self.output_picker.path(), "图片输出", True))
        self.run_btn.clicked.connect(self._on_run)

    def _open_dir(self, path: str, label: str, create: bool) -> None:
        if not path:
            self.console.warn(f"尚未设置{label}目录")
            return
        if not os.path.isdir(path):
            if not create:
                self.console.warn(f"{label}目录不存在：{path}")
                return
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as exc:
                self.console.error(f"无法创建{label}目录：{exc}")
                return
        os.startfile(path)

    def _on_run(self) -> None:
        resource, output = self.resource_picker.path(), self.output_picker.path()
        if not resource or not output:
            QMessageBox.warning(self, "提示", "请先选择图片来源目录和图片输出目录。")
            return
        self._settings.setValue("resource_dir", resource)
        self._settings.setValue("output_dir", output)

        self.run_btn.setEnabled(False)
        self.run_btn.setText("处理中…")
        self._worker = _Worker(resource, output, self)
        self._worker.message.connect(self.console.log)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, summary) -> None:
        self.run_btn.setEnabled(True)
        self.run_btn.setText("开始重命名输出")
        if summary.aborted:
            QMessageBox.warning(self, "未执行输出", "检查未通过或无法执行，请查看下方终端中的警告信息。")
        elif summary.failed:
            QMessageBox.warning(
                self, "部分照片组未处理", f"有 {summary.failed} 组照片未能处理，详细路径见下方终端（红色提示）。"
            )

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker is not None and self._worker.isRunning():
            if QMessageBox.question(self, "确认退出", "正在处理中，确定要退出吗？") != QMessageBox.Yes:
                event.ignore()
                return
            self._worker.terminate()
            self._worker.wait()
        self._settings.setValue("resource_dir", self.resource_picker.path())
        self._settings.setValue("output_dir", self.output_picker.path())
        event.accept()
