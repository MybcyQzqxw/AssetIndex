"""A simple read-only, black log console widget."""
from __future__ import annotations

import html
from datetime import datetime

from PySide6.QtWidgets import QPlainTextEdit

_COLORS = {
    "info": "#d4d4d4",
    "success": "#6ac265",
    "warn": "#e5c07b",
    "error": "#e06c75",
    "alert": "#ff4d4d",
}


class ConsoleWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setStyleSheet(
            "QPlainTextEdit {"
            " background-color: #000000; color: #d4d4d4; border-radius: 6px; padding: 6px;"
            " font-family: Consolas, 'Courier New', monospace; font-size: 12px;"
            "}"
        )

    def log(self, level: str, text: str) -> None:
        color = _COLORS.get(level, _COLORS["info"])
        stamp = datetime.now().strftime("%H:%M:%S")
        body = html.escape(text).replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
        weight = "font-weight:bold;" if level == "alert" else ""
        prefix = "⚠ " if level == "alert" else ""
        self.appendHtml(f'<span style="color:{color};{weight}">[{stamp}] {prefix}{body}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def info(self, text: str) -> None:
        self.log("info", text)

    def success(self, text: str) -> None:
        self.log("success", text)

    def warn(self, text: str) -> None:
        self.log("warn", text)

    def error(self, text: str) -> None:
        self.log("error", text)
