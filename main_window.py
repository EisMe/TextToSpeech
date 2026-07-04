"""The main application window.

This module owns Qt layout construction and event wiring. It intentionally
does not own: string content (strings.py), visual theme (theme.py),
background work (workers.py), or optional-dependency detection
(optional_deps.py) -- it imports and orchestrates those instead.
"""
import logging
import os
import shutil
import time
import uuid
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QLabel, QPushButton, QCheckBox, QComboBox,
    QHBoxLayout, QVBoxLayout, QFrame, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont

from app_config import AUDIO_FILE_NAME
from strings import STRINGS, SAMPLE_TEXT, GEORGIAN_ALPHABET
from theme import (
    PALETTE, DARK_PALETTE, add_shadow,
    DEFAULT_FONT_FAMILY, TITLE_FONT_FAMILY, TITLE_FONT_SIZE, TITLE_FONT_WEIGHT,
    INPUT_LABEL_FONT_FAMILY, INPUT_LABEL_FONT_SIZE, INPUT_LABEL_FONT_WEIGHT,
    STATUS_BAR_HEIGHT,
)
from optional_deps import HAS_PYDUB, HAS_PDF, HAS_DOCX, PyPDF2, docx
from workers import GenerationWorker, AudioWorker
from widgets import GeorgianTextEdit, GeorgianKeyboardDialog

logger = logging.getLogger(__name__)


