import os
import sys

custom_temp = os.path.join(os.getcwd(), "my_temp")
os.makedirs(custom_temp, exist_ok=True)
os.environ["TEMP"] = custom_temp
os.environ["TMP"] = custom_temp

import shutil
import uuid
import time
from pathlib import Path
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QPlainTextEdit,
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QVBoxLayout, QFrame,
    QFileDialog, QMessageBox, QDialog, QSplitter, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QColor, QTextCursor, QTextCharFormat

from Functions import preprocess_and_syllabify, synthesize_speech
from db import populate_syllable_db, get_syllable_audio_path
from utils import resource_path


def safe_import(module_name, package_name=None):
    """Safely import optional dependencies"""
    try:
        if package_name:
            return __import__(module_name, fromlist=[package_name])
        return __import__(module_name)
    except ImportError:
        return None


pydub = safe_import('pydub')
PyPDF2 = safe_import('PyPDF2')
docx = safe_import('docx')

HAS_PYDUB = pydub is not None
HAS_PDF = PyPDF2 is not None
HAS_DOCX = docx is not None

# === Constants ===
DEFAULT_FONT_FAMILY = "Sylfaen"
DEFAULT_FONT_SIZE = 13
TITLE_FONT_FAMILY = "Segoe UI"
TITLE_FONT_SIZE = 19
TITLE_FONT_WEIGHT = QFont.Weight.Bold

INPUT_LABEL_FONT_FAMILY = TITLE_FONT_FAMILY
INPUT_LABEL_FONT_SIZE = 12
INPUT_LABEL_FONT_WEIGHT = QFont.Weight.DemiBold

STATUS_BAR_HEIGHT = 32
AUDIO_FILE_NAME = "georgian_audio.wav"
AUDIO_FORMAT = "wav"

SAMPLE_TEXT = """
საქართველო არის ქვეყანა კავკასიაში.
თბილისი არის საქართველოს დედაქალაქი.
ქართული ენა უნიკალურია.
"""

Georgian_Alphabet = ["აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"]

GEORGIAN_KEYBOARD_MAP = {
    'q': 'ქ', 'w': 'წ', 'e': 'ე', 'r': 'რ', 't': 'ტ', 'y': 'ყ',
    'u': 'უ', 'i': 'ი', 'o': 'ო', 'p': 'პ', 'a': 'ა', 's': 'ს',
    'd': 'დ', 'f': 'ფ', 'g': 'გ', 'h': 'ჰ', 'j': 'ჯ', 'k': 'კ',
    'l': 'ლ', 'z': 'ზ', 'x': 'ხ', 'c': 'ც', 'v': 'ვ', 'b': 'ბ',
    'n': 'ნ', 'm': 'მ'
}
GEORGIAN_KEYBOARD_MAP_SHIFT = {
    't': 'თ', 'w': 'ჭ', 'r': 'ღ', 'c': 'ჩ', 'j': 'ჟ'
}
GEORGIAN_KEYBOARD_LAYOUTS = {
    'normal': [
        ['ქ', 'წ', 'ე', 'რ', 'ტ', 'ყ', 'უ', 'ი', 'ო', 'პ'],
        ['ა', 'ს', 'დ', 'ფ', 'გ', 'ჰ', 'ჯ', 'კ', 'ლ'],
        ['ზ', 'ხ', 'ც', 'ვ', 'ბ', 'ნ', 'მ']
    ],
    'shift': [
        ['ქ', 'ჭ', 'ე', 'ღ', 'თ', 'ყ', 'უ', 'ი', 'ო', 'პ'],
        ['ა', 'შ', 'დ', 'ფ', 'გ', 'ჰ', 'ჯ', 'კ', 'ლ'],
        ['ზ', 'ხ', 'ჩ', 'ვ', 'ბ', 'ნ', 'მ']
    ]
}

