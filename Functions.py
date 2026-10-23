import os
import re
import logging

from pydub import AudioSegment, effects
from pydub.generators import WhiteNoise
from pydub.silence import detect_nonsilent

from utils import resource_path
from db import get_syllable_audio_path, populate_syllable_db
from Constants.abbreviations import abbrevs
from Constants.acronyms import acr
from Constants.symbols import symbols_to_remove, symbols_to_expand

logger = logging.getLogger(__name__)

CROSSFADE_MS = 15
SILENCE_MIN_LEN_MS = 15
SILENCE_THRESH_DB = -45
INTER_WORD_SILENCE_MS = 100
SENTENCE_FINAL_SILENCE_MS = 400
BACKGROUND_NOISE_GAIN_DB = -35
HIGH_PASS_CUTOFF_HZ = 20
FADE_MS = 5

# Unknown abbreviations are appended here (one per line, "<abbr>\tUNKNOWN")
# so they can be expanded by hand and then moved into Constants/abbreviations.py.
UNKNOWN_ABBREV_FILE = "unknown_abbreviations.txt"

GEORGIAN = "\u10D0-\u10FF"
# Abbreviation-like tokens: dotted multi-part forms (e.g. "ე.ი.") and slash forms (e.g. "ს/ს").
ABBREV_LIKE = re.compile(
    rf"(?<![{GEORGIAN}.])(?:[{GEORGIAN}]{{1,5}}\.){{2,}}"
    rf"|(?<![{GEORGIAN}/])[{GEORGIAN}]{{1,5}}/[{GEORGIAN}]{{1,5}}(?![{GEORGIAN}/])"
)


# === აბრევიატურების გაშლა ===
def _whole_token(s):
    """Regex matching `s` only when it is not part of a longer word.

    Plain \\b fails for abbreviations ending in '.', because there is no word
    boundary between '.' and a following space, so lookarounds are used.
    """
    return r'(?<![\w.])' + re.escape(s) + r'(?!\w)'


def log_unknown_abbreviations(text, path=None):
    """Append abbreviation-like tokens that were not expanded to the UNKNOWN list.

    Returns the set of unknown tokens found in `text`.
    """
    found = {m.group(0) for m in ABBREV_LIKE.finditer(text)}
    if not found:
        return found
    path = path or os.path.join(os.getcwd(), UNKNOWN_ABBREV_FILE)
    try:
        known = set()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                known = {line.split("\t")[0] for line in f if line.strip()}
        new = sorted(found - known)
        if new:
            with open(path, "a", encoding="utf-8") as f:
                for abbr in new:
                    f.write(f"{abbr}\tUNKNOWN\n")
            logger.info("Unknown abbreviations logged to %s: %s", path, ", ".join(new))
    except OSError:
        logger.exception("Could not write unknown abbreviations to %s", path)
    return found


def expand_abbreviations(text):
    """Expands abbreviations in the text using the abbrevs dictionary.

    Abbreviation-like tokens that are not in the dictionary are logged as
    UNKNOWN entries (see log_unknown_abbreviations) for manual expansion.
    """
    # Longest first, so "ძვ.წ." is expanded before its suffix "წ.".
    for abbrev in sorted(abbrevs, key=len, reverse=True):
        text = re.sub(_whole_token(abbrev), abbrevs[abbrev], text)
    log_unknown_abbreviations(text)
    # Until an unknown dotted form is expanded by hand, drop its inner dots so
    # they are not read as sentence ends ("ფ.ს.ქ." -> "ფსქ").
    text = ABBREV_LIKE.sub(lambda m: m.group(0).replace(".", ""), text)
    return text


# === აკრონიმების გაშლა ===
def expand_acronyms(text):
    """Expands acronyms in the text using the acr dictionary.

    Matches whole tokens, so an acronym followed by punctuation
    (e.g. "თსუ.") is expanded too.
    """
    for acronym in sorted(acr, key=len, reverse=True):
        text = re.sub(_whole_token(acronym), acr[acronym], text)
    return text


