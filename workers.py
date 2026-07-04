"""Background workers that keep the GUI thread responsive.

GenerationWorker runs syllable-DB preparation and speech synthesis off the
main thread. AudioWorker runs playback off the main thread. Both only emit
short, already-localized strings back to the UI; full tracebacks are logged
here, never surfaced directly to the user (see module logger).
"""
import logging
import os
import subprocess
import sys

from PyQt6.QtCore import QThread, pyqtSignal

from Functions import preprocess_and_syllabify, synthesize_speech
from db import populate_syllable_db, get_syllable_audio_path

from app_config import AUDIO_FORMAT
from strings import STRINGS

logger = logging.getLogger(__name__)


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
            logger.exception("Audio generation failed")
            self.failed.emit(str(e))


class AudioWorker(QThread):
    """Worker thread for audio playback, to prevent UI freezing."""
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
        except Exception:
            logger.exception("Audio worker failed")
            self.finished.emit(False, STRINGS["playback_error"].format(file=self.audio_file))

    def _play_audio(self):
        self.progress.emit(STRINGS["status_playing"])
        try:
            if sys.platform == "win32":
                # No subprocess/shell needed on Windows: this launches the
                # file directly with its registered default player.
                os.startfile(self.audio_file)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", self.audio_file], check=True)
            else:
                subprocess.run(["aplay", self.audio_file], check=True)
        except Exception:
            logger.exception("Audio playback failed for %s", self.audio_file)
            self.finished.emit(False, STRINGS["playback_error"].format(file=self.audio_file))