STRINGS = {
    "title": "ქართული ტექსტიდან მეტყველებაში გარდაქმნა",
    "input_label": "ტექსტის შეყვანა",
    "georgian_mode": "ქართული რეჟიმი",
    "font": "ფონტი:",
    "file_ops": "ფაილის ოპერაციები",
    "load_file": "📂  ფაილის ატვირთვა",
    "clear_text": "🗑️  ტექსტის წაშლა",
    "input_tools": "ტექსტის ხელსაწყოები",
    "keyboard": "⌨️  კლავიატურა",
    "sample_text": "📝  ტექსტის ნიმუში",
    "audio_gen": "აუდიოს გენერაცია",
    "generate_audio": "🎵  აუდიოს გენერაცია",
    "play_audio": "▶️  აუდიოს დაკვრა",
    "save_audio": "💾  აუდიოს შენახვა",
    "missing_deps": "ვერ მოიძებნა დამატებითი პაკეტები:",
    "pydub_missing": "pydub არ არის დაინსტალირებული",
    "pdf_missing": "PyPDF2 არ არის დაინსტალირებული",
    "docx_missing": "python-docx არ არის დაინსტალირებული",
    "status_ready": "მზადაა",
    "status_georgian_on": "ქართული რეჟიმი: ჩართულია",
    "status_georgian_off": "ქართული რეჟიმი: გამორთულია",
    "status_font_changed": "ფონტი შეიცვალა: {font}",
    "status_loaded": "ჩაიტვირთა: {file}",
    "status_text_cleared": "ტექსტი წაშლილია",
    "status_sample_inserted": "ნიმუში ჩასმულია",
    "status_db": "⏳ მიმდინარეობს მარცვლების ბაზის მომზადება...",
    "status_preprocess": "🔍 წინასწარი დამუშავება...",
    "status_missing_syllables": "აკლია მარცვლები",
    "status_audio_gen": "🎛️ აუდიოს გენერაცია...",
    "status_audio_success": "✅ აუდიო წარმატებით შეიქმნა",
    "status_audio_error": "❌ შეცდომა აუდიოს გენერაციისას",
    "status_playing": "▶️ მიმდინარეობს დაკვრა...",
    "status_play_done": "დაკვრა დასრულდა",
    "status_play_error": "❌ დაკვრის შეცდომა",
    "status_audio_saved": "აუდიო შენახულია: {file}",
    "status_audio_saved_success": "აუდიო წარმატებით შენახულია",
    "status_permission_error": "წვდომა აკრძალულია: ფაილის შენახვა ვერ მოხერხდა. აირჩიეთ სხვა მდებარეობა.",
    "warning_no_text": "გთხოვთ, ჯერ შეიყვანოთ ტექსტი",
    "warning_invalid_char": "ტექსტი შეიცავს არაქართულ სიმბოლოს: „{char}“",
    "warning_generate_audio": "გთხოვთ, ჯერ დააგენერიროთ აუდიო",
    "warning_missing_syllables": "მონაცემთა ბაზაში არ მოიძებნა შემდეგი მარცვლები:\n{syllables}",
    "warning_clear_text": "გსურთ ტექსტის წაშლა?",
    "success": "წარმატება",
    "error": "შეცდომა",
    "missing_dependency": "აკლია დამატებითი პაკეტი",
    "info": "ინფორმაცია",
    "confirm": "დადასტურება",
    "save_audio_file": "აუდიო ფაილის შენახვა",
    "open_file": "ფაილის გახსნა",
    "wav_files": "WAV ფაილები (*.wav)",
    "all_files": "ყველა ფაილი (*)",
    "virtual_keyboard": "ქართული კლავიატურა",
    "shortcut_keyboard": "⌨️ კლავიატურა  (Ctrl+K)",
}