# === სიმბოლოების გაშლა ===
# A hyphen is read as "minus" only as a sign directly before a number ("-5").
# Elsewhere it joins a numeral or acronym to a Georgian ending ("2007-ში",
# "თსუ-ს"), marks an ordinal ("მე-5", "5-ე", "1-ლი") or links a compound.
MINUS_SIGN = re.compile(r'(?:^|(?<=[\s(=<>]))[-−](?=\d)', re.MULTILINE)


def expand_symbols(text):
    minus = symbols_to_expand.get("-")
    if minus:
        text = MINUS_SIGN.sub(f' {minus} ', text)
    for symbol, replacement in symbols_to_expand.items():
        if symbol != "-":
            text = text.replace(symbol, f' {replacement} ')
    return text


def remove_symbols_and_tags(text):
    """Removes unwanted characters.

    Deletes markup tags and the characters in symbols_to_remove, then every
    character outside the Georgian alphabet except whitespace and the
    punctuation used for pauses (. , ! ?).
    """
    text = re.sub(r'(?<!\d)-\s*([a-zA-Z0-9]+)', r'\1', text)
    text = re.sub(r'(?<!\d)-', '', text)
    text = re.sub(r'<[^>]+>', '', text)

    if symbols_to_remove:
        char_class = "".join(re.escape(s) for s in symbols_to_remove)
        text = re.sub(f'[{char_class}]', '', text)

    # Non-Georgian characters (Latin letters, digits left over, other scripts).
    text = re.sub(rf'[^{GEORGIAN}\s.,!?]', ' ', text)

    # Attach pause punctuation to the preceding word: "word , x" -> "word, x".
    text = re.sub(r'\s*([.,!?]+)\s*', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def ordinal_to_words(number):
    """Ordinal numeral in the nominative: 5 -> "მეხუთე", 21 -> "ოცდამეერთე".

    The prefix მე- and the suffix -ე go on the last element of the cardinal,
    after "და" in compounds; 1 is the suppletive "პირველი".
    """
    if number == 1:
        return "პირველი"
    words = convert_numbers_to_words(number)
    if not words or words.isdigit():
        return words
    head, space, last = words.rpartition(" ")
    tens, da, unit = last.rpartition("და")
    stem = unit[:-1] if unit.endswith(("ი", "ა")) else unit
    return f"{head}{space}{tens}{da}მე{stem}ე"


def attach_suffix(word, suffix):
    """Join a Georgian ending written after a hyphen to a numeral in words.

    "ხუთი" + "ში" -> "ხუთში", "რვა" + "ის" -> "რვის", "ხუთი" + "დან" ->
    "ხუთიდან", "ხუთი" + "მდე" -> "ხუთამდე", "ორი" + "ვე" -> "ორივე".
    """
    if suffix.startswith("ვე"):
        return word + suffix
    if suffix.startswith("დან"):
        stem = word[:-1] if word.endswith(("ი", "ა", "ე")) else word
        return stem + "ი" + suffix
    if suffix.startswith("მდე"):
        return (word[:-1] + "ა" if word.endswith("ი") else word) + suffix
    if word.endswith("ი") or (word.endswith(("ა", "ე")) and suffix.startswith("ი")):
        return word[:-1] + suffix
    return word + suffix


# Roman numerals next to a Georgian word ("XIX საუკუნე", "ბაგრატ III") are read
# as ordinals. Only I, V and X are accepted (up to XXXIX): enough for centuries
# and regnal numbers, without catching Latin acronyms such as "CD".
ROMAN_NUMERAL = re.compile(
    rf"(?<![A-Za-z])(?=[IVX])(X{{0,3}}(?:IX|IV|V?I{{0,3}}))(?:-([{GEORGIAN}]+))?(?![A-Za-z])"
)
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10}


def roman_to_int(numeral):
    values = [ROMAN_VALUES[ch] for ch in numeral]
    return sum(-v if i + 1 < len(values) and v < values[i + 1] else v
               for i, v in enumerate(values))


