"""Folder picker: editable path, browse button and drag-and-drop of a folder."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class PathPicker(QFrame):
    path_changed = Signal(str)

    def __init__(self, title: str, hint: str, parent=None):
        super().__init__(parent)
        self.setObjectName("PathPicker")
        self.setAcceptDrops(True)
        self._title = title

        title_label = QLabel(title)
        title_label.setObjectName("PickerTitle")

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(hint)
        self.edit.setAcceptDrops(False)  # let the frame handle folder drops
        self.edit.setClearButtonEnabled(True)
        self.edit.editingFinished.connect(self._emit_changed)

        browse_btn = QPushButton("浏览…")
        browse_btn.setObjectName("SoftButton")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)

        row = QHBoxLayout()
        row.addWidget(self.edit, 1)
        row.addWidget(browse_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.addWidget(title_label)
        layout.addLayout(row)

    def path(self) -> str:
        return os.path.normpath(self.edit.text().strip().strip('"')) if self.edit.text().strip() else ""

    def set_path(self, value: str, emit: bool = True) -> None:
        self.edit.setText(os.path.normpath(value) if value else "")
        if emit:
            self._emit_changed()

    def _emit_changed(self) -> None:
        self.path_changed.emit(self.path())

    def _on_browse(self) -> None:
        start = self.path() if os.path.isdir(self.path()) else ""
        chosen = QFileDialog.getExistingDirectory(self, f"选择{self._title}", start)
        if chosen:
            self.set_path(chosen)

    @staticmethod
    def _dropped_folder(event) -> str:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                local = url.toLocalFile()
                if os.path.isdir(local):
                    return local
                if os.path.isfile(local):
                    return os.path.dirname(local)
        return ""

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and self._dropped_folder(event):
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._clear_drag_state()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        folder = self._dropped_folder(event)
        self._clear_drag_state()
        if folder:
            self.set_path(folder)
            event.acceptProposedAction()

    def _clear_drag_state(self) -> None:
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
