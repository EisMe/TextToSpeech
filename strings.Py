"""Localized strings and Georgian-input data.

Everything user-facing lives in STRINGS so the app has exactly one place to
translate or proofread. Keyboard/alphabet data is also kept here since it's
static reference data, not application logic.
"""

SAMPLE_TEXT = """
საქართველო არის ქვეყანა კავკასიაში.
თბილისი არის საქართველოს დედაქალაქი.
ქართული ენა უნიკალურია.
"""

GEORGIAN_ALPHABET = frozenset("აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ")

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
    "warning": "გაფრთხილება",
    "context_disable_georgian": "ქართულის გამორთვა",
    "context_enable_georgian": "ქართულის ჩართვა",
    "could_not_load_file": "ფაილის ჩატვირთვა ვერ მოხერხდა:\n{err}",
    "install_required_package": "დააინსტალირეთ საჭირო პაკეტი.",
    "file_read_error_txt": "ტექსტური ფაილის წაკითხვა ვერ მოხერხდა: {err}",
    "file_read_error_pdf": "PDF ფაილის წაკითხვა ვერ მოხერხდა: {err}",
    "file_read_error_docx": "DOCX ფაილის წაკითხვა ვერ მოხერხდა: {err}",
    "pdf_required": "PDF ფაილების გასახსნელად საჭიროა PyPDF2 პაკეტი.",
    "docx_required": "DOCX ფაილების გასახსნელად საჭიროა python-docx პაკეტი.",
    "unsupported_format": "მხარდაუჭერელი ფაილის ფორმატი: {ext}",
    "playback_error": "დაკვრის შეცდომა ფაილისთვის {file}",
}