def expand_roman_numerals(text):
    def replace(match):
        numeral, suffix = match.group(1), match.group(2)
        before = match.string[max(0, match.start() - 2):match.start()]
        after = match.string[match.end():match.end() + 2]
        next_to_georgian = (
            suffix
            or re.search(rf"[{GEORGIAN}]\s?$", before)
            or re.match(rf"\s?[{GEORGIAN}]", after)
        )
        if not next_to_georgian:
            return match.group(0)
        word = ordinal_to_words(roman_to_int(numeral))
        return attach_suffix(word, suffix) if suffix else word

    return ROMAN_NUMERAL.sub(replace, text)


def expand_numbers(text):
    def replace_ordinal(match):
        return ordinal_to_words(int(match.group(1)))

    def replace_first(match):
        # "1-ლი" -> "პირველი", "1-ლმა" -> "პირველმა"
        if int(match.group(1)) == 1:
            return "პირველ" + match.group(2)
        return match.group(0)

    def replace_with_suffix(match):
        return attach_suffix(convert_numbers_to_words(int(match.group(1))), match.group(2))

    def replace_decimal(match):
        decimal = match.group(1)
        suffix = match.group(2) or ""

        if decimal.startswith("."):
            int_part = 0
            frac_part = decimal[1:]
        else:
            int_part, frac_part = decimal.split(".")

        int_word = convert_numbers_to_words(int(int_part))
        frac_word = convert_numbers_to_words(int(frac_part))
        return f"{int_word} მთელი {frac_word}{suffix}"

    def replace_plain_number(match):
        word = convert_numbers_to_words(int(match.group()))
        return word if word else str(match.group())

    text = re.sub(r'(?<=\d),(?=\d{3}\b)', '', text)
    # Ordinals: "მე-5" and "5-ე" -> "მეხუთე", "1-ლი" -> "პირველი".
    text = re.sub(rf'(?<![{GEORGIAN}])მე-(\d+)(?!\d)', replace_ordinal, text)
    text = re.sub(rf'(?<!\d)(\d+)-ე(?![{GEORGIAN}])', replace_ordinal, text)
    text = re.sub(rf'(?<!\d)(\d+)-ლ([{GEORGIAN}]*)', replace_first, text)
    # Case endings after a hyphen: "2007-ში" -> "ორი ათას შვიდში".
    text = re.sub(rf'(?<!\d)(\d+)-([{GEORGIAN}]+)', replace_with_suffix, text)
    # Ranges: "1990-1995" is read as two numbers.
    text = re.sub(r'(?<=\d)\s*-\s*(?=\d)', ' ', text)
    text = re.sub(r'\b(\d*\.\d+)([%\w\-]*)', lambda m: str(replace_decimal(m)), text)
    text = re.sub(r'\b\d+\b', lambda m: str(replace_plain_number(m)), text)

    return text


# === რიცხვების სიტყვებად გარდაქმნა ===
def convert_numbers_to_words(number):
    units = [
        "ნულ", "ერთ", "ორ", "სამ", "ოთხ", "ხუთ", "ექვს", "შვიდ", "რვა", "ცხრა",
        "ათ", "თერთმეტ", "თორმეტ", "ცამეტ", "თოთხმეტ", "თხუთმეტ", "თექვსმეტ",
        "ჩვიდმეტ", "თვრამეტ", "ცხრამეტ", "ოც"
    ]
    tens = ["ოც", "ორმოც", "სამოც", "ოთხმოც"]
    if number < 21:
        if units[number].endswith("ა"):
            return units[number] + ""
        else:
            return units[number] + "ი"
    elif number < 100:
        a = number // 20
        b = number - a * 20
        if b != 0:
            prefix = tens[a - 1] + "და" + units[b]
            if units[b].endswith("ა"):
                return prefix
            else:
                return prefix + "ი"
        else:
            return tens[a - 1] + "ი"
    elif number < 1_000:
        a = number // 100
        if a == 1:
            prefix = "ას"
        else:
            prefix = units[a] + "ას"

        if number % 100 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 100)
            return prefix + " " + rest if rest else prefix

    elif number < 1_000_000:
        a = number // 1_000
        if a == 1:
            prefix = "ათას"
        else:
            prefix = convert_numbers_to_words(a) + " ათას"
        if number % 1_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1000)
            return prefix + " " + rest if rest else prefix

    elif number < 1_000_000_000:
        a = number // 1_000_000
        prefix = convert_numbers_to_words(a) + " მილიონ"
        if number % 1_000_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1_000_000)
            return prefix + " " + rest if rest else prefix

    elif number < 1_000_000_000_000:
        a = number // 1_000_000_000
        prefix = convert_numbers_to_words(a) + " მილიარდ"
        if number % 1_000_000_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1_000_000_000)
            return prefix + " " + rest if rest else prefix
    else:
        return str(number)