class ModernGeorgianTTS(QMainWindow):
    """Main application window for Georgian TTS."""

    def __init__(self, temp_dir: str):
        super().__init__()
        self.setWindowTitle("Georgian TTS · ქართული TTS")
        self.resize(1080, 720)
        self.setMinimumSize(860, 600)

        self.audio_file = os.path.join(temp_dir, f"georgian_tts_{uuid.uuid4().hex}.wav")
        self.audio_worker = None
        self.gen_worker = None
        self._card_frames = []

        self.init_ui()

    # ---------- layout ----------

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(14)

        outer_layout.addWidget(self.create_title_label())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        left_panel = self.create_text_input_panel()
        right_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([650, 380])
        outer_layout.addWidget(splitter, 1)

        self.status_label = self.create_status_bar()
        outer_layout.addWidget(self.status_label)

    def create_title_label(self):
        label = QLabel(STRINGS["title"])
        label.setObjectName("titleLabel")
        label.setFont(QFont(TITLE_FONT_FAMILY, TITLE_FONT_SIZE, TITLE_FONT_WEIGHT))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_status_bar(self):
        label = QLabel(STRINGS["status_ready"])
        label.setObjectName("statusLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(STATUS_BAR_HEIGHT)
        return label

    def set_status(self, text, state="normal"):
        """state: normal | ok | error -- drives the status pill color."""
        self.status_label.setText(text)
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def create_text_input_panel(self):
        frame = QFrame()
        frame.setObjectName("card")
        add_shadow(frame, alpha=DARK_PALETTE['shadow_alpha'])
        self._card_frames.append(frame)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self.create_input_label())

        self.text_edit = self.create_text_editor()
        layout.addWidget(self.text_edit, 1)

        layout.addLayout(self.create_controls_layout())
        return frame

    def create_input_label(self):
        label = QLabel(STRINGS["input_label"])
        label.setFont(QFont(INPUT_LABEL_FONT_FAMILY, INPUT_LABEL_FONT_SIZE, INPUT_LABEL_FONT_WEIGHT))
        return label

    def create_text_editor(self):
        return GeorgianTextEdit()

    def create_controls_layout(self):
        controls_layout = QHBoxLayout()

        self.mode_checkbox = QCheckBox(STRINGS["georgian_mode"])
        self.mode_checkbox.stateChanged.connect(self.toggle_georgian_mode)
        controls_layout.addWidget(self.mode_checkbox)

        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel(STRINGS["font"]))

        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Sylfaen", "BPG Arial", "BPG Nino Mtavruli",
            "DejaVu Sans", "Arial Unicode MS", "Noto Sans Georgian"
        ])
        self.font_combo.currentTextChanged.connect(self.change_font)
        self.font_combo.setFixedWidth(160)
        controls_layout.addWidget(self.font_combo)

        controls_layout.addStretch()

        shortcut_label = QLabel(STRINGS["shortcut_keyboard"])
        shortcut_label.setObjectName("sectionLabel")
        shortcut_label.setStyleSheet("font-size: 11px;")
        controls_layout.addWidget(shortcut_label)

        self.text_edit.shortcut_keyboard = QAction(self)
        self.text_edit.shortcut_keyboard.setShortcut("Ctrl+K")
        self.text_edit.shortcut_keyboard.triggered.connect(self.show_keyboard)
        self.addAction(self.text_edit.shortcut_keyboard)

        return controls_layout

    def create_control_panel(self):
        frame = QFrame()
        frame.setObjectName("card")
        add_shadow(frame, alpha=DARK_PALETTE['shadow_alpha'])
        self._card_frames.append(frame)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        self.add_section(layout, STRINGS["file_ops"], [
            (STRINGS["load_file"], self.load_file),
            (STRINGS["clear_text"], self.clear_text)
        ])
        layout.addSpacing(18)

        self.add_section(layout, STRINGS["input_tools"], [
            (STRINGS["keyboard"], self.show_keyboard),
            (STRINGS["sample_text"], self.insert_sample)
        ])
        layout.addSpacing(18)

        # Audio section — generate button is the visual primary action
        label = self.create_section_label(STRINGS["audio_gen"])
        layout.addWidget(label)

        gen_btn = QPushButton(STRINGS["generate_audio"])
        gen_btn.setObjectName("primaryButton")
        gen_btn.setMinimumHeight(40)
        gen_btn.clicked.connect(self.generate_audio)
        layout.addWidget(gen_btn)
        self.generate_button = gen_btn

        secondary_row = QHBoxLayout()
        if HAS_PYDUB:
            play_btn = QPushButton(STRINGS["play_audio"])
            play_btn.clicked.connect(self.play_audio)
            secondary_row.addWidget(play_btn)
        save_btn = QPushButton(STRINGS["save_audio"])
        save_btn.clicked.connect(self.save_audio)
        secondary_row.addWidget(save_btn)
        layout.addLayout(secondary_row)

        self.add_missing_deps_info(layout)
        layout.addStretch()
        return frame

    def add_section(self, parent_layout, title, buttons):
        label = self.create_section_label(title)
        parent_layout.addWidget(label)
        parent_layout.addLayout(self.create_button_layout(buttons))

    def create_section_label(self, title):
        label = QLabel(title.upper())
        label.setObjectName("sectionLabel")
        label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        return label

    def create_button_layout(self, buttons):
        button_layout = QVBoxLayout()
        button_layout.setSpacing(6)
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(34)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        return button_layout

    def add_missing_deps_info(self, layout):
        missing_deps = []
        if not HAS_PYDUB:
            missing_deps.append(STRINGS["pydub_missing"])
        if not HAS_PDF:
            missing_deps.append(STRINGS["pdf_missing"])
        if not HAS_DOCX:
            missing_deps.append(STRINGS["docx_missing"])

        if missing_deps:
            layout.addSpacing(18)
            deps_label = QLabel(STRINGS["missing_deps"])
            deps_label.setStyleSheet(f"color:{PALETTE['danger']}; font-weight:600; font-size:11px;")
            layout.addWidget(deps_label)
            for dep in missing_deps:
                dep_label = QLabel(f"• {dep}")
                dep_label.setStyleSheet(f"color:{PALETTE['danger']}; font-size:10px;")
                layout.addWidget(dep_label)

    # ---------- behaviour ----------

    def toggle_georgian_mode(self, state):
        mode = self.text_edit.toggle_georgian()
        self.set_status(STRINGS["status_georgian_on"] if mode else STRINGS["status_georgian_off"])

    def change_font(self, font_name):
        self.text_edit.set_font(font_name)
        self.set_status(STRINGS["status_font_changed"].format(font=font_name))

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, STRINGS["open_file"], "", STRINGS["all_files"]
        )
        if not file_path:
            return
        try:
            content = self.read_file_content(file_path)
            self.text_edit.setPlainText(content)
            self.set_status(STRINGS["status_loaded"].format(file=os.path.basename(file_path)), "ok")
        except ImportError as ie:
            QMessageBox.critical(
                self, STRINGS["missing_dependency"],
                f"{ie}\n{STRINGS['install_required_package']}"
            )
        except Exception as e:
            logger.exception("Failed to load file: %s", file_path)
            QMessageBox.critical(self, STRINGS["error"], STRINGS["could_not_load_file"].format(err=e))

    def read_file_content(self, file_path):
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(STRINGS["file_read_error_txt"].format(err=e))

        elif file_ext == '.pdf':
            if not HAS_PDF or PyPDF2 is None:
                raise ImportError(STRINGS["pdf_required"])
            try:
                reader = PyPDF2.PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                raise ValueError(STRINGS["file_read_error_pdf"].format(err=e))

        elif file_ext == '.docx':
            if not HAS_DOCX or docx is None:
                raise ImportError(STRINGS["docx_required"])
            try:
                doc = docx.Document(file_path)
                return "\n".join(para.text for para in doc.paragraphs)
            except Exception as e:
                raise ValueError(STRINGS["file_read_error_docx"].format(err=e))

        else:
            raise ValueError(STRINGS["unsupported_format"].format(ext=file_ext))

    def clear_text(self):
        reply = QMessageBox.question(
            self, STRINGS["confirm"], STRINGS["warning_clear_text"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.text_edit.clear()
            self.set_status(STRINGS["status_text_cleared"])

    def show_keyboard(self):
        keyboard_dialog = GeorgianKeyboardDialog(self, self.text_edit)
        keyboard_dialog.exec()

    def insert_sample(self):
        self.text_edit.insertPlainText(SAMPLE_TEXT)
        self.set_status(STRINGS["status_sample_inserted"])

    def generate_audio(self):
        """Validate input, then hand generation off to a background thread."""
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, STRINGS["warning"], STRINGS["warning_no_text"])
            return

        for char in text:
            if char.isalpha() and char not in GEORGIAN_ALPHABET:
                QMessageBox.warning(
                    self, STRINGS["error"],
                    STRINGS["warning_invalid_char"].format(char=char)
                )
                return

        self.generate_button.setEnabled(False)
        self.generate_button.setText("⏳  მუშავდება…")

        self.gen_worker = GenerationWorker(text, self.audio_file)
        self.gen_worker.stage.connect(lambda msg: self.set_status(msg))
        self.gen_worker.missing_syllables.connect(self.on_missing_syllables)
        self.gen_worker.finished_ok.connect(self.on_generation_success)
        self.gen_worker.failed.connect(self.on_generation_failed)
        self.gen_worker.start()

    def _reset_generate_button(self):
        self.generate_button.setEnabled(True)
        self.generate_button.setText(STRINGS["generate_audio"])

    def on_missing_syllables(self, missing):
        self._reset_generate_button()
        missing_str = ", ".join(sorted(missing))
        self.set_status(STRINGS["status_missing_syllables"], "error")
        QMessageBox.warning(
            self, STRINGS["status_missing_syllables"],
            STRINGS["warning_missing_syllables"].format(syllables=missing_str)
        )

    def on_generation_success(self, audio_path):
        self._reset_generate_button()
        self.set_status(STRINGS["status_audio_success"], "ok")
        QMessageBox.information(self, STRINGS["success"], STRINGS["status_audio_success"])

    def on_generation_failed(self, message):
        self._reset_generate_button()
        self.set_status(STRINGS["status_audio_error"], "error")
        QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_audio_error']}\n{message}")

    def play_audio(self):
        if not os.path.exists(self.audio_file):
            QMessageBox.warning(self, STRINGS["warning"], STRINGS["warning_generate_audio"])
            return
        if self.audio_worker and self.audio_worker.isRunning():
            QMessageBox.information(self, STRINGS["info"], STRINGS["status_playing"])
            return

        self.audio_worker = AudioWorker('play', self.audio_file)
        self.audio_worker.finished.connect(self.on_audio_finished)
        self.audio_worker.progress.connect(lambda msg: self.set_status(msg))
        self.set_status(STRINGS["status_playing"])
        self.audio_worker.start()

    def on_audio_finished(self, success, message):
        if success:
            self.set_status(STRINGS["status_play_done"], "ok")
        else:
            self.set_status(STRINGS["status_play_error"], "error")
            QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_play_error']}\n{message}")

    def save_audio(self):
        if not os.path.exists(self.audio_file):
            QMessageBox.warning(self, STRINGS["warning"], STRINGS["warning_generate_audio"])
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, STRINGS["save_audio_file"], AUDIO_FILE_NAME, STRINGS["wav_files"]
        )
        if not file_path:
            return

        try:
            self.copy_file_safely(self.audio_file, file_path)
            filename = os.path.basename(file_path)
            self.set_status(STRINGS["status_audio_saved"].format(file=filename), "ok")
            QMessageBox.information(self, STRINGS["success"], STRINGS["status_audio_saved_success"])
        except PermissionError:
            QMessageBox.critical(self, STRINGS["error"], STRINGS["status_permission_error"])
        except Exception as e:
            QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_audio_saved']}\n{e}")

    def copy_file_safely(self, source, destination):
        max_retries = 3
        retry_delay = 0.1
        dest_dir = os.path.dirname(destination)
        for attempt in range(max_retries):
            try:
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(source, destination)
                return
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e

    def closeEvent(self, event):
        for worker in (self.audio_worker, self.gen_worker):
            if worker and worker.isRunning():
                # Give the worker a moment to finish cleanly. terminate() is
                # avoided since it can kill mid-write (WAV export) or
                # mid-subprocess (playback) and leave things in a bad state.
                if not worker.wait(3000):
                    logger.warning("%s did not finish within timeout on close", worker)
        if os.path.exists(self.audio_file):
            try:
                os.remove(self.audio_file)
            except OSError:
                pass
        event.accept()