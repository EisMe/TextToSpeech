# Georgian Text-to-Speech (TTS) — syllable-based concatenative system

**English** | [ქართული](#ქართული)

A rule-based Georgian text-to-speech system. It splits normalized text into syllables with explicit phonological rules and joins pre-recorded syllable audio (concatenative synthesis). It runs offline on a CPU and uses no cloud API.

> Research prototype. It is meant to be a transparent, inspectable reference system for Georgian, not a competitor to neural TTS in naturalness.

## Features

- Text normalization: abbreviations, acronyms, symbols and numbers are expanded to words.
- Rule-based syllabification (harmonic clusters, ejectives, sonorants).
- Concatenation of recorded syllables with fixed-length pauses (100 ms between words, 200 ms at a comma, 400 ms after `.`, `!` or `?`) and 15 ms cross-fades.
- Unknown dotted or slashed abbreviations (e.g. `ფ.ს.ქ.`, `ბ/ზ`) are logged to `unknown_abbreviations.txt` as `UNKNOWN` entries for manual expansion.
- Desktop GUI (PyQt6): type text, load a `.txt`, `.pdf` or `.docx` file, or use the on-screen Georgian keyboard; play the result or save it as `.wav`.

## Current limitations

- **Inventory:** `AudioDB/` has 121 recorded syllables. The corpus analysis in the paper identifies 247 syllables that cover about 80% of syllable tokens.
- **Missing syllables:** a syllable with no recording is built from smaller units (see *How it works*). Generation stops, and the GUI lists the syllables, only if one of those units is missing too. The fallback needs recordings of the single consonants, which are not in `AudioDB/` yet.
- **Prosody:** only fixed pauses and cross-fades. No pitch, duration or stress modelling.
- **Normalization:** lookup-based; no context-dependent disambiguation of abbreviations or number case.
- **Speaker:** one voice.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/EisMe/TextToSpeech.git
cd TextToSpeech
pip install -r requirements.txt
```

On Python 3.13, `pydub` also needs: `pip install audioop-lts`.

## Usage

```bash
python Interface.py
```

Enter Georgian text or load a `.txt`, `.pdf` or `.docx` file (PDF and DOCX import need `PyPDF2` and `python-docx`), press generate, then play or save the audio. Generation only works if every syllable of the text, or every unit it falls back to, is in `AudioDB/`.

## How it works

1. **Normalize** the text (`Functions.py`: symbols → abbreviations → acronyms → numbers → removal of unwanted and non-Georgian characters).
2. **Syllabify** each word with the rule set in `syllabify_georgian()`.
3. **Look up** `AudioDB/<syllable>.wav` for every syllable. If it is missing, the syllable is rebuilt from units: the last onset consonant with the vowel (a CV unit) plus each other consonant on its own, e.g. `წლებ` → `წ` + `ლე` + `ბ` (`resolve_syllable_audio()`). A missing CV unit is split again into consonant + vowel.
4. **Concatenate** with pydub: normalize, 20 Hz high-pass, 5 ms fades, 15 ms cross-fade, fixed pauses, low-level white noise overlay.

## Repository layout

| Path | Purpose |
|---|---|
| `Interface.py`, `main_window.py`, `widgets.py`, `theme.py`, `workers.py` | GUI |
| `Functions.py` | normalization, syllabification, synthesis |
| `Constants/` | abbreviation, acronym and symbol lists |
| `db.py`, `tts_syllables.db` | SQLite registry of recordings (audio is located by file name) |
| `AudioDB/` | recorded syllables (`<syllable>.wav`, 44.1 kHz, 16-bit) |

## Paper and citation

This repository accompanies the paper on a syllable-based concatenative TTS system for Georgian. If you use it, please cite:

```
Iakobashvili, N. (2026). Georgian Text-to-Speech. https://github.com/EisMe/TextToSpeech
```

## License

- Code: MIT License (see `LICENSE`).
- Recordings in `AudioDB/`: CC BY 4.0 (see `AudioDB/LICENSE.txt`).

The speaker consented to the recordings being published under this license.

---

# ქართული

**წესებზე დაფუძნებული ქართული ტექსტიდან მეტყველებაში გადამყვანი (TTS) სისტემა.** ტექსტი იყოფა მარცვლებად ფონოლოგიური წესებით, შემდეგ კი წინასწარ ჩაწერილი მარცვლების აუდიო ერთმანეთს უერთდება (კონკატენაციური სინთეზი). სისტემა მუშაობს ოფლაინ, პროცესორზე და არ იყენებს ღრუბლოვან API-ს.

> კვლევითი პროტოტიპი. მისი მიზანია იყოს გამჭვირვალე, შესამოწმებადი საორიენტაციო სისტემა ქართულისთვის და არა ნეირონულ TTS-თან კონკურენცია ბუნებრიობით.

## შესაძლებლობები

- ტექსტის ნორმალიზაცია: აბრევიატურები, აკრონიმები, სიმბოლოები და რიცხვები იშლება სიტყვებად.
- მარცვლებად დაყოფა წესებით (ჰარმონიული კლასტერები, ეჯექტივები, სონორები).
- ჩაწერილი მარცვლების შეერთება ფიქსირებული პაუზებით (100 მწ სიტყვებს შორის, 200 მწ მძიმესთან, 400 მწ `.`, `!` ან `?`-ის შემდეგ) და 15 მწ კროსფეიდით.
- უცნობი აბრევიატურები (მაგ. `ფ.ს.ქ.`, `ბ/ზ`) იწერება ფაილში `unknown_abbreviations.txt` `UNKNOWN` ნიშნით, ხელით გასაშლელად.
- GUI (PyQt6): ტექსტის შეყვანა, `.txt`, `.pdf` ან `.docx` ფაილის ატვირთვა ან ეკრანული ქართული კლავიატურა; შედეგის მოსმენა ან `.wav`-ად შენახვა.

## ამჟამინდელი შეზღუდვები

- **მარცვლების რაოდენობა:** `AudioDB/`-ში 121 ჩაწერილი მარცვალია. ნაშრომის კორპუსის ანალიზით 247 მარცვალი ფარავს მარცვლის გამოყენებათა დაახლოებით 80%-ს.
- **ნაკლული მარცვლები:** ჩაუწერელი მარცვალი იწყობა უფრო მცირე ერთეულებისგან: ბოლო თანხმოვანი ხმოვანთან ერთად (CV ერთეული) და დანარჩენი თანხმოვნები ცალ-ცალკე, მაგ. `წლებ` → `წ` + `ლე` + `ბ`. გენერაცია ჩერდება მხოლოდ მაშინ, თუ რომელიმე ერთეულიც აკლია. ამისთვის საჭიროა ცალკეული თანხმოვნების ჩანაწერები, რომლებიც `AudioDB/`-ში ჯერ არ არის.
- **პროსოდია:** მხოლოდ ფიქსირებული პაუზები და კროსფეიდი. ტონის, ხანგრძლივობისა და მახვილის მოდელირება არ არის.
- **ნორმალიზაცია:** სიებზე დაფუძნებულია; აბრევიატურებისა და რიცხვების ბრუნვა კონტექსტის მიხედვით არ განისაზღვრება.
- **ხმა:** ერთი დიქტორი.

## დაყენება

საჭიროა Python 3.10+.

```bash
git clone https://github.com/EisMe/TextToSpeech.git
cd TextToSpeech
pip install -r requirements.txt
```

Python 3.13-ზე `pydub`-ს დამატებით სჭირდება: `pip install audioop-lts`.

## გამოყენება

```bash
python Interface.py
```

შეიყვანეთ ქართული ტექსტი ან ატვირთეთ `.txt`, `.pdf` ან `.docx` ფაილი (PDF-სა და DOCX-ს სჭირდება `PyPDF2` და `python-docx`), დააჭირეთ გენერაციას, შემდეგ მოუსმინეთ ან შეინახეთ აუდიო. გენერაცია მუშაობს მხოლოდ მაშინ, თუ ტექსტის ყველა მარცვალი არის `AudioDB/`-ში.

## როგორ მუშაობს

1. **ნორმალიზაცია** (`Functions.py`): სიმბოლოები → აბრევიატურები → აკრონიმები → რიცხვები → არასასურველი და არაქართული სიმბოლოების წაშლა.
2. **მარცვლებად დაყოფა** `syllabify_georgian()` ფუნქციის წესებით.
3. **ძიება:** თითოეული მარცვლისთვის იძებნება `AudioDB/<მარცვალი>.wav`.
4. **შეერთება** pydub-ით: ნორმალიზაცია, 20 ჰც მაღალი ფილტრი, 5 მწ ფეიდები, 15 მწ კროსფეიდი, ფიქსირებული პაუზები, დაბალი დონის თეთრი ხმაური.

## ლიცენზია

- კოდი: MIT (იხ. `LICENSE`).
- `AudioDB/`-ის ჩანაწერები: CC BY 4.0 (იხ. `AudioDB/LICENSE.txt`).

დიქტორი ეთანხმება, რომ ჩანაწერები ამ ლიცენზიით გამოქვეყნდეს.