# === გრაფემი ფონემში ===
def grapheme_to_phoneme(text):
    return list(text)


VOWELS = set("აეიოუ")

EJECTIVES = set("პტკყწჭ")

FRICATIVES = set("სშზჟხღჰ")

SONORANTS = set("მნლრვ")

HARMONIC_CLUSTERS = {
    "შხ", "ტკ", "ჩქ", "ფქ", "დგ", "ცქ", "შქ", "ზგ", "ჭკ",
    "ფხ", "თხ", "ცხ", "ჩხ", "ბღ", "დღ", "ზღ", "ჯღ",
    "პყ", "ტყ", "წყ", "ჭყ",
}


def _leftmost_harmonic_start(cluster):
    """Index within `cluster` where a harmonic pair (rule 3) begins, or None."""
    for i in range(len(cluster) - 1):
        if cluster[i:i + 2] in HARMONIC_CLUSTERS:
            return i
    return None


def _leftmost_ejective(cluster):
    """Index within `cluster` of the first ejective consonant (rule 4), or None."""
    for i, ch in enumerate(cluster):
        if ch in EJECTIVES:
            return i
    return None


def _coda_length(cluster):
    """How many leading characters of an inter-vowel consonant cluster stay
    with the PRECEDING syllable (the rest open the following syllable).

    `cluster` is the run of consonants between two vowels; len(cluster) >= 2
    here (the 0- and 1-consonant cases are handled directly by the caller,
    rules 5 and the trivial hiatus case).
    """

    coda_len = 1

    if cluster[0] in FRICATIVES and any(c in SONORANTS for c in cluster[1:]):
        coda_len = 0

    harmonic_at = _leftmost_harmonic_start(cluster)
    if harmonic_at is not None:
        coda_len = min(coda_len, harmonic_at)

    ejective_at = _leftmost_ejective(cluster)
    if ejective_at is not None:
        coda_len = min(coda_len, ejective_at)

    return coda_len


def syllabify_georgian(word):
    vowel_idxs = [i for i, ch in enumerate(word) if ch in VOWELS]
    if not vowel_idxs:
        logger.debug("Word %r has no vowels; returned as a single syllable.", word)
        return [word]

    syllables = []
    start = 0

    for vi, vj in zip(vowel_idxs, vowel_idxs[1:]):
        cluster = word[vi + 1:vj]

        if len(cluster) == 0:
            boundary = vi + 1
        elif len(cluster) == 1:
            boundary = vi + 1
        else:
            boundary = vi + 1 + _coda_length(cluster)

        syllables.append(word[start:boundary])
        start = boundary

    syllables.append(word[start:])
    syllables = [syl.replace(" ", "") for syl in syllables if syl.strip()]
    return syllables


def fallback_units(syllable):
    """Split a syllable into smaller recordable units (sub-syllable fallback).

    A syllable is (onset consonants) + vowel + (coda consonants). It is rebuilt
    from the last onset consonant joined with the vowel (a CV unit) plus each
    remaining consonant on its own, e.g. "წლებ" -> ["წ", "ლე", "ბ"]. A syllable
    without a vowel is split into its letters.
    """
    vowel_at = next((i for i, ch in enumerate(syllable) if ch in VOWELS), None)
    if vowel_at is None:
        return list(syllable)
    onset, coda = syllable[:vowel_at], syllable[vowel_at + 1:]
    core = onset[-1:] + syllable[vowel_at]
    return list(onset[:-1]) + [core] + list(coda)


