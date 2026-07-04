"""Custom widgets: a Georgian-input-aware text editor and a virtual keyboard dialog.

Kept separate from main_window.py because neither widget depends on the main
window's layout or business logic -- they only need Qt and the Georgian
string/keyboard data.
"""
from PyQt6.QtWidgets import QPlainTextEdit, QDialog, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont

from strings import (
    STRINGS, GEORGIAN_KEYBOARD_MAP, GEORGIAN_KEYBOARD_MAP_SHIFT, GEORGIAN_KEYBOARD_LAYOUTS
)
from theme import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE


class GeorgianTextEdit(QPlainTextEdit):
    """Text editor with a Latin->Georgian phonetic input mode and a context-menu toggle."""

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
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and key in GEORGIAN_KEYBOARD_MAP_SHIFT:
                self.textCursor().insertText(GEORGIAN_KEYBOARD_MAP_SHIFT[key])
                return
            elif key in self.georgian_map:
                self.textCursor().insertText(self.georgian_map[key])
                return
        super().keyPressEvent(event)

    def show_context_menu(self, pos):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        toggle_text = STRINGS["context_disable_georgian"] if self.georgian_mode else STRINGS["context_enable_georgian"]
        toggle_action = QAction(toggle_text, self)
        toggle_action.triggered.connect(self.toggle_georgian)
        menu.addAction(toggle_action)
        menu.exec(self.mapToGlobal(pos))


class GeorgianKeyboardDialog(QDialog):
    """On-screen virtual Georgian keyboard."""

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