# === Visual theme (dark, only) ===================================
DARK_PALETTE = {
    "bg": "#15171f",
    "panel": "#1e2130",
    "border": "#2f3346",
    "text": "#e7e9f2",
    "muted": "#9096ab",
    "primary": "#5b7bff",
    "primary_hover": "#7089ff",
    "primary_text": "#ffffff",
    "accent": "#34d399",
    "danger": "#f87171",
    "input_bg": "#171923",
    "hover_bg": "#262a3d",
    "pressed_bg": "#2e3350",
    "indicator_off": "#3a3f55",
    "shadow_alpha": 90,
}


def build_stylesheet(p):
    """Build the app QSS from a palette dict (LIGHT_PALETTE or DARK_PALETTE)."""
    return f"""
QMainWindow {{
    background: {p['bg']};
}}
QWidget {{
    color: {p['text']};
    font-family: "Segoe UI", "Noto Sans Georgian", sans-serif;
}}
QFrame#card {{
    background: {p['panel']};
    border: 1px solid {p['border']};
    border-radius: 12px;
}}
QLabel#titleLabel {{
    color: {p['text']};
}}
QLabel#sectionLabel {{
    color: {p['muted']};
    letter-spacing: 0.5px;
}}
QPlainTextEdit {{
    background: {p['input_bg']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 10px;
    selection-background-color: {p['primary']};
}}
QPlainTextEdit:focus {{
    border: 1px solid {p['primary']};
}}
QPushButton {{
    background: {p['panel']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 8px 14px;
    text-align: left;
}}
QPushButton:hover {{
    background: {p['hover_bg']};
    border: 1px solid {p['primary']};
}}
QPushButton:pressed {{
    background: {p['pressed_bg']};
}}
QPushButton#primaryButton {{
    background: {p['primary']};
    color: {p['primary_text']};
    border: none;
    font-weight: 600;
    padding: 10px 16px;
    text-align: center;
}}
QPushButton#primaryButton:hover {{
    background: {p['primary_hover']};
}}
QPushButton#themeToggle {{
    text-align: center;
    padding: 6px 10px;
}}
QComboBox {{
    background: {p['input_bg']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 4px 8px;
}}
QComboBox QAbstractItemView {{
    background: {p['panel']};
    color: {p['text']};
    selection-background-color: {p['primary']};
    selection-color: {p['primary_text']};
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 34px;
    height: 18px;
    border-radius: 9px;
    background: {p['indicator_off']};
}}
QCheckBox::indicator:checked {{
    background: {p['primary']};
}}
QLabel#statusLabel {{
    background: {p['panel']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 0 12px;
}}
QLabel#statusLabel[state="error"] {{
    color: {p['danger']};
    border-color: {p['danger']};
}}
QLabel#statusLabel[state="ok"] {{
    color: {p['accent']};
    border-color: {p['accent']};
}}
QDialog {{
    background: {p['panel']};
    color: {p['text']};
}}
QMessageBox {{
    background: {p['panel']};
}}
"""


# Kept for any external code that imports PALETTE / STYLESHEET directly.
PALETTE = DARK_PALETTE
STYLESHEET = build_stylesheet(DARK_PALETTE)


def add_shadow(widget, alpha=30):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class GenerationWorker(QThread):
    """Runs syllable-DB prep + synthesis off the UI thread so the window never freezes."""
    stage = pyqtSignal(str)
    missing_syllables = pyqtSignal(set)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, text, audio_out_path):
        super().__init__()
        self.text = text
        self.audio_out_path = audio_out_path

    def run(self):
        try:
            self.stage.emit(STRINGS["status_db"])
            populate_syllable_db()

            self.stage.emit(STRINGS["status_preprocess"])
            syllables = preprocess_and_syllabify(self.text)

            missing = {
                syl for syl in syllables
                if syl not in ("<s>", "<eos>") and not get_syllable_audio_path(syl)
            }
            if missing:
                self.missing_syllables.emit(missing)
                return

            self.stage.emit(STRINGS["status_audio_gen"])
            audio = synthesize_speech(syllables)
            audio.export(self.audio_out_path, format=AUDIO_FORMAT)
            self.finished_ok.emit(self.audio_out_path)
        except Exception as e:
            import traceback
            self.failed.emit(f"{e}\n{traceback.format_exc()}")


