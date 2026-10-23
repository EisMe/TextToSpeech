import unittest

from pydub import AudioSegment
from pydub.generators import Sine

from Functions import normalize_text, ordinal_to_words, trim_silence


class HyphenTest(unittest.TestCase):
    def test_minus_sign_before_number(self):
        self.assertEqual(normalize_text("ტემპერატურა -5 გრადუსი"), "ტემპერატურა მინუს ხუთი გრადუსი")

    def test_case_ending_after_number(self):
        self.assertEqual(normalize_text("2007-ში დაარსდა"), "ორი ათას შვიდში დაარსდა")
        self.assertEqual(normalize_text("1990-იან წლებში"), "ათას ცხრაას ოთხმოცდაათიან წლებში")
        self.assertEqual(normalize_text("10-მდე"), "ათამდე")
        self.assertEqual(normalize_text("5-დან"), "ხუთიდან")

    def test_range_is_read_as_two_numbers(self):
        self.assertEqual(normalize_text("1990-1995"), "ათას ცხრაას ოთხმოცდაათი ათას ცხრაას ოთხმოცდათხუთმეტი")

    def test_compound_word(self):
        self.assertEqual(normalize_text("ჩრდილო-დასავლეთი"), "ჩრდილოდასავლეთი")

    def test_acronym_with_ending(self):
        self.assertEqual(normalize_text("თსუ-ს"), "თბილისის სახელმწიფო უნივერსიტეტის")

    def test_abbreviation_with_hyphen(self):
        self.assertEqual(normalize_text("ბ.-ნო გიორგი"), "ბატონო გიორგი")


class OrdinalTest(unittest.TestCase):
    def test_ordinal_words(self):
        self.assertEqual(ordinal_to_words(1), "პირველი")
        self.assertEqual(ordinal_to_words(2), "მეორე")
        self.assertEqual(ordinal_to_words(8), "მერვე")
        self.assertEqual(ordinal_to_words(21), "ოცდამეერთე")
        self.assertEqual(ordinal_to_words(125), "ას ოცდამეხუთე")

    def test_written_forms(self):
        self.assertEqual(normalize_text("მე-5 კლასი"), "მეხუთე კლასი")
        self.assertEqual(normalize_text("5-ე კლასი"), "მეხუთე კლასი")
        self.assertEqual(normalize_text("1-ლი ადგილი"), "პირველი ადგილი")

    def test_roman_numerals(self):
        self.assertEqual(normalize_text("XIX საუკუნე"), "მეცხრამეტე საუკუნე")
        self.assertEqual(normalize_text("ბაგრატ III"), "ბაგრატ მესამე")
        self.assertEqual(normalize_text("ლუი XIV-ის"), "ლუი მეთოთხმეტის")

    def test_latin_acronym_is_not_a_numeral(self):
        self.assertEqual(normalize_text("CD დისკი"), "დისკი")


class TrimSilenceTest(unittest.TestCase):
    def test_keeps_silence_inside_the_unit(self):
        # Burst, a 40 ms silent lag (as after an ejective release), then the vowel.
        burst = Sine(2000).to_audio_segment(duration=30)
        vowel = Sine(220).to_audio_segment(duration=150)
        gap = AudioSegment.silent(duration=40, frame_rate=burst.frame_rate)
        edge = AudioSegment.silent(duration=50, frame_rate=burst.frame_rate)
        trimmed = trim_silence(edge + burst + gap + vowel + edge)
        self.assertAlmostEqual(len(trimmed), 220, delta=5)


if __name__ == "__main__":
    unittest.main()
