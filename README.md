# Georgian Text-to-Speech (TTS) — syllable-based concatenative system

**English** | [ქართული](#ქართული)

A rule-based Georgian text-to-speech system. It splits normalized text into syllables with explicit phonological rules and joins pre-recorded syllable audio (concatenative synthesis). It runs offline on a CPU and uses no cloud API.

> Research prototype. It is meant to be a transparent, inspectable reference system for Georgian, not a competitor to neural TTS in naturalness.

## Features

- Text normalization: abbreviations, acronyms, symbols and numbers are expanded to words.
- Rule-based syllabification (harmonic clusters, ejectives, sonorants).
- Concatenation of recorded syllables with fixed-length pauses (100 ms between words, 400 ms after `!` or `?`) and 15 ms cross-fades.
- Desktop GUI (PyQt6): type text, load a `.txt` file, or use the on-screen Georgian keyboard; play the result or save it as `.wav`.

## Current limitations

- **Inventory:** `AudioDB/` has 121 recorded syllables. The corpus analysis in the paper identifies 241 syllables that cover about 80% of syllable tokens.
- **Missing syllables:** if a syllable has no recording, generation stops and the GUI lists the missing syllables. There is no diphone fallback yet.
- **Prosody:** only fixed pauses and cross-fades. No pitch, duration or stress modelling.
- **Punctuation:** commas and full stops are removed during normalization, so only `!` and `?` produce the longer sentence-end pause.
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

Enter or load Georgian text, press generate, then play or save the audio. Generation only works if every syllable of the text is in `AudioDB/`.

## How it works

1. **Normalize** the text (`Functions.py`: symbols → abbreviations → acronyms → numbers → cleanup).
2. **Syllabify** each word with the rule set in `syllabify_georgian()`.
3. **Look up** `AudioDB/<syllable>.wav` for every syllable.
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
- ჩაწერილი მარცვლების შეერთება ფიქსირებული პაუზებით (100 მწ სიტყვებს შორის, 400 მწ `!` ან `?`-ის შემდეგ) და 15 მწ კროსფეიდით.
- GUI (PyQt6): ტექსტის შეყვანა, `.txt` ფაილის ატვირთვა ან ეკრანული ქართული კლავიატურა; შედეგის მოსმენა ან `.wav`-ად შენახვა.

## ამჟამინდელი შეზღუდვები

- **მარცვლების რაოდენობა:** `AudioDB/`-ში 121 ჩაწერილი მარცვალია. ნაშრომის კორპუსის ანალიზით 241 მარცვალი ფარავს მარცვლის გამოყენებათა დაახლოებით 80%-ს.
- **ნაკლული მარცვლები:** თუ მარცვალი არ არის ჩაწერილი, გენერაცია ჩერდება და GUI აჩვენებს ნაკლულ მარცვლებს. დიფონური ალტერნატივა ჯერ არ არსებობს.
- **პროსოდია:** მხოლოდ ფიქსირებული პაუზები და კროსფეიდი. ტონის, ხანგრძლივობისა და მახვილის მოდელირება არ არის.
- **პუნქტუაცია:** მძიმე და წერტილი ნორმალიზაციისას იშლება, ამიტომ წინადადების ბოლოს გრძელ პაუზას მხოლოდ `!` და `?` იძლევა.
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

შეიყვანეთ ან ატვირთეთ ქართული ტექსტი, დააჭირეთ გენერაციას, შემდეგ მოუსმინეთ ან შეინახეთ აუდიო. გენერაცია მუშაობს მხოლოდ მაშინ, თუ ტექსტის ყველა მარცვალი არის `AudioDB/`-ში.

## როგორ მუშაობს

1. **ნორმალიზაცია** (`Functions.py`): სიმბოლოები → აბრევიატურები → აკრონიმები → რიცხვები → გასუფთავება.
2. **მარცვლებად დაყოფა** `syllabify_georgian()` ფუნქციის წესებით.
3. **ძიება:** თითოეული მარცვლისთვის იძებნება `AudioDB/<მარცვალი>.wav`.
4. **შეერთება** pydub-ით: ნორმალიზაცია, 20 ჰც მაღალი ფილტრი, 5 მწ ფეიდები, 15 მწ კროსფეიდი, ფიქსირებული პაუზები, დაბალი დონის თეთრი ხმაური.

## ლიცენზია

- კოდი: MIT (იხ. `LICENSE`).
- `AudioDB/`-ის ჩანაწერები: CC BY 4.0 (იხ. `AudioDB/LICENSE.txt`).

დიქტორი ეთანხმება, რომ ჩანაწერები ამ ლიცენზიით გამოქვეყნდეს.