class AudioWorker(QThread):
    """Worker thread for audio playback to prevent UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self, operation, audio_file=None):
        super().__init__()
        self.operation = operation
        self.audio_file = audio_file

    def run(self):
        try:
            if self.operation == 'play' and self.audio_file:
                self._play_audio()
            self.finished.emit(True, "Operation completed successfully")
        except Exception as e:
            import traceback
            self.finished.emit(False, f"{e}\n{traceback.format_exc()}")

    def _play_audio(self):
        self.progress.emit(STRINGS["status_playing"])
        try:
            if sys.platform == "win32":
                subprocess.run(f'start "" "{self.audio_file}"', shell=True)
            else:
                subprocess.run(f'aplay "{self.audio_file}"', shell=True)
        except Exception as e:
            import traceback
            self.finished.emit(False, f"Audio playback error for file {self.audio_file}: {e}\n{traceback.format_exc()}")


class GeorgianTextEdit(QPlainTextEdit):
    """Custom text edit with Georgian input and context menu"""

    def __init__(self):
        super().__init__()
        self.setFont(QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setUndoRedoEnabled(True)
        self.georgian_mode = False
        self.georgian_map = GEORGIAN_KEYBOARD_MAP
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setPlaceholderText("დაწერეთ ან ჩასვით ქართული ტექსტი აქ…")

    def toggle_georgian(self):
        self.georgian_mode = not self.georgian_mode
        return self.georgian_mode

    def set_font(self, font_family, size=DEFAULT_FONT_SIZE):
        self.setFont(QFont(font_family, size))

    def keyPressEvent(self, event):
        if self.georgian_mode and event.text():
            key = event.text().lower()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                if key in GEORGIAN_KEYBOARD_MAP_SHIFT:
                    self.textCursor().insertText(GEORGIAN_KEYBOARD_MAP_SHIFT[key])
                    return
            elif key in self.georgian_map:
                self.textCursor().insertText(self.georgian_map[key])
                return
        super().keyPressEvent(event)

    def show_context_menu(self, pos):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        toggle_text = "Disable Georgian" if self.georgian_mode else "Enable Georgian"
        toggle_action = QAction(toggle_text, self)
        toggle_action.triggered.connect(self.toggle_georgian)
        menu.addAction(toggle_action)
        menu.exec(self.mapToGlobal(pos))


class GeorgianKeyboardDialog(QDialog):
    """Virtual Georgian Keyboard Dialog"""

    def __init__(self, parent, text_edit):
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle(STRINGS["virtual_keyboard"])
        self.setMinimumSize(620, 220)
        self.shift_on = False
        self.buttons = []
        self.layouts = GEORGIAN_KEYBOARD_LAYOUTS
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)

        current_layout = self.layouts['normal']
        for row_chars in current_layout:
            row_layout = QHBoxLayout()
            row_layout.addStretch()
            button_row = []
            for char in row_chars:
                btn = QPushButton(char)
                btn.setFont(QFont("Sylfaen", 14))
                btn.setFixedSize(42, 42)
                btn.setStyleSheet("text-align:center;")
                btn.clicked.connect(lambda checked, c=char: self.insert_char(c))
                row_layout.addWidget(btn)
                button_row.append(btn)
            row_layout.addStretch()
            self.buttons.append(button_row)
            main_layout.addLayout(row_layout)

        self.create_bottom_controls(main_layout)

    def create_bottom_controls(self, main_layout):
        bottom_layout = QHBoxLayout()

        self.shift_btn = QPushButton("Shift")
        self.shift_btn.setFixedSize(64, 32)
        self.shift_btn.clicked.connect(self.toggle_shift)
        bottom_layout.addWidget(self.shift_btn)

        space_btn = QPushButton("Space")
        space_btn.setFixedSize(80, 32)
        space_btn.clicked.connect(lambda: self.insert_char(' '))
        bottom_layout.addWidget(space_btn)

        for char in ['.', ',', '!', '?', ';', ':', '-', '(', ')']:
            btn = QPushButton(char)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("text-align:center;")
            btn.clicked.connect(lambda checked, c=char: self.insert_char(c))
            bottom_layout.addWidget(btn)

        enter_btn = QPushButton("Enter")
        enter_btn.setFixedSize(64, 32)
        enter_btn.clicked.connect(lambda: self.insert_char('\n'))
        bottom_layout.addWidget(enter_btn)

        main_layout.addLayout(bottom_layout)

    def insert_char(self, char):
        cursor = self.text_edit.textCursor()
        cursor.insertText(char)
        self.text_edit.setFocus()

    def toggle_shift(self):
        self.shift_on = not self.shift_on
        self.update_keyboard_layout()

    def update_keyboard_layout(self):
        layout_name = 'shift' if self.shift_on else 'normal'
        current_layout = self.layouts[layout_name]
        for row_idx, row_chars in enumerate(current_layout):
            for col_idx, char in enumerate(row_chars):
                if row_idx < len(self.buttons) and col_idx < len(self.buttons[row_idx]):
                    btn = self.buttons[row_idx][col_idx]
                    btn.setText(char)
                    btn.clicked.disconnect()
                    btn.clicked.connect(lambda checked, c=char: self.insert_char(c))


class ModernGeorgianTTS(QMainWindow):
    """Main application window for Georgian TTS"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Georgian TTS · ქართული TTS")
        self.resize(1080, 720)
        self.setMinimumSize(860, 600)

        self.audio_file = os.path.join(os.getcwd(), f"georgian_tts_{uuid.uuid4().hex}.wav")
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
        """state: normal | ok | error -- drives the status pill color"""
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
        except ValueError as ve:
            QMessageBox.critical(self, STRINGS["error"], f"ფაილის ჩატვირთვა ვერ მოხერხდა:\n{ve}")
        except ImportError as ie:
            QMessageBox.critical(self, STRINGS["missing_dependency"], f"{ie}\nდააინსტალირეთ საჭირო პაკეტი.")
        except Exception as e:
            QMessageBox.critical(self, STRINGS["error"], f"ფაილის ჩატვირთვა ვერ მოხერხდა:\n{e}")

    def read_file_content(self, file_path):
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Could not read text file: {e}")

        elif file_ext == '.pdf':
            if not HAS_PDF or PyPDF2 is None:
                raise ImportError("PyPDF2 is required to open PDF files.")
            try:
                reader = PyPDF2.PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                raise ValueError(f"Could not read PDF file: {e}")

        elif file_ext == '.docx':
            if not HAS_DOCX or docx is None:
                raise ImportError("python-docx is required to open DOCX files.")
            try:
                doc = docx.Document(file_path)
                return "\n".join(para.text for para in doc.paragraphs)
            except Exception as e:
                raise ValueError(f"Could not read DOCX file: {e}")

        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

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
            QMessageBox.warning(self, STRINGS["warning_no_text"], STRINGS["warning_no_text"])
            return

        for char in text:
            if char.isalpha() and char not in Georgian_Alphabet[0]:
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
            QMessageBox.warning(self, STRINGS["warning_generate_audio"], STRINGS["warning_generate_audio"])
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
            QMessageBox.warning(self, STRINGS["warning_generate_audio"], STRINGS["warning_generate_audio"])
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
        for attempt in range(max_retries):
            try:
                os.makedirs(os.path.dirname(destination), exist_ok=True)
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
                worker.terminate()
                worker.wait()
        if os.path.exists(self.audio_file):
            try:
                os.remove(self.audio_file)
            except OSError:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = ModernGeorgianTTS()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()