def resolve_syllable_audio(syllable, db_path=None):
    """Audio files for `syllable`: its own recording if there is one, otherwise
    the recordings of its fallback units. A CV unit with no recording is
    further split into consonant + vowel. Returns None if any piece is missing.
    """
    path = get_syllable_audio_path(syllable, db_path)
    if path:
        return [path]

    paths = []
    for unit in fallback_units(syllable):
        unit_path = get_syllable_audio_path(unit, db_path)
        if unit_path:
            paths.append(unit_path)
            continue
        if len(unit) == 2:
            pieces = [get_syllable_audio_path(ch, db_path) for ch in unit]
            if all(pieces):
                paths.extend(pieces)
                continue
        return None
    logger.debug("Syllable %r built from fallback units %s", syllable, fallback_units(syllable))
    return paths


def unique_syllables(syllables):
    return set(syllables)


def normalize_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)  # markup tags, before '<'/'>' are expanded to words
    text = expand_symbols(text)
    text = expand_abbreviations(text)
    text = expand_acronyms(text)

    text = re.sub(r'([a-zA-Z]+)-([a-zA-Z]+)', r'\1\2', text)
    text = expand_roman_numerals(text)
    text = expand_numbers(text)
    text = remove_symbols_and_tags(text)

    return text.strip()


def preprocess_and_syllabify(text):
    text = normalize_text(text)
    words = text.split()
    all_syllables = []

    for word in words:
        # '.', '!', '?' end a sentence (<eos>, long pause); ',' gives a double
        # pause (<s><s>); every other word is followed by a single <s>.
        if re.search(r'[.!?]', word):
            pause = ["<eos>"]
        elif ',' in word:
            pause = ["<s>", "<s>"]
        else:
            pause = ["<s>"]

        word_clean = re.sub(r'[.,!?;:"„“–]', '', word)

        if not word_clean:
            # Stray punctuation: strengthen the pause after the previous word.
            if all_syllables and pause == ["<eos>"]:
                while all_syllables and all_syllables[-1] == "<s>":
                    all_syllables.pop()
                all_syllables.append("<eos>")
            elif all_syllables and pause == ["<s>", "<s>"]:
                all_syllables.append("<s>")
            continue

        all_syllables.extend(syllabify_georgian(word_clean))
        all_syllables.extend(pause)

    return all_syllables


def trim_silence(seg):
    """Cut leading and trailing silence, keeping any silence inside the unit.

    Stop closures and the lag after an ejective burst are silent as well, so
    keeping only the first non-silent chunk would reduce syllables such as
    "კავ" or "წამ" to their burst.
    """
    ranges = detect_nonsilent(
        seg, min_silence_len=SILENCE_MIN_LEN_MS, silence_thresh=SILENCE_THRESH_DB
    )
    if not ranges:
        return seg
    return seg[ranges[0][0]:ranges[-1][1]]


def synthesize_speech(syllables, db_path=None):
    if db_path is None:
        db_path = resource_path("tts_syllables.db")

    def simple_crossfade(a, b, duration_ms=CROSSFADE_MS):
        return a.append(b, crossfade=duration_ms)

    def prepare_segment(path):
        seg = AudioSegment.from_wav(path)
        seg = effects.normalize(seg).high_pass_filter(HIGH_PASS_CUTOFF_HZ)
        seg = trim_silence(seg)
        return seg.fade_in(FADE_MS).fade_out(FADE_MS)

    output = AudioSegment.empty()

    for syl in syllables:
        if syl == "<s>":
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=INTER_WORD_SILENCE_MS)
            continue
        if syl == "<eos>":
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=SENTENCE_FINAL_SILENCE_MS)
            continue

        paths = resolve_syllable_audio(syl, db_path)
        if not paths:
            logger.warning("Missing syllable audio: %s", syl)
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=INTER_WORD_SILENCE_MS)
            continue

        try:
            for path in paths:
                seg = prepare_segment(path)
                if len(output) == 0:
                    output = seg
                else:
                    output = simple_crossfade(output, seg)
        except Exception:
            logger.exception("Error processing syllable '%s'", syl)
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=INTER_WORD_SILENCE_MS)

    if len(output) > 0:
        noise = WhiteNoise().to_audio_segment(duration=len(output)).apply_gain(BACKGROUND_NOISE_GAIN_DB)
        output = output.overlay(noise)

    return output