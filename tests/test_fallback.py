import unittest
from unittest import mock

import Functions
from Functions import fallback_units, resolve_syllable_audio


class FallbackUnitsTest(unittest.TestCase):
    def test_complex_onset_and_coda(self):
        self.assertEqual(fallback_units("წლებ"), ["წ", "ლე", "ბ"])

    def test_cv_syllable_is_kept_whole(self):
        self.assertEqual(fallback_units("და"), ["და"])

    def test_bare_vowel(self):
        self.assertEqual(fallback_units("ა"), ["ა"])

    def test_vowel_with_coda(self):
        self.assertEqual(fallback_units("ურ"), ["უ", "რ"])

    def test_no_vowel(self):
        self.assertEqual(fallback_units("კმ"), ["კ", "მ"])


class ResolveSyllableAudioTest(unittest.TestCase):
    def _with_recordings(self, recorded):
        return mock.patch.object(
            Functions, "get_syllable_audio_path",
            side_effect=lambda unit, db_path=None: f"{unit}.wav" if unit in recorded else None,
        )

    def test_own_recording_wins(self):
        with self._with_recordings({"წლებ", "წ", "ლე", "ბ"}):
            self.assertEqual(resolve_syllable_audio("წლებ"), ["წლებ.wav"])

    def test_built_from_units(self):
        with self._with_recordings({"წ", "ლე", "ბ"}):
            self.assertEqual(resolve_syllable_audio("წლებ"), ["წ.wav", "ლე.wav", "ბ.wav"])

    def test_cv_unit_split_further(self):
        with self._with_recordings({"წ", "ლ", "ე", "ბ"}):
            self.assertEqual(resolve_syllable_audio("წლებ"), ["წ.wav", "ლ.wav", "ე.wav", "ბ.wav"])

    def test_missing_unit(self):
        with self._with_recordings({"წ", "ლე"}):
            self.assertIsNone(resolve_syllable_audio("წლებ"))


if __name__ == "__main__":
    unittest.main()
