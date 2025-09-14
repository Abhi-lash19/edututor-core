from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Standard / third-party imports
from PySide6.QtCore import Qt as _Qt
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# Local imports (must be after third-party imports but still at module top)
from edututor.core.orchestrator import Orchestrator

# Optional imports: Intent enum and classify_intent helper (may be absent in some versions)
try:
    from edututor.core.classifiers import Intent, classify_intent  # type: ignore
except Exception:  # pragma: no cover - optional import
    Intent = None  # type: ignore
    try:
        from edututor.core.classifiers import classify_intent  # type: ignore
    except Exception:
        classify_intent = None  # type: ignore

# Tell mypy/linters to treat Qt as Any for attribute access like Qt.Horizontal
Qt: Any = _Qt


# Toggle debug messages (prints debug info into transcript)
DEBUG_MODE = False

APP_NAME = "EduTutor"


def resource_path(name: str) -> Path:
    """Return path to an asset inside the repo's assets/ folder."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "assets" / name


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # backend
        self.orchestrator = Orchestrator()
        self.exam_mode_enabled = False

        # build UI
        self._build_toolbar()
        self._build_central_widget()
        self._build_status_bar()

        # Window sizing
        self.resize(1100, 720)

        # Keyboard shortcut Ctrl+Enter => send
        send_shortcut = QAction("Send (Ctrl+Enter)", self)
        send_shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        send_shortcut.triggered.connect(self._on_send_click)  # type: ignore[arg-type]
        self.addAction(send_shortcut)

        # initial status update
        self._update_status_provider()

    # UI builders
    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Exam mode toggle
        self.exam_action = QAction("Enable Exam Mode (OFF)", self)
        self.exam_action.setCheckable(True)
        self.exam_action.triggered.connect(self._toggle_exam_mode)
        tb.addAction(self.exam_action)

        # Clear transcript
        clear_action = QAction("Clear Transcript", self)
        clear_action.triggered.connect(self._clear_transcript)
        tb.addAction(clear_action)

        # Save / Load code
        save_code_action = QAction("Save Code...", self)
        save_code_action.triggered.connect(self._save_code_to_file)
        tb.addAction(save_code_action)

        load_code_action = QAction("Load Code...", self)
        load_code_action.triggered.connect(self._load_code_from_file)
        tb.addAction(load_code_action)

        # Debug toggle
        self.debug_action = QAction("Debug (OFF)", self)
        self.debug_action.setCheckable(True)
        self.debug_action.triggered.connect(self._toggle_debug_mode)
        tb.addAction(self.debug_action)

    def _build_central_widget(self) -> None:
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)

        # LEFT: chat
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(4, 4, 4, 4)

        self.chat_transcript = QTextEdit()
        self.chat_transcript.setReadOnly(True)
        self.chat_transcript.setPlaceholderText("Transcript will appear here...")
        left_layout.addWidget(self.chat_transcript, stretch=7)

        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(120)
        self.input_box.setPlaceholderText(
            "Ask a question (e.g. 'explain recursion' or paste an error)..."
        )
        left_layout.addWidget(self.input_box, stretch=1)

        bottom_row = QWidget()
        br_layout = QHBoxLayout(bottom_row)
        br_layout.setContentsMargins(0, 0, 0, 0)

        self.send_btn = QPushButton("Send ▶")
        self.send_btn.clicked.connect(self._on_send_click)
        br_layout.addWidget(self.send_btn)

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

        # RIGHT: code editor
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 4, 4, 4)

        right_layout.addWidget(QLabel("Code / Snippet (paste here and click Explain This):"))

        self.code_box = QPlainTextEdit()
        monospace = QFont("Consolas" if os.name == "nt" else "Courier")
        monospace.setPointSize(11)
        self.code_box.setFont(monospace)
        self.code_box.setPlaceholderText(
            "# Paste code here to ask 'Explain This' (no edits will be made)"
        )
        right_layout.addWidget(self.code_box, stretch=7)

        code_btn_row = QWidget()
        cbr = QHBoxLayout(code_btn_row)
        cbr.setContentsMargins(0, 0, 0, 0)

        self.explain_btn = QPushButton("Explain This ▶")
        self.explain_btn.clicked.connect(self._on_explain_click)
        cbr.addWidget(self.explain_btn)

        copy_to_input = QPushButton("Copy to Input")
        copy_to_input.clicked.connect(self._copy_code_to_input)
        cbr.addWidget(copy_to_input)

        right_layout.addWidget(code_btn_row, stretch=0)
        splitter.addWidget(right_container)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel("Provider: mock | Exam Mode: OFF")
        sb.addWidget(self.status_label)

    # -------------------------
    # UI handlers
    # -------------------------
    def _append_transcript(self, who: str, text: str) -> None:
        """Append a formatted, HTML-escaped message to the transcript."""
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Use small HTML blocks for readability
        self.chat_transcript.append(f"<b>{who}:</b>")
        self.chat_transcript.append(safe_text)
        self.chat_transcript.append("<hr>")

    def _on_send_click(self) -> None:
        if self.exam_mode_enabled:
            QMessageBox.warning(self, "Exam Mode", "AI tutor is disabled in Exam Mode.")
            return

        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self._append_transcript("You", text)
        self.input_box.clear()

        try:
            res = self.orchestrator.handle_user_message(text)
        except Exception as exc:
            self._append_transcript("System", f"Error calling orchestrator: {exc}")
            return

        out_text = self._coerce_res_text(res)
        self._append_transcript("EduTutor", out_text)

    def _send_with_hint(self, hint: str) -> None:
        """
        Send the current input with a hint.
        Tries to use Intent enum if available; otherwise prefixes the prompt.
        """
        if self.exam_mode_enabled:
            QMessageBox.warning(self, "Exam Mode", "AI tutor is disabled in Exam Mode.")
            return

        text = self.input_box.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Input required", "Please type a question first.")
            return

        self._append_transcript("You", text + f" (hint={hint})")

        hint_candidates = {
            "concept": ["CONCEPT", "CONCEPT_EXPLAIN", "EXPLAIN_CONCEPT"],
            "error": ["ERROR", "EXPLAIN_ERROR"],
            "explain": ["CODE", "EXPLAIN_CODE", "EXPLAIN"],
        }

        chosen_enum = None
        if Intent is not None:
            for candidate in hint_candidates.get(hint, []):
                if hasattr(Intent, candidate):
                    chosen_enum = getattr(Intent, candidate)
                    break

        try:
            if chosen_enum is not None:
                if DEBUG_MODE and classify_intent:
                    cls_res = classify_intent(text, user_hint=chosen_enum)
                    self._append_transcript("DEBUG", f"classify_intent -> {cls_res}")
                res = self.orchestrator.handle_user_message(text, user_hint=chosen_enum)
            else:
                fallback_prompt = f"({hint}) {text}"
                if DEBUG_MODE and classify_intent:
                    cls_res = classify_intent(fallback_prompt)
                    self._append_transcript("DEBUG", f"classify_intent (fallback) -> {cls_res}")
                res = self.orchestrator.handle_user_message(fallback_prompt)
        except Exception as exc:
            self._append_transcript("System", f"Error calling orchestrator: {exc}")
            return

        out_text = self._coerce_res_text(res)
        self._append_transcript("EduTutor", out_text)

        if DEBUG_MODE:
            self._append_transcript("DEBUG", f"orchestrator returned: {repr(res)}")

        self.input_box.clear()

    def _on_explain_click(self) -> None:
        if self.exam_mode_enabled:
            QMessageBox.warning(self, "Exam Mode", "AI tutor is disabled in Exam Mode.")
            return

        code = self.code_box.toPlainText().strip()
        if not code:
            QMessageBox.information(
                self, "Explain This", "Please paste code in the right pane first."
            )
            return

        chosen_enum = None
        if Intent is not None:
            for cand in ("CODE", "EXPLAIN_CODE", "CODE_EXPLAIN", "EXPLAIN"):
                if hasattr(Intent, cand):
                    chosen_enum = getattr(Intent, cand)
                    break

        try:
            if chosen_enum is not None:
                if DEBUG_MODE and classify_intent:
                    self._append_transcript("DEBUG", f"Sending code with user_hint={chosen_enum}")
                res = self.orchestrator.handle_user_message(code, user_hint=chosen_enum)
            else:
                prompt = f"explain this code:\n\n{code}"
                if DEBUG_MODE and classify_intent:
                    self._append_transcript("DEBUG", "Sending code with fallback prompt prefix")
                res = self.orchestrator.handle_user_message(prompt)
        except Exception as exc:
            self._append_transcript("System", f"Error calling orchestrator: {exc}")
            return

        self._append_transcript("You (code)", "Posted code for explanation (see right pane)")
        out_text = self._coerce_res_text(res)
        self._append_transcript("EduTutor", out_text)

        if DEBUG_MODE:
            self._append_transcript("DEBUG", f"orchestrator returned: {repr(res)}")

    def _copy_code_to_input(self) -> None:
        self.input_box.setPlainText(self.code_box.toPlainText())

    def _toggle_exam_mode(self, checked: bool) -> None:
        self.exam_mode_enabled = checked
        label = "ON" if checked else "OFF"
        self.exam_action.setText(f"Enable Exam Mode ({label})")
        self.send_btn.setEnabled(not checked)
        self.explain_btn.setEnabled(not checked)
        self.status_label.setText(f"Provider: {self._provider_name()} | Exam Mode: {label}")

    def _clear_transcript(self) -> None:
        """Clear the chat transcript for fresh testing."""
        self.chat_transcript.clear()

    def _save_code_to_file(self) -> None:
        """Save the right-hand code box to a file (convenience for QA)."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Code", filter="*.py;;*.txt;;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.code_box.toPlainText())
            QMessageBox.information(self, "Saved", f"Code saved to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save file: {exc}")

    def _load_code_from_file(self) -> None:
        """Load code into the right-hand editor from disk (useful for longer snippets)."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Code", filter="*.py;;*.txt;;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                contents = fh.read()
            self.code_box.setPlainText(contents)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to open file: {exc}")

    def _provider_name(self) -> str:
        try:
            return type(self.orchestrator.provider).__name__
        except Exception:
            return "unknown"

    def _update_status_provider(self) -> None:
        exam_mode_status = "ON" if self.exam_mode_enabled else "OFF"
        self.status_label.setText(
            f"Provider: {self._provider_name()} | Exam Mode: {exam_mode_status}"
        )

    def _toggle_debug_mode(self, checked: bool) -> None:
        global DEBUG_MODE
        DEBUG_MODE = checked
        self.debug_action.setText(f"Debug ({'ON' if checked else 'OFF'})")
        self._append_transcript("System", f"Debug mode {'enabled' if checked else 'disabled'}")

    def _coerce_res_text(self, res: Any) -> str:
        """
        Normalize the possible shapes of an orchestrator result into a text string.
        Supports objects with .text, .content, dicts with keys, or fallback str().
        """
        if res is None:
            return ""
        if hasattr(res, "text"):
            return getattr(res, "text") or ""
        if hasattr(res, "content"):
            return getattr(res, "content") or ""
        if isinstance(res, dict):
            return res.get("text") or res.get("content") or ""
        return str(res)


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
