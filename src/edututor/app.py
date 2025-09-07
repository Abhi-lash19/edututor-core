# src/edututor/app.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Qt widgets and helpers
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QFont, QAction
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTextEdit,
    QPlainTextEdit,
    QPushButton,
    QMessageBox,
    QToolBar,
    QStatusBar,
    QFileDialog,
)

# Import orchestrator you added in PR#2 (mock-backed)
from edututor.core.orchestrator import Orchestrator

APP_NAME = "EduTutor"


def resource_path(name: str) -> Path:
    """
    Find assets relative to the project root (assets/...). Useful for icons.
    """
    here = Path(__file__).resolve().parent.parent
    return here.parent / "assets" / name


class MainWindow(QMainWindow):
    """
    MainWindow is an improved interactive test UI for EduTutor:
      - Left: Chat transcript + input
      - Right: Code editor (monospace) + 'Explain This' button
      - Top toolbar: Exam Mode toggle, Save/Load code, Clear transcript
      - Status bar: provider/exam-mode hints

    This is still a lightweight test UI (not the final polished design),
    but it's good for manual QA of guardrails/orchestrator behavior.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Orchestrator: handles classification/policy + mocked LLM responses
        self.orchestrator = Orchestrator()

        # Track exam mode here (simple toggle for the demo)
        self.exam_mode_enabled = False

        # Build UI
        self._build_toolbar()
        self._build_central_widget()
        self._build_status_bar()

        # Window sizing
        self.resize(1000, 700)

        # Keyboard shortcuts
        send_shortcut = QAction("Send (Ctrl+Enter)", self)
        send_shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        send_shortcut.triggered.connect(self._on_send_click)  # type: ignore[arg-type]
        self.addAction(send_shortcut)

    # -------------------------
    # UI construction helpers
    # -------------------------
    def _build_toolbar(self) -> None:
        """Create a small toolbar with exam mode toggle and utility actions."""
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Exam mode toggle action (disables network-ish behavior in the real app)
        self.exam_action = QAction("Enable Exam Mode (OFF)", self)
        self.exam_action.setCheckable(True)
        self.exam_action.triggered.connect(self._toggle_exam_mode)
        tb.addAction(self.exam_action)

        # Clear transcript
        clear_action = QAction("Clear Transcript", self)
        clear_action.triggered.connect(self._clear_transcript)
        tb.addAction(clear_action)

        # Save/Load code from right pane
        save_code_action = QAction("Save Code...", self)
        save_code_action.triggered.connect(self._save_code_to_file)
        tb.addAction(save_code_action)

        load_code_action = QAction("Load Code...", self)
        load_code_action.triggered.connect(self._load_code_from_file)
        tb.addAction(load_code_action)

    def _build_central_widget(self) -> None:
        """Main split layout: chat (left) and code editor (right)."""
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)

        # ----- LEFT: Chat area -----
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(4, 4, 4, 4)

        # Chat transcript (read-only). We'll append Q&A here.
        self.chat_transcript = QTextEdit()
        self.chat_transcript.setReadOnly(True)
        self.chat_transcript.setPlaceholderText("Transcript will appear here...")
        left_layout.addWidget(self.chat_transcript, stretch=7)

        # Input area (multi-line)
        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(120)
        self.input_box.setPlaceholderText("Ask a question (e.g. 'explain recursion' or paste an error)...")
        left_layout.addWidget(self.input_box, stretch=1)

        # Bottom row: Send & Quick category buttons
        bottom_row = QWidget()
        br_layout = QHBoxLayout(bottom_row)
        br_layout.setContentsMargins(0, 0, 0, 0)

        self.send_btn = QPushButton("Send ▶")
        self.send_btn.clicked.connect(self._on_send_click)
        br_layout.addWidget(self.send_btn)

        # Quick hint buttons to simulate user hint category (Concept / Error / Explain)
        self.btn_concept = QPushButton("Concept")
        self.btn_concept.clicked.connect(lambda: self._send_with_hint("concept"))
        br_layout.addWidget(self.btn_concept)

        self.btn_error = QPushButton("Error")
        self.btn_error.clicked.connect(lambda: self._send_with_hint("error"))
        br_layout.addWidget(self.btn_error)

        self.btn_explain = QPushButton("Explain Code")
        self.btn_explain.clicked.connect(lambda: self._send_with_hint("explain"))
        br_layout.addWidget(self.btn_explain)

        left_layout.addWidget(bottom_row, stretch=0)

        splitter.addWidget(left_container)

        # ----- RIGHT: Code editor -----
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 4, 4, 4)

        right_layout.addWidget(QLabel("Code / Snippet (paste here and click Explain This):"))

        # Use QPlainTextEdit with monospace font for code editing
        self.code_box = QPlainTextEdit()
        monospace = QFont("Consolas" if os.name == "nt" else "Courier")
        monospace.setPointSize(11)
        self.code_box.setFont(monospace)
        self.code_box.setPlaceholderText("# Paste code here to ask 'Explain This' (no edits will be made)")
        right_layout.addWidget(self.code_box, stretch=7)

        code_btn_row = QWidget()
        cbr = QHBoxLayout(code_btn_row)
        cbr.setContentsMargins(0, 0, 0, 0)

        self.explain_btn = QPushButton("Explain This ▶")
        self.explain_btn.clicked.connect(self._on_explain_click)
        cbr.addWidget(self.explain_btn)

        # small helper to copy code into chat input quickly
        copy_to_input = QPushButton("Copy to Input")
        copy_to_input.clicked.connect(self._copy_code_to_input)
        cbr.addWidget(copy_to_input)

        right_layout.addWidget(code_btn_row, stretch=0)

        splitter.addWidget(right_container)

        # give left more initial space
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _build_status_bar(self) -> None:
        """Status bar shows small runtime hints (provider / exam mode)."""
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel("Provider: mock | Exam Mode: OFF")
        sb.addWidget(self.status_label)

    # -------------------------
    # UI action handlers
    # -------------------------
    def _append_transcript(self, who: str, text: str) -> None:
        """
        Append a nicely formatted message to the transcript.
        Use simple prefixes and spacing to keep it readable.
        """
        self.chat_transcript.append(f"<b>{who}:</b>")
        # QTextEdit accepts HTML; escape is minimal here for demo
        self.chat_transcript.append(text)
        self.chat_transcript.append("<hr>")

    def _on_send_click(self) -> None:
        """
        Send text from input_box via orchestrator.
        Disabled in exam mode.
        """
        if self.exam_mode_enabled:
            QMessageBox.warning(self, "Exam Mode", "AI tutor is disabled in Exam Mode.")
            return

        text = self.input_box.toPlainText().strip()
        if not text:
            return
        # show user message
        self._append_transcript("You", text)
        self.input_box.clear()
        # Call orchestrator (mock-backed) and display reply
        res = self.orchestrator.handle_user_message(text)
        if res.allowed:
            # show sanitized response
            self._append_transcript("EduTutor", res.content)
        else:
            # refusal -> show content and highlight
            self._append_transcript("EduTutor (refusal)", res.content)

    def _send_with_hint(self, hint: str) -> None:
        """
        Convenience methods that add a small hint label to the input then send.
        Helps testing the classifier's response to user UI hints.
        """
        mapping = {"concept": " (hint:concept)", "error": " (hint:error)", "explain": " (hint:explain)"}
        current = self.input_box.toPlainText()
        self.input_box.setPlainText(current + mapping.get(hint, ""))

    def _on_explain_click(self) -> None:
        """
        Take the code from the right pane and ask the orchestrator to explain it.
        We send the code as user content but also preface it so the classifier
        can pick up it is an 'explain code' request.
        """
        if self.exam_mode_enabled:
            QMessageBox.warning(self, "Exam Mode", "AI tutor is disabled in Exam Mode.")
            return

        code = self.code_box.toPlainText().strip()
        if not code:
            QMessageBox.information(self, "Explain This", "Please paste code in the right pane first.")
            return

        # for the mock/orchestrator, include a hint phrase so classifier treats it as EXPLAIN_CODE
        prompt = f"explain this code:\n\n{code}"
        self._append_transcript("You (code)", "Posted code for explanation (see right pane)")
        res = self.orchestrator.handle_user_message(prompt)
        if res.allowed:
            self._append_transcript("EduTutor", res.content)
        else:
            self._append_transcript("EduTutor (refusal)", res.content)

    def _copy_code_to_input(self) -> None:
        """Convenience: copy the selected / whole code into the chat input."""
        text = self.code_box.toPlainText()
        self.input_box.setPlainText(text)

    def _toggle_exam_mode(self, checked: bool) -> None:
        """Toggle exam mode - disables send/explain and updates UI badges."""
        self.exam_mode_enabled = checked
        label = "ON" if checked else "OFF"
        self.exam_action.setText(f"Enable Exam Mode ({label})")
        self.send_btn.setEnabled(not checked)
        self.explain_btn.setEnabled(not checked)
        # update status bar
        self.status_label.setText(f"Provider: mock | Exam Mode: {label}")

    def _clear_transcript(self) -> None:
        """Clear the chat transcript for fresh testing."""
        self.chat_transcript.clear()

    def _save_code_to_file(self) -> None:
        """Save the right-hand code box to a file (convenience for QA)."""
        path, _ = QFileDialog.getSaveFileName(self, "Save Code", filter="*.py;;*.txt;;All Files (*)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.code_box.toPlainText())
            QMessageBox.information(self, "Saved", f"Code saved to {path}")
        except Exception as exc:  # noqa: BLE001 - demo-level catch
            QMessageBox.critical(self, "Error", f"Failed to save file: {exc}")

    def _load_code_from_file(self) -> None:
        """Load code into the right-hand editor from disk (useful for longer snippets)."""
        path, _ = QFileDialog.getOpenFileName(self, "Open Code", filter="*.py;;*.txt;;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                contents = fh.read()
            self.code_box.setPlainText(contents)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to open file: {exc}")


def main(argv: Optional[list[str]] = None) -> int:
    """
    Application entrypoint. Sets QT_API to pyside6 and runs the main window.
    """
    argv = argv or sys.argv
    os.environ.setdefault("QT_API", "pyside6")
    app = QApplication(argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
