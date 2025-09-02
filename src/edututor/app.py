from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

APP_NAME = "EduTutor"


def resource_path(name: str) -> Path:
    here = Path(__file__).resolve().parent.parent
    return here.parent / "assets" / name


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel("EduTutor MVP", self))
        layout.addWidget(QLabel("This is a placeholder window. UI comes next.", self))
        layout.setAlignment(Qt.AlignTop)  # type: ignore[attr-defined]
        self.setCentralWidget(root)
        self.resize(900, 600)


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv or sys.argv
    os.environ.setdefault("QT_API", "pyside6")
    app = QApplication(argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
