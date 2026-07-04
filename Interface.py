"""Entry point for the Georgian TTS desktop application.

Run this file directly (`python Interface.py`) to launch the GUI.
All implementation lives in the sibling modules -- this file only wires
them together:

    strings.py        Localized UI text, Georgian alphabet/keyboard data
    theme.py           Fonts, color palette, QSS stylesheet builder
    optional_deps.py   Optional third-party dependency detection
    app_config.py      App-wide constants + temp-directory setup
    workers.py         Background QThread workers (generation, playback)
    widgets.py         Reusable custom widgets (text editor, virtual keyboard)
    main_window.py     The main window: layout + event wiring
"""
import logging
import sys

from PyQt6.QtWidgets import QApplication

from app_config import setup_temp_dir
from theme import STYLESHEET
from main_window import ModernGeorgianTTS


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    temp_dir = setup_temp_dir()

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = ModernGeorgianTTS(temp_dir)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()