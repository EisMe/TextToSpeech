"""Fonts, colors, and the QSS stylesheet.

The app currently ships one theme (dark). It's still expressed as a palette
dict + a builder function, rather than a hardcoded stylesheet string, so that
adding a second theme later is a data change (a new dict) rather than a
rewrite of every widget's styling.
"""
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# === Fonts ===
DEFAULT_FONT_FAMILY = "Sylfaen"
DEFAULT_FONT_SIZE = 13
TITLE_FONT_FAMILY = "Segoe UI"
TITLE_FONT_SIZE = 19
TITLE_FONT_WEIGHT = QFont.Weight.Bold

INPUT_LABEL_FONT_FAMILY = TITLE_FONT_FAMILY
INPUT_LABEL_FONT_SIZE = 12
INPUT_LABEL_FONT_WEIGHT = QFont.Weight.DemiBold

STATUS_BAR_HEIGHT = 32

# === Palette (dark, only) ===
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
    """Build the app's QSS from a palette dict."""
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


PALETTE = DARK_PALETTE
STYLESHEET = build_stylesheet(DARK_PALETTE)


def add_shadow(widget, alpha=DARK_PALETTE["shadow_alpha"